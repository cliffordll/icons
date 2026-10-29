"""Build floating corner badges from shared glyphs and measured outline gaps.

Run this before render_tool_icons.py after changing a badge or its background.
Geometry is in 24px units; no opaque masks or scaled strokes are used.
"""

import argparse
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from fontTools.misc.bezierTools import splitCubicAtT, splitQuadraticAtT
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.svgLib.path import SVGPath, parse_path

ROOT = Path(__file__).resolve().parents[1]
STROKE = 1.35
GAP = 0.6
BADGE_SIZE = 10.5
BADGE_OFFSET_Y = -0.75


def paths(stem):
    return [e.attrib['d'] for e in ET.parse(ROOT / 'source/svgs' / (stem + '.svg')).iter()
            if e.tag.endswith('}path')]


def full_geometry(stem):
    """Reuse all source primitives and transforms, including circles and ellipses."""
    pen = SVGPathPen(None)
    SVGPath(str(ROOT / 'source/svgs' / (stem+'.svg'))).draw(pen)
    return pen.getCommands()


def folder_geometry():
    """Apply the folder's nested SVG transforms before clipping its outline."""
    output = SVGPathPen(None)

    def visit(element, parent):
        local = Transform()
        for operation, values in re.findall(r'(translate|scale|matrix)\(([^)]+)\)', element.get('transform', '')):
            args = [float(v) for v in re.split(r'[ ,]+', values.strip())]
            if operation == 'translate':
                local = local.translate(args[0], args[1] if len(args) > 1 else 0)
            elif operation == 'scale':
                local = local.scale(args[0], args[1] if len(args) > 1 else args[0])
            else:
                local = local.transform(Transform(*args))
        combined = parent.transform(local)
        if element.tag.endswith('}path'):
            parse_path(element.attrib['d'], TransformPen(output, combined))
        for child in element:
            visit(child, combined)

    visit(ET.parse(ROOT / 'source/svgs/file-folder.svg').getroot(), Transform())
    return output.getCommands()


def transform(d, dx=0, dy=0):
    pen = SVGPathPen(None)
    parse_path(d, TransformPen(pen, (1, 0, 0, 1, dx, dy)))
    return pen.getCommands()


def resize_path(d, sx, sy, cx, cy, target_x=None, target_y=None):
    """Resize geometry only, leaving the renderer's effective stroke unchanged."""
    target_x = cx if target_x is None else target_x
    target_y = cy if target_y is None else target_y
    pen = SVGPathPen(None)
    parse_path(d, TransformPen(pen, (sx, 0, 0, sy, target_x-sx*cx, target_y-sy*cy)))
    return pen.getCommands()


def circle(x, y, r):
    return f'M{x-r} {y}a{r} {r} 0 1 0 {2*r} 0a{r} {r} 0 1 0 {-2*r} 0Z'


def rectangle(x, y, w, h, r=0.6):
    return (f'M{x+r} {y}h{w-2*r}q{r} 0 {r} {r}v{h-2*r}'
            f'q0 {r} {-r} {r}h{-w+2*r}q{-r} 0 {-r} {-r}v{-h+2*r}'
            f'q0 {-r} {r} {-r}Z')


def segments(d):
    pen = RecordingPen()
    parse_path(d, pen)
    result = []
    current = start = None
    for command, points in pen.value:
        if command == 'moveTo':
            current = start = points[0]
        elif command in ('lineTo', 'curveTo', 'qCurveTo'):
            result.append((current, *points))
            current = points[-1]
        elif command == 'closePath' and current != start:
            result.append((current, start))
            current = start
    return result


def point(segment, t):
    points = list(segment)
    while len(points) > 1:
        points = [((1-t)*a[0]+t*b[0], (1-t)*a[1]+t*b[1])
                  for a, b in zip(points, points[1:])]
    return points[0]


def point_line_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = dx*dx + dy*dy
    t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length)) if length else 0
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def edges(d):
    result = []
    for segment in segments(d):
        # Dense enough that curved-glyph clearance error is below 0.003px.
        count = 1 if len(segment) == 2 else 32
        points = [point(segment, j/count) for j in range(count+1)]
        result.extend(zip(points, points[1:]))
    return result


def inside(p, polygon):
    yes = False
    x, y = p
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        if ((a[1] > y) != (b[1] > y)
                and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]):
            yes = not yes
    return yes


