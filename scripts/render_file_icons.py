"""Build pure vector file icons, then rasterize each registered SVG at all sizes.

Requires Pillow, fontTools and wxPython; --font can select a font file on another OS.
"""

import argparse
import json
import tempfile
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT if (PROJECT_ROOT / 'manifest.json').is_file() else PROJECT_ROOT / 'icons'
SPACING = 1
FONT_SIZE = 8.5
GAP_PADDING = 2
TEXT_COLOUR = '#3B3B3B'
TEMPLATES = Path(__file__).resolve().parent / 'icon_templates'
MASTER_SCALE = 16
PLUS_ARM_LENGTH = 5.0
PLUS_STROKE = 1.35
SHORT_LABELS = {'MPEG-1': 'MPG1', 'MPEG1': 'MPG1',
                'MPEG-2': 'MPG2', 'MPEG2': 'MPG2',
                'MPEG-4': 'MPG4', 'MPEG4': 'MPG4', 'SQLITE': 'SQL'}
SVG_NS = 'http://www.w3.org/2000/svg'
ElementTree.register_namespace('', SVG_NS)
_WX_APP = None


def svg_root():
    return ElementTree.Element(f'{{{SVG_NS}}}svg',
                               dict(width='384', height='384', viewBox='0 0 24 24'))


def rasterize_svg(svg, size):
    """Rasterize vector geometry directly at the requested output size."""
    import wx
    import wx.svg

    global _WX_APP
    if wx.GetApp() is None:
        _WX_APP = wx.App(False)
    vector = wx.svg.SVGimage.CreateFromBytes(ElementTree.tostring(svg))
    image = vector.ConvertToBitmap(scale=size / vector.width,
                                   width=size, height=size).ConvertToImage()
    if not image.IsOk() or not image.HasAlpha():
        raise ValueError(f'Cannot render file icon vector layer at {size}px')
    result = Image.frombytes('RGB', (size, size), bytes(image.GetData())).convert('RGBA')
    result.putalpha(Image.frombytes('L', (size, size), bytes(image.GetAlpha())))
    return result


@lru_cache(maxsize=8)
def outline_font(font_path, font_axes):
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    font = TTFont(font_path)
    if font_axes is not None:
        axes = font['fvar'].axes
        if len(axes) != len(font_axes):
            raise ValueError('Font variation axes do not match the selected font')
        font = instantiateVariableFont(font, dict(zip(
            (axis.axisTag for axis in axes), font_axes)), inplace=False)
    return font.getGlyphSet(), font.getBestCmap(), font['head'].unitsPerEm


@lru_cache(maxsize=1024)
def glyph_outline(font_path, font_axes, character):
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.svgPathPen import SVGPathPen

    glyphs, cmap, units = outline_font(font_path, font_axes)
    selected = glyphs[cmap[ord(character)]]
    path = SVGPathPen(glyphs)
    bounds = BoundsPen(glyphs)
    selected.draw(path)
    selected.draw(bounds)
    return path.getCommands(), bounds.bounds, units


