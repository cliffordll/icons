"""Build search and zoom variants from the same magnifier template as badges."""

from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'
ET.register_namespace('', NS[1:-1])


def build():
    for stem, symbol in [('view-search', ''), ('view-zoom-in', 'M7.75 10.3h5M10.25 7.8v5'),
                         ('view-zoom-out', 'M7.75 10.3h5')]:
        svg = ET.parse(ROOT / 'scripts/icon_templates/magnifier.svg').getroot()
        group = svg.find(NS+'g')
        if symbol:
            ET.SubElement(group, NS+'path', {'data-role': 'symbol', 'd': symbol})
        ET.indent(svg, space='  ')
        (ROOT / 'source/svgs' / (stem+'.svg')).write_text(
            ET.tostring(svg, encoding='unicode')+'\n', encoding='utf-8')


if __name__ == '__main__':
    build()