GEAR = ET.parse(ROOT / 'scripts/icon_templates/gear-badge.svg').getroot()[0].attrib['d']
_magnifier = ET.parse(ROOT / 'scripts/icon_templates/magnifier.svg').getroot()
_lens = _magnifier.find('.//{http://www.w3.org/2000/svg}circle')
_handle = _magnifier.find('.//{http://www.w3.org/2000/svg}path').attrib['d']
_magnifier_bounds = BoundsPen(None)
SVGPath.fromstring(ET.tostring(_magnifier)).draw(_magnifier_bounds)
_mx0, _my0, _mx1, _my1 = _magnifier_bounds.bounds
_mcx, _mcy = (_mx0+_mx1)/2, (_my0+_my1)/2
SEARCH_SCALE = (BADGE_SIZE-STROKE)/max(_mx1-_mx0, _my1-_my0)
SEARCH_X = 17.5+(float(_lens.attrib['cx'])-_mcx)*SEARCH_SCALE
SEARCH_Y = 17.5+(float(_lens.attrib['cy'])-_mcy)*SEARCH_SCALE
SEARCH_RADIUS = float(_lens.attrib['r'])*SEARCH_SCALE
SEARCH = [circle(SEARCH_X, SEARCH_Y, SEARCH_RADIUS),
          resize_path(_handle, SEARCH_SCALE, SEARCH_SCALE, _mcx, _mcy, 17.5, 17.5)]
GLYPH_SCALE = (BADGE_SIZE-STROKE)/(9-STROKE)
CODE = [resize_path('M16.525 14.125 13.675 17.5l2.85 3.375M18.475 14.125l2.85 3.375-2.85 3.375',
                    GLYPH_SCALE, GLYPH_SCALE, 17.5, 17.5)]
CODE_SILHOUETTE = [resize_path('M13.675 17.5 16.525 14.125 18.475 14.125'
                               ' 21.325 17.5 18.475 20.875 16.525 20.875Z',
                               GLYPH_SCALE, GLYPH_SCALE, 17.5, 17.5)]
DOWNLOAD_SCALE = GLYPH_SCALE * 0.9
DOWNLOAD = [resize_path('M17.5 13.675v7.65m-3.825-3.825 3.825 3.825 3.825-3.825',
                        3.816/3.825, DOWNLOAD_SCALE, 17.5, 17.5)]
PERCENT_RADIUS = 1.2*BADGE_SIZE/10
PERCENT_X = (BADGE_SIZE-STROKE-2*PERCENT_RADIUS)/2
PERCENT_CIRCLES = [(17.5+sx*PERCENT_X, 17.5+sy*2*GLYPH_SCALE, PERCENT_RADIUS)
                   for sx, sy in [(-1, -1), (1, 1)]]
PERCENT_HEIGHT = (BADGE_SIZE-STROKE)*0.9
PERCENT = [f'M{17.5-2.5*GLYPH_SCALE} {17.5+PERCENT_HEIGHT/2}'
           f'L{17.5+2.5*GLYPH_SCALE} {17.5-PERCENT_HEIGHT/2}',
           *(circle(x, y, r) for x, y, r in PERCENT_CIRCLES)]
BOLT = [resize_path('M18.1 13.5l-3.6 4.8H17.3l-.4 3.2 3.6-4.8h-2.8Z',
                    (BADGE_SIZE-STROKE)/6, (BADGE_SIZE-STROKE)/8, 17.5, 17.5)]
PAPER = [rectangle(17.5-6.75*GLYPH_SCALE/2, 17.5-(BADGE_SIZE-STROKE)/2,
                   6.75*GLYPH_SCALE, BADGE_SIZE-STROKE)]

# Size the confirmed filled gear without redrawing any of its contours.
# Reductions compensate edge thickness; enlargements preserve the full shape.
_gear_bounds = BoundsPen(None)
parse_path(GEAR, _gear_bounds)
_gx0, _gy0, _gx1, _gy1 = _gear_bounds.bounds
_gear_width = max(_gx1-_gx0, _gy1-_gy0)
if BADGE_SIZE <= _gear_width:
    GEAR_SCALE = (BADGE_SIZE-STROKE)/(_gear_width-STROKE)
    GEAR_EDGE = STROKE*(1-GEAR_SCALE)
else:
    # Enlargement keeps the complete confirmed filled shape in proportion.
    GEAR_SCALE = BADGE_SIZE/_gear_width
    GEAR_EDGE = 0
GEAR = resize_path(GEAR, GEAR_SCALE, GEAR_SCALE,
                   (_gx0+_gx1)/2, (_gy0+_gy1)/2, 17.5, 17.5)