def build_vector_label(label, masks, font_path, font_axes, font_size,
                        cap_height, baseline, width_units, gaps_units, text_colour):
    """Keep bitmap-measured layout, but draw the actual font outlines as vectors."""
    svg = svg_root()
    group = ElementTree.SubElement(svg, f'{{{SVG_NS}}}g', {'fill': text_colour})
    cursor = (24 * MASTER_SCALE - width_units) // 2
    axes = tuple(font_axes) if font_axes is not None else None
    for index, (character, mask) in enumerate(zip(label, masks)):
        top = (round(baseline * MASTER_SCALE) - cap_height
               + (cap_height - mask.height) // 2) / MASTER_SCALE
        if label == '+':
            stroke = PLUS_STROKE * MASTER_SCALE
            extent = (PLUS_ARM_LENGTH + PLUS_STROKE) * MASTER_SCALE
            x = (extent - stroke) / 2
            y = (extent - stroke) / 2
            for left, upper, width, height in (
                    (x, 0, stroke, extent), (0, y, extent, stroke)):
                ElementTree.SubElement(group, f'{{{SVG_NS}}}rect', {
                    'x': str((cursor + left) / MASTER_SCALE),
                    'y': str(top + upper / MASTER_SCALE),
                    'width': str(width / MASTER_SCALE),
                    'height': str(height / MASTER_SCALE),
                    'rx': str(stroke / (2 * MASTER_SCALE)),
                })
        else:
            path, (xmin, ymin, xmax, ymax), units = glyph_outline(
                str(Path(font_path).resolve()), axes, character)
            scale = font_size / units
            tx = cursor / MASTER_SCALE - xmin * scale
            ty = top + ymax * scale
            ElementTree.SubElement(group, f'{{{SVG_NS}}}path', {
                'd': path,
                'transform': f'translate({tx:.9f} {ty:.9f}) scale({scale:.9f} {-scale:.9f})',
            })
        cursor += mask.width + (gaps_units[index] if index < len(gaps_units) else 0)
    group.set('data-role', 'label')
    return group


def save_png(image, path):
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.png', delete=False) as output:
        temporary = Path(output.name)
        image.save(output, format='PNG')
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def glyph(character, font):
    mask = Image.new('L', (font.size * 2, font.size * 2))
    draw = ImageDraw.Draw(mask)
    draw.text((0, 0), character, font=font, fill=255)
    return mask.crop(mask.getbbox())


def character_gap_units(label, base_gap_units, pair_spacing):
    """Apply shared optical spacing to listed pairs without changing other gaps."""
    return [min(base_gap_units, round(pair_spacing[pair] * MASTER_SCALE))
            if (pair := label[index:index + 2]) in pair_spacing else base_gap_units
            for index in range(max(0, len(label) - 1))]


def vector_frame(frame_template, band=None):
    """Cut the existing outline at horizontal label gaps without bitmap masks.

    The standard document's straight sides cross the gap; its rounded corners
    and fold remain outside it. Flat cut ends match the previous PNG erasure.
    """
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.svgLib.path import parse_path

    template = Path(frame_template) if frame_template else ROOT / 'source/svgs/tools/file-file.svg'
    if template.resolve() == (TEMPLATES / 'file-square.png').resolve():
        template = ROOT / 'source/svgs/tools/file-file.svg'
    if template.suffix.lower() != '.svg':
        raise ValueError('File icon frames must be SVG; embedded raster templates are not supported')
    base = ElementTree.parse(template).getroot()
    if base.get('viewBox') != '0 0 24 24':
        raise ValueError('File frame must use viewBox="0 0 24 24"')
    if any(node.tag.rsplit('}', 1)[-1] in ('image', 'foreignObject', 'text') for node in base.iter()):
        raise ValueError('File frame must contain pure vector geometry')
    group = ElementTree.Element(f'{{{SVG_NS}}}g', {'data-role': 'frame'})
    group.extend(deepcopy(list(base)))
    if band is None:
        return group
    top, bottom = band
    # Only the document outline intersects the horizontal band. Preserve the
    # separate fold subpath, including its round endpoints.
    document = group.find(f'.//{{{SVG_NS}}}path[@id="document"]')
    if document is None:
        raise ValueError('A frame with label gaps needs a document path with id="document"')
    pen = RecordingPen()
    parse_path(document.attrib['d'], pen)
    output = RecordingPen()
    current = start = last = None

    def emit_line(a, b):
        nonlocal last
        if last != a:
            output.moveTo(a)
        output.lineTo(b)
        last = b

    def line(a, b):
        nonlocal last
        if a == b:
            return
        cuts = [0., 1.]
        if a[1] != b[1]:
            cuts += [(edge-a[1])/(b[1]-a[1]) for edge in band
                     if 0 < (edge-a[1])/(b[1]-a[1]) < 1]
        cuts.sort()
        for t0, t1 in zip(cuts, cuts[1:]):
            mid_y = a[1]+(b[1]-a[1])*(t0+t1)/2
            if top < mid_y < bottom:
                last = None
                continue
            def point(t):
                return a if t == 0 else b if t == 1 else tuple(a[i]+(b[i]-a[i])*t for i in (0, 1))
            emit_line(point(t0), point(t1))

    # Open contours (the fold) have no cut ends. Keep their original caps.
    contours, contour = [], []
    for command, values in pen.value:
        if command == 'moveTo' and contour:
            contours.append(contour)
            contour = []
        contour.append((command, values))
    if contour:
        contours.append(contour)
    fold = SVGPathPen(None)
    for contour in contours:
        if not any(command == 'closePath' for command, _ in contour):
            for command, values in contour:
                getattr(fold, command)(*values)
            continue
        for command, values in contour:
            if command == 'moveTo':
                current = start = values[0]
                last = None
            elif command in ('lineTo', 'closePath'):
                target = values[0] if command == 'lineTo' else start
                line(current, target)
                current = target
            elif command in ('qCurveTo', 'curveTo'):
                ys = [current[1]]+[p[1] for p in values]
                if max(ys) > top and min(ys) < bottom:
                    raise ValueError('Label gap intersects a curved frame corner')
                if last != current:
                    output.moveTo(current)
                getattr(output, command)(*values)
                current = last = values[-1]
            elif command != 'endPath':
                raise ValueError(f'Unsupported frame command: {command}')
    # Clipping a closed contour can leave its original start as two touching
    # open subpaths. Join those runs across the start so the renderer strokes
    # the corner continuously instead of antialiasing two flat caps there.
    runs, run = [], []
    for command, values in output.value:
        if command == 'moveTo' and run:
            runs.append(run)
            run = []
        run.append((command, values))
    if run:
        runs.append(run)
    if len(runs) > 1 and runs[-1][-1][1][-1] == runs[0][0][1][0]:
        runs = [runs[-1]+runs[0][1:], *runs[1:-1]]
    joined = SVGPathPen(None)
    for run in runs:
        for command, values in run:
            getattr(joined, command)(*values)
    document.set('d', joined.getCommands())
    document.set('stroke-linecap', 'butt')
    if fold.getCommands():
        parent = next(node for node in group.iter() if document in list(node))
        ElementTree.SubElement(parent, f'{{{SVG_NS}}}path', {
            'data-role': 'fold', 'd': fold.getCommands()})
    return group


def build_file_svg(label, colour, font_path, text_colour=TEXT_COLOUR, frame_template=None,
           text_offset_y=1.5, font_axes=None, spacing=SPACING, font_size=FONT_SIZE,
           circle_bounds=(4.5, 6.0, 19.5, 21.0), pair_spacing=None):
    text_center = (circle_bounds[0] + circle_bounds[2]) / 2
    requested_spacing = spacing
    # 画布两侧各留 1 DIP；先缩字距，再按整行缩字号，绝不横向拉伸字符。
    available = 22 * MASTER_SCALE
    while True:
        font = ImageFont.truetype(str(font_path), round(font_size * MASTER_SCALE))
        if font_axes is not None:
            font.set_variation_by_axes(font_axes)
        cap_height = glyph('M', font).height
        masks = [glyph(c, font) for c in label]
        if label == '+':
            mask = masks[0]
            # Match file-folder-plus: 5px centerline arms and 1.35px rounded strokes.
            extent = round((PLUS_ARM_LENGTH + PLUS_STROKE) * MASTER_SCALE)
            mask = Image.new('L', (extent, extent))
            stroke = round(PLUS_STROKE * MASTER_SCALE)
            x = (extent - stroke) // 2
            y = (extent - stroke) // 2
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((x, 0, x + stroke - 1, extent - 1),
                                        radius=stroke / 2, fill=255)
            mask_draw.rounded_rectangle((0, y, extent - 1, y + stroke - 1),
                                        radius=stroke / 2, fill=255)
            masks = [mask]
        spacing_units = round(requested_spacing * MASTER_SCALE)
        if len(masks) > 1:
            fit_spacing = (available - sum(mask.width for mask in masks)) // (len(masks) - 1)
            spacing_units = min(spacing_units, max(round(0.25 * MASTER_SCALE), fit_spacing))
        gaps_units = character_gap_units(label, spacing_units, pair_spacing or {})
        width_units = sum(mask.width for mask in masks) + sum(gaps_units)
        if width_units <= available:
            break
        font_size -= 0.25
        if font_size < 5:
            raise ValueError(f'Label too long; provide an abbreviation: {label}')
    spacing = spacing_units / MASTER_SCALE
    width = width_units / MASTER_SCALE
    left = text_center - width / 2
    right = left + width
    gaps = left <= 5.5 or right >= 18.5
    baseline = 16 + text_offset_y
    band_top = baseline - cap_height / MASTER_SCALE - GAP_PADDING
    band_bottom = baseline + GAP_PADDING if gaps else baseline + 1

    svg = svg_root()
    if colour is not None:
        ElementTree.SubElement(svg, f'{{{SVG_NS}}}circle', {
            'data-role': 'format-circle',
            'cx': str((circle_bounds[0] + circle_bounds[2]) / 2),
            'cy': str((circle_bounds[1] + circle_bounds[3]) / 2),
            'r': str((circle_bounds[2] - circle_bounds[0]) / 2),
            'fill': colour,
        })
    svg.append(vector_frame(frame_template, (band_top, band_bottom) if gaps else None))
    svg.append(build_vector_label(label, masks, font_path, font_axes, font_size,
                                  cap_height, baseline, width_units, gaps_units, text_colour))
    return svg, dict(label_left=left, label_right=right,
                        frame_gaps=gaps, character_gap=spacing,
                        condensed=False, label_center=text_center,
                        font_size=font_size, cap_height=cap_height / MASTER_SCALE,
                        baseline=baseline, text_offset_y=text_offset_y, display_label=label,
                        font_family=font.getname()[0], font_style=font.getname()[1],
                        font_axes=font_axes,
                        native_pixel_text=False, rendering='pure-vector-svg',
                        pixel_aligned_label=False,
                        text_colour=text_colour,
                        canvas_padding=0,
                        frame_gap_padding=GAP_PADDING if gaps else 0,
                        pair_spacing={label[index:index + 2]: gap / MASTER_SCALE
                                      for index, gap in enumerate(gaps_units)
                                      if index < len(label) - 1 and gap < spacing_units})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path, default=Path('C:/Windows/Fonts/seguisb.ttf'))
    parser.add_argument('--font-axes', type=float, nargs='+', help='Variable-font axes in font order (Bahnschrift: weight width)')
    parser.add_argument('--text-colour', help='Override label colour for the selected icons')
    parser.add_argument('--frame-template', type=Path, help='Use a pure vector SVG frame for selected icons')
    parser.add_argument('--render-only', action='store_true', help='Render registered SVGs without rebuilding them or requiring a font')
    parser.add_argument('--text-offset-y', type=float, help='Vertical label offset in 24px design units')
    parser.add_argument('--spacing', type=float, help='Visible character gap in 24px design units')
    parser.add_argument('--font-size', type=float, help='Font size in 24px design units')
    parser.add_argument('--circle-offset-y', type=float, help='Circle vertical offset in 24px design units')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--names', nargs='+', help='Only regenerate the named file icons')
    selection.add_argument('--all', action='store_true', help='Explicitly regenerate all file icons')
    args = parser.parse_args()
    if not args.render_only and not args.font.is_file():
        parser.error('Font file missing; supply --font PATH')
    if not args.all and not args.names:
        args.names = ['hls', 'm3u8', 'ts', 'mp4', 'url']
    manifest_path = ROOT / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    defaults = manifest['file_frame']['style_defaults']
    circle = manifest['file_frame']['circle']
    if (args.all or args.names and 'new' in args.names) and not any(
            entry['category'] == 'files' and entry['name'] == 'new' for entry in manifest['icons']):
        manifest['icons'].append(dict(category='files', name='new', label='+',
                                     origin='new-file', added=True, group='other', source='source/files/other-new.png',
                                     circle_color=None))
    entries = [i for i in manifest['icons'] if i['category'] == 'files']
    if args.names:
        unknown = set(args.names) - {i['name'] for i in entries}
        if unknown:
            parser.error(f'Unknown file icons: {sorted(unknown)}')
        entries = [i for i in entries if i['name'] in args.names]
    if args.all and not args.render_only and args.frame_template is None:
        defaults['frame_template'] = 'source/svgs/tools/file-file.svg'
    for entry in entries:
        name = entry['name']
        vector_path = ROOT / 'source/svgs/files' / (Path(entry['source']).stem+'.svg')
        if args.render_only:
            if entry.get('vector_source') != vector_path.relative_to(ROOT).as_posix() or not vector_path.is_file():
                parser.error(f'File icon without a registered SVG: {name}')
            vector = ElementTree.parse(vector_path).getroot()
            for directory in ('source', *(str(s) for s in manifest['sizes'])):
                size = 384 if directory == 'source' else int(directory)
                save_png(rasterize_svg(vector, size), ROOT / directory / 'files' / Path(entry['source']).name)
            print(f'Rendered {name} from SVG')
            continue
        entry['display_label'] = SHORT_LABELS.get(entry['label'], entry['label'])
        overrides = {
            'frame_template': (args.frame_template.resolve().relative_to(PROJECT_ROOT).as_posix()
                               if args.frame_template else None),
            'text_offset_y': args.text_offset_y,
            'character_gap': args.spacing,
            'font_size': args.font_size,
            'circle_offset_y': args.circle_offset_y,
            'text_colour': args.text_colour,
        }
        for key, value in overrides.items():
            if value is None:
                continue
            if args.all:
                defaults[key] = value
            else:
                entry[key] = value
        character_gap = (args.spacing if args.spacing is not None else entry.get(
            'character_gap',
            defaults.get('character_gap_by_length', {}).get(
                str(len(entry['display_label'])), defaults['character_gap'])))
        frame_template_path = entry.get('frame_template', defaults['frame_template'])
        frame_template = PROJECT_ROOT / frame_template_path if frame_template_path else None
        circle_offset_y = entry.get('circle_offset_y', defaults['circle_offset_y'])
        circle_bounds = (circle['x'], circle['y'] + circle_offset_y,
                         circle['x'] + circle['diameter'],
                         circle['y'] + circle_offset_y + circle['diameter'])
        if name == 'new':
            vector = ElementTree.parse(ROOT / 'source/svgs/tools/file-new.svg').getroot()
        else:
            vector, metrics = build_file_svg(entry['display_label'], entry['circle_color'], args.font,
                                            entry.get('text_colour', defaults['text_colour']), frame_template,
                                            entry.get('text_offset_y', defaults['text_offset_y']), args.font_axes,
                                            character_gap, entry.get('font_size', defaults['font_size']),
                                            circle_bounds, defaults.get('pair_spacing', {}))
        ElementTree.indent(vector, space='  ')
        vector_path.write_text(ElementTree.tostring(vector, encoding='unicode')+'\n', encoding='utf-8')
        entry['vector_source'] = vector_path.relative_to(ROOT).as_posix()
        for directory in ('source', *(str(s) for s in manifest['sizes'])):
            path = ROOT / directory / 'files' / Path(entry['source']).name
            path.parent.mkdir(parents=True, exist_ok=True)
            size = 384 if directory == 'source' else int(directory)
            result = rasterize_svg(vector, size)
            save_png(result, path)
            if name == 'new':
                tool_entry = next((i for i in manifest['icons']
                                   if i['category'] == 'tools' and i['name'] == 'new'), None)
                tool_path = ROOT / directory / 'tools' / (
                    Path(tool_entry['source']).name if tool_entry else 'file-new.png')
                tool_path.parent.mkdir(parents=True, exist_ok=True)
                save_png(result, tool_path)
        if name != 'new':
            base_metrics = metrics
            manifest['file_frame']['text_metrics'].setdefault(name, {}).update(base_metrics)
            print(name, base_metrics)
    if any(entry['name'] == 'new' for entry in entries) and not any(
            entry['category'] == 'tools' and entry['name'] == 'new' for entry in manifest['icons']):
        manifest['icons'].append(dict(category='tools', name='new', label='新建文件',
                                     origin='synced:files/other-new.png', added=True, group='file',
                                     source='source/tools/file-new.png'))
    if args.render_only:
        return
    if not args.names:
        manifest['file_frame']['label_rule'] = (
            f'{base_metrics["font_family"]} {base_metrics["font_style"]}, '
            '8.5px font, default 1px character gaps at 24px, reduce gaps only to fit. '
            'Labels and circles share center x=12; baseline y=17.5. '
            'Long file types use short display labels. Fixed square canvas; '
            'no individual letter is compressed. Special new reuses file-new.svg. '
            'Frame gaps add 2px padding. Complete pure vector SVGs drive all PNG sizes.'
        )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
