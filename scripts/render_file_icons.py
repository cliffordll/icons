"""Regenerate file icons with centered circles and separated characters.

Requires Pillow, fontTools and wxPython; --font can select a font file on another OS.
"""

import argparse
import json
import tempfile
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


def render_vector_label(size, label, masks, font_path, font_axes, font_size,
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
            # Preserve the approved optical width and rounded caps of the new-file symbol.
            stroke = round(19 / 16 * MASTER_SCALE)
            x = (mask.width - stroke) // 2
            y = (mask.height - stroke) // 2
            for left, upper, width, height in (
                    (x, 0, stroke, mask.height), (0, y, mask.width, stroke)):
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
    return rasterize_svg(svg, size)


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


def render_frame(size):
    """文件与新建图标共用 1.35px 粗线、圆角和折角，按目标尺寸绘制。"""
    unit = max(MASTER_SCALE, size / 24 * 4)
    frame = Image.new('RGBA', (round(24 * unit), round(24 * unit)))
    draw = ImageDraw.Draw(frame)

    def coords(values):
        return tuple(round(value * unit) for value in values)

    draw.rounded_rectangle(coords((4.075, 2.125, 19.925, 21.875)),
                           radius=round(1.1 * unit), fill='#444444')
    draw.rounded_rectangle(coords((5.425, 3.475, 18.575, 20.525)),
                           radius=round(0.35 * unit), fill=(0, 0, 0, 0))
    draw.polygon([coords(p) for p in ((14.55, 2.125), (24, 2.125), (24, 7.5), (19.925, 7.5))],
                 fill=(0, 0, 0, 0))
    draw.line([coords(p) for p in ((14.1, 2.6), (19.45, 7.95))],
              fill='#444444', width=round(1.35 * unit))
    draw.line([coords(p) for p in ((13.675, 2.8), (13.675, 7.675), (19.25, 7.675))],
              fill='#444444', width=round(1.35 * unit), joint='curve')
    return frame.resize((size, size), Image.Resampling.LANCZOS)


def render(original, label, colour, font_path, text_colour=TEXT_COLOUR, frame_template=None,
           text_offset_y=1.5, font_axes=None, spacing=SPACING, font_size=FONT_SIZE,
           circle_bounds=(4.5, 6.0, 19.5, 21.0), pair_spacing=None):
    size = original.height
    scale = size / 24
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
            # 加号交叉处视觉偏重，线宽用 19/16px；保留外接尺寸和中心位置。
            width = round(mask.width * cap_height / mask.height)
            mask = Image.new('L', (width, cap_height))
            stroke = round(19 / 16 * MASTER_SCALE)
            x = (width - stroke) // 2
            y = (cap_height - stroke) // 2
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((x, 0, x + stroke - 1, cap_height - 1),
                                        radius=stroke / 2, fill=255)
            mask_draw.rounded_rectangle((0, y, width - 1, y + stroke - 1),
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

    background = Image.new('RGBA', (size, size))
    if colour is not None:
        svg = svg_root()
        ElementTree.SubElement(svg, f'{{{SVG_NS}}}circle', {
            'cx': str((circle_bounds[0] + circle_bounds[2]) / 2),
            'cy': str((circle_bounds[1] + circle_bounds[3]) / 2),
            'r': str((circle_bounds[2] - circle_bounds[0]) / 2),
            'fill': colour,
        })
        background = rasterize_svg(svg, size)
    if frame_template is None or Path(frame_template).resolve() == (TEMPLATES / 'file-square.png').resolve():
        frame = render_frame(size)
    else:
        with Image.open(frame_template) as template:
            frame = template.convert('RGBA').resize((size, size), Image.Resampling.LANCZOS)
    if gaps:
        band = (0, round(band_top * scale), size, round(band_bottom * scale))
        frame.paste((0, 0, 0, 0), band)
    body = Image.alpha_composite(background, frame)
    text = render_vector_label(size, label, masks, font_path, font_axes, font_size,
                               cap_height, baseline, width_units, gaps_units, text_colour)
    result = Image.alpha_composite(body, text)
    return result, dict(label_left=left, label_right=right,
                        frame_gaps=gaps, character_gap=spacing,
                        condensed=False, label_center=text_center,
                        font_size=font_size, cap_height=cap_height / MASTER_SCALE,
                        baseline=baseline, text_offset_y=text_offset_y, display_label=label,
                        font_family=font.getname()[0], font_style=font.getname()[1],
                        font_axes=font_axes,
                        native_pixel_text=False, rendering='vector-label-and-circle',
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
    parser.add_argument('--frame-template', type=Path, help='Use a transparent frame PNG for selected icons')
    parser.add_argument('--text-offset-y', type=float, help='Vertical label offset in 24px design units')
    parser.add_argument('--spacing', type=float, help='Visible character gap in 24px design units')
    parser.add_argument('--font-size', type=float, help='Font size in 24px design units')
    parser.add_argument('--circle-offset-y', type=float, help='Circle vertical offset in 24px design units')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--names', nargs='+', help='Only regenerate the named file icons')
    selection.add_argument('--all', action='store_true', help='Explicitly regenerate all file icons')
    args = parser.parse_args()
    if not args.font.is_file():
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
    for entry in entries:
        name = entry['name']
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
        for directory in ('source', *(str(s) for s in manifest['sizes'])):
            path = ROOT / directory / 'files' / Path(entry['source']).name
            path.parent.mkdir(parents=True, exist_ok=True)
            with Image.new('RGBA', (384, 384) if directory == 'source' else (int(directory), int(directory))) as original:
                result, metrics = render(original, entry['display_label'],
                                         entry['circle_color'], args.font,
                                         entry.get('text_colour', defaults['text_colour']), frame_template,
                                         entry.get('text_offset_y', defaults['text_offset_y']), args.font_axes,
                                         character_gap,
                                         entry.get('font_size', defaults['font_size']), circle_bounds,
                                         defaults.get('pair_spacing', {}))
            save_png(result, path)
            if name == 'new':
                tool_entry = next((i for i in manifest['icons']
                                   if i['category'] == 'tools' and i['name'] == 'new'), None)
                tool_path = ROOT / directory / 'tools' / (
                    Path(tool_entry['source']).name if tool_entry else 'file-new.png')
                tool_path.parent.mkdir(parents=True, exist_ok=True)
                save_png(result, tool_path)
            if directory == '24':
                base_metrics = metrics
        manifest['file_frame']['text_metrics'].setdefault(name, {}).update(base_metrics)
        print(name, base_metrics)
    if any(entry['name'] == 'new' for entry in entries) and not any(
            entry['category'] == 'tools' and entry['name'] == 'new' for entry in manifest['icons']):
        manifest['icons'].append(dict(category='tools', name='new', label='新建文件',
                                     origin='synced:files/other-new.png', added=True, group='file',
                                     source='source/tools/file-new.png'))
    if not args.names:
        manifest['file_frame']['label_rule'] = (
            f'{base_metrics["font_family"]} {base_metrics["font_style"]}, '
            '8.5px font, default 1px character gaps at 24px, reduce gaps only to fit. '
            'Labels and circles share center x=12; baseline y=17.5. '
            'Long file types use short display labels. Fixed square canvas; '
            'no individual letter is compressed. Plus sign matches cap height. '
            'Frame gaps add 2px padding.'
        )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