class Badge:
    def __init__(self, profile, glyphs, filled=False, circles=(), solids=(), edge=0):
        self.profile = profile
        self.glyphs = [transform(d, dy=BADGE_OFFSET_Y) for d in glyphs]
        self.filled = filled
        self.edge = edge
        self.half_width = edge/2 if filled else STROKE/2
        self.circles = [(x, y+BADGE_OFFSET_Y, r) for x, y, r in circles]
        self.lines = [edge for d in self.glyphs for edge in edges(d)]
        self.solids = [[a for a, _ in edges(transform(d, dy=BADGE_OFFSET_Y))] for d in solids]

    def distance(self, p):
        if any(inside(p, polygon) for polygon in self.solids):
            return -1
        distances = [point_line_distance(p, a, b) for a, b in self.lines]
        distances.extend(math.hypot(p[0]-x, p[1]-y)-r for x, y, r in self.circles)
        return min(distances)

    def visible(self, p):
        return self.distance(p) >= GAP + STROKE/2 + self.half_width


def glyph(profile, dx=0, dy=0):
    if profile == 'search':
        return Badge(profile, SEARCH, circles=[(SEARCH_X, SEARCH_Y, SEARCH_RADIUS)])
    if profile == 'code':
        return Badge(profile, CODE, solids=CODE_SILHOUETTE)
    if profile == 'download':
        return Badge(profile, DOWNLOAD)
    if profile == 'plus':
        return Badge(profile, ['M12.925 17.5h9.15M17.5 12.925v9.15'])
    if profile == 'percent':
        return Badge(profile, PERCENT, circles=PERCENT_CIRCLES)
    if profile == 'bolt':
        return Badge(profile, BOLT, solids=BOLT)
    if profile == 'paper':
        return Badge(profile, PAPER, solids=PAPER)
    if profile == 'gear':
        d = transform(GEAR, dx, dy)
        outer = d.split('Z')[0] + 'Z'
        # Gear source is a filled band, so clearance is measured from its outer edge.
        return Badge(profile, [d], filled=True, solids=[outer], edge=GEAR_EDGE)
    raise ValueError(profile)


def piece(segment, a, b):
    if len(segment) == 2:
        return (point(segment, a), point(segment, b))
    split = splitCubicAtT if len(segment) == 4 else splitQuadraticAtT
    ts = [t for t in (a, b) if 1e-9 < t < 1-1e-9]
    return split(*segment, *ts)[1 if a > 1e-9 else 0]


def clip(d, badge, prefix=False):
    output, cutpoints = [], []
    stopped = False
    for segment in segments(d):
        if stopped:
            break
        cuts = [0.0]
        previous = badge.visible(segment[0])
        for j in range(1, 257):
            t = j/256
            current = badge.visible(point(segment, t))
            if previous != current:
                lo, hi = (j-1)/256, t
                for _ in range(30):
                    mid = (lo+hi)/2
                    if badge.visible(point(segment, mid)) == previous:
                        lo = mid
                    else:
                        hi = mid
                cuts.append((lo+hi)/2)
            previous = current
        cuts.append(1.0)
        for a, b in zip(cuts, cuts[1:]):
            if b-a < 1e-8:
                continue
            if not badge.visible(point(segment, (a+b)/2)):
                if prefix:
                    stopped = True
                    break
                continue
            q = piece(segment, a, b)
            fmt = lambda p: f'{p[0]:.7f} {p[1]:.7f}'
            output.append('M'+fmt(q[0])+{2: 'L', 3: 'Q', 4: 'C'}[len(q)]
                          +' '.join(fmt(p) for p in q[1:]))
            if a > 1e-8:
                cutpoints.append(q[0])
            if b < 1-1e-8:
                cutpoints.append(q[-1])
                if prefix:
                    stopped = True
                    break
    return ''.join(output), cutpoints


def prune_short_islands(d, cuts, minimum):
    """Omit detached corner remnants, retaining measured ends of surviving paths."""
    groups = []
    for segment in segments(d):
        if not groups or math.dist(groups[-1][-1][-1], segment[0]) > 1e-5:
            groups.append([])
        groups[-1].append(segment)
    kept = [group for group in groups if sum(
        math.dist(point(s, j/16), point(s, (j+1)/16))
        for s in group for j in range(16)) >= minimum]
    ends = [p for group in kept for segment in group for p in (segment[0], segment[-1])]
    cuts = [p for p in cuts if any(math.dist(p, q) < 1e-5 for q in ends)]
    output = []
    for group in kept:
        for segment in group:
            fmt = lambda p: f'{p[0]:.7f} {p[1]:.7f}'
            output.append('M'+fmt(segment[0])+{2: 'L', 3: 'Q', 4: 'C'}[len(segment)]
                          +' '.join(fmt(p) for p in segment[1:]))
    return ''.join(output), cuts


