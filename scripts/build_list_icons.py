"""Build list variants with shared row positions, strokes and visible spacing."""

from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
STROKE = 1.35
CHECK_STROKE = 1.0
LEFT = 3.425
RIGHT = 20.575
MARKER_GAP = 1.35
ROWS = {2: (7, 17), 3: (5.85, 12, 18.15)}
BOX_WIDTH = 4.8
BOX_HEIGHT = 4.2
CIRCLE_RADIUS = 2.1
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])


def build(stem, kind, count, checked=False):
    svg = ET.Element(NS+'svg', {'width': '384', 'height': '384', 'viewBox': '0 0 24 24'})
    group = ET.SubElement(svg, NS+'g', {
        'data-role': 'list-layout', 'data-marker': kind,
        'data-rows': ' '.join(map(str, ROWS[count])),
        'fill': 'none', 'stroke': '#444444', 'stroke-width': str(STROKE),
        'stroke-linecap': 'round', 'stroke-linejoin': 'round',
    })
    for index, y in enumerate(ROWS[count]):
        if kind == 'square':
            ET.SubElement(group, NS+'rect', {
                'data-role': 'marker', 'x': str(LEFT), 'y': str(y-BOX_HEIGHT/2),
                'width': str(BOX_WIDTH), 'height': str(BOX_HEIGHT), 'rx': '0.6',
            })
            marker_ink_right = LEFT+BOX_WIDTH+STROKE/2
        elif kind == 'circle':
            ET.SubElement(group, NS+'circle', {
                'data-role': 'marker', 'cx': str(LEFT+CIRCLE_RADIUS),
                'cy': str(y), 'r': str(CIRCLE_RADIUS),
            })
            marker_ink_right = LEFT+2*CIRCLE_RADIUS+STROKE/2
        elif kind == 'number':
            if index == 0:
                d = f'M{LEFT} {y-1.5}l2-1v5M{LEFT} {y+2.5}h4'
            else:
                d = (f'M{LEFT} {y-1.25}C{LEFT} {y-2.916666667} '
                     f'{LEFT+4} {y-2.916666667} {LEFT+4} {y-1.25}'
                     f'C{LEFT+4} {y+0.05} {LEFT} {y+1} {LEFT} {y+2.5}H{LEFT+4}')
            ET.SubElement(group, NS+'path', {'data-role': 'marker', 'd': d})
            marker_ink_right = LEFT+4+STROKE/2
        else:
            raise ValueError(kind)
        # Align visible edges and keep a common gap beside each marker shape.
        start = marker_ink_right+MARKER_GAP+STROKE/2
        ET.SubElement(group, NS+'path', {
            'data-role': 'row', 'd': f'M{start:.9f} {y}H{RIGHT}',
        })
    if checked:
        # Keep the original task-batch meaning; the tick fits inside its box.
        ET.SubElement(group, NS+'path', {
            'data-role': 'check', 'stroke-width': str(CHECK_STROKE),
            'd': f'M{LEFT+1.525} 12 {LEFT+2.175} 12.65 {LEFT+3.375} 11.4',
        })
    ET.indent(svg, space='  ')
    (ROOT / 'source/svgs' / (stem+'.svg')).write_text(
        ET.tostring(svg, encoding='unicode')+'\n', encoding='utf-8')


def main():
    variants = [
        ('view-list-square-two', 'square', 2, False),
        ('view-list-square', 'square', 3, False),
        ('task-batch', 'square', 3, True),
        ('view-list-circle-two', 'circle', 2, False),
        ('view-list-circle', 'circle', 3, False),
        ('edit-list-ordered', 'number', 2, False),
    ]
    for args in variants:
        build(*args)
    print(f'Built {len(variants)} list icons with shared geometry and {MARKER_GAP}px marker gaps.')


if __name__ == '__main__':
    main()