def omit_bottom_corner_island(d, cuts, complete_outline):
    """Stop selected clipboard or document bottom edges at the badge.

    Applied only to file-review and file-search, not as a global length rule.
    Only a detached run wholly inside the bottom 0.6px corner band is removed.
    """
    bounds = BoundsPen(None)
    parse_path(complete_outline, bounds)
    bottom = bounds.bounds[3]
    groups = []
    for segment in segments(d):
        if not groups or math.dist(groups[-1][-1][-1], segment[0]) > 1e-5:
            groups.append([])
        groups[-1].append(segment)
    kept = []
    for group in groups:
        detached = all(any(math.dist(end, cut) < 1e-5 for cut in cuts)
                       for end in (group[0][0], group[-1][-1]))
        if detached and all(p[1] >= bottom-0.6-1e-5 for segment in group for p in segment):
            continue
        kept.extend(group)
    ends = [p for segment in kept for p in (segment[0], segment[-1])]
    cuts = [p for p in cuts if any(math.dist(p, end) < 1e-5 for end in ends)]
    output = []
    for segment in kept:
        fmt = lambda p: f'{p[0]:.7f} {p[1]:.7f}'
        output.append('M'+fmt(segment[0])+{2: 'L', 3: 'Q', 4: 'C'}[len(segment)]
                      +' '.join(fmt(p) for p in segment[1:]))
    return ''.join(output), cuts


def specs():
    monitor = transform(rectangle(3, 3.375, 16.95, 12.25)
                        + 'M11.5 15.625V20.25M8.5 20.25h6', dy=0.1875)
    pin_hole = ET.parse(ROOT / 'source/svgs/view-location.svg').find('.//{http://www.w3.org/2000/svg}circle')
    pin = (transform(paths('view-location')[0], dy=0.25)
           + circle(float(pin_hole.attrib['cx']), float(pin_hole.attrib['cy'])+0.25,
                    float(pin_hole.attrib['r'])))
    printer = ('M6 17.5H3.6q-.6 0-.6-.6V9.1q0-.6.6-.6h16.8q.6 0 .6.6'
               'v7.8q0 .6-.6.6H18'
               + 'M6 8.5V4.1q0-.6.6-.6h10.8q.6 0 .6.6v4.4'
               + rectangle(6, 13, 12, 7.5))
    clipboard_body = transform('M8 4.5H5.1q-.6 0-.6.6v15.3q0 .6.6.6h13.8'
                               'q.6 0 .6-.6V5.1q0-.6-.6-.6H16'
                               + rectangle(8, 2.5, 8, 4), dx=-1)
    clipboard = clipboard_body + transform('M8 10h4M8 14h2', dx=-1)
    document = (ET.parse(ROOT / 'source/svgs/file-file.svg')
                .find('.//{http://www.w3.org/2000/svg}path[@id="document"]')
                .attrib['d'])
    globe = full_geometry('net-globe')
    server = rectangle(3.675, 3.675, 16.65, 7) + rectangle(3.675, 13.325, 16.65, 7)
    result = {
        'net-cloud-search': (transform('M21 13.5c0 2.5-2 4.5-4.5 4.5h-10'
                                      'a4 4 0 0 1-.6-7.95A6.2 6.2 0 0 1 18 8.5'
                                      'c2.3.5 3.4 2.6 3 5', dy=-0.75), glyph('search'), ''),
        'net-globe-search': (globe, glyph('search'), ''),
        'lock-shield-search': (transform(paths('lock-shield')[0], -0.9375, -0.25), glyph('search'), ''),
        'file-print-preview': (transform(printer, -0.25, -0.5), glyph('search'),
                               f'<path fill="#444444" stroke="none" d="{circle(17.35,10.3,.675)}"/>'),
        'file-review': (clipboard, glyph('search'), ''),
        'file-search': (document, glyph('search'), ''),
        'file-download': (document, glyph('download'), ''),
        'edit-paste': (clipboard_body, glyph('paper'), ''),
        'view-location-search': (pin, glyph('search'), ''),
        'view-location-settings': (pin, glyph('gear'), ''),
        'play-player-setting': (monitor, glyph('gear'), ''),
        'file-folder-settings': (folder_geometry(), glyph('gear'), ''),
        'user-add': (full_geometry('user-user'), glyph('plus'), ''),
        'sys-remote': (monitor, glyph('code'), ''),
        'view-map-code': (paths('view-map')[0], glyph('code'), ''),
        'net-server-bolt': (server + 'M11 7.175h6M11 16.825h6', glyph('bolt'),
                            f'<path fill="#444444" stroke="none" d="{circle(7,7.175,.8)+circle(7,16.825,.8)}"/>'),
    }
    for name, profile in [('code', 'code'), ('download', 'download'), ('percent', 'percent')]:
        result['user-send-'+name] = ('', glyph(profile), '')
    return result


def centering_offset(background, extra):
    """Center only the complete background; the badge stays in canvas space."""
    outlines = [(background, STROKE)]
    for path in ET.fromstring('<g>'+extra+'</g>'):
        outlines.append((path.attrib['d'], 0))
    bounds = []
    for d, stroke in outlines:
        pen = BoundsPen(None)
        parse_path(d, pen)
        if pen.bounds:
            x0, y0, x1, y1 = pen.bounds
            bounds.append((x0-stroke/2, y0-stroke/2, x1+stroke/2, y1+stroke/2))
    x0 = min(b[0] for b in bounds)
    y0 = min(b[1] for b in bounds)
    x1 = max(b[2] for b in bounds)
    y1 = max(b[3] for b in bounds)
    return 12-(x0+x1)/2, 12-(y0+y1)/2


def build(names=None):
    results = {}
    selected = specs()
    if names:
        unknown = set(names)-selected.keys()
        if unknown:
            raise ValueError(f'Unknown badge icons: {sorted(unknown)}')
        selected = {name: selected[name] for name in names}
    for stem, (background, badge, extra) in selected.items():
        complete_background = full_geometry('user-send') if stem.startswith('user-send-') else background
        dx, dy = centering_offset(complete_background, extra)
        # Move the uncut subject first, then recalculate its cuts against the
        # fixed canvas-space badge. Translating a clipped composite moves the
        # badge off its anchor; moving only the old cuts changes their gaps.
        complete_background = transform(complete_background, dx, dy)
        background = transform(background, dx, dy) if background else ''
        if extra:
            detail_group = ET.fromstring('<g>'+extra+'</g>')
            for detail in detail_group:
                detail.attrib['d'] = transform(detail.attrib['d'], dx, dy)
            extra = ''.join(ET.tostring(detail, encoding='unicode') for detail in detail_group)
        if stem.startswith('user-send-'):
            # Each exposed wing stops at its first intersection with the badge's
            # clearance band. Never restore the hidden tail as detached fragments.
            left, left_points = clip(transform('M10.2 13.8l3.6 7.2', dx, dy), badge, prefix=True)
            right, right_points = clip(transform('M21 3 13.8 21', dx, dy), badge, prefix=True)
            if len(left_points) != 1 or len(right_points) != 1:
                raise ValueError(f'{stem}: both wings must meet the badge clearance band')
            background = transform('M21 3 3 10.2 10.2 13.8 21 3', dx, dy) + left + right
            cuts = left_points + right_points
        else:
            background, cuts = clip(background, badge)
            if stem == 'net-server-bolt':
                background, cuts = prune_short_islands(background, cuts, minimum=1.6)
            elif stem in ('file-review', 'file-search'):
                background, cuts = omit_bottom_corner_island(background, cuts, complete_background)
        for p in cuts:
            clearance = badge.distance(p)-STROKE/2-badge.half_width
            if abs(clearance-GAP) > 0.00001:
                raise ValueError(f'{stem}: bad cutpoint {p}, gap {clearance}')
        cut_attribute = ' '.join(f'{x:.7f},{y:.7f}' for x, y in cuts)
        foreground = ''.join('<path d="'+d+'"/>' for d in badge.glyphs)
        fill = (f' fill="#444444" stroke="#444444" stroke-width="{badge.edge:.9f}"'
                ' fill-rule="evenodd"') if badge.filled else ''
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="384" height="384" viewBox="0 0 24 24">\n'
               '  <g data-role="centered-composite" data-layout="subject-centered-fixed-badge"'
               ' fill="none" stroke="#444444" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">\n'
               f'    <g data-role="background" data-center-shift="{dx:.9f},{dy:.9f}"'
               f' data-complete-outline="{complete_background}" data-cutpoints="{cut_attribute}"><path d="{background}"/>{extra}</g>\n'
               f'    <g data-role="badge" data-profile="{badge.profile}"{fill}>{foreground}</g>\n'
               '  </g>\n</svg>\n')
        results[stem] = svg
        print(f'{stem}: {badge.profile}, {len(cuts)} measured cuts at {GAP}px')
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names', nargs='+', help='Prefixed SVG stems; omit to build all badges')
    args = parser.parse_args()
    for stem, svg in build(args.names).items():
        (ROOT / 'source/svgs' / (stem+'.svg')).write_text(svg, encoding='utf-8')
