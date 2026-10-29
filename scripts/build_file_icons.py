"""Build document-derived tool SVGs from the shared file-file base."""

from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def build_file_new():
    base = ET.parse(ROOT / 'source/svgs/file-file.svg').getroot()
    document = base.find(f'.//{{{NS}}}path[@id="document"]')
    if document is None:
        raise ValueError('file-file.svg is missing its document base path')

    svg = ET.Element(f'{{{NS}}}svg', {
        'width': '384', 'height': '384', 'viewBox': '0 0 24 24'})
    group = ET.SubElement(svg, f'{{{NS}}}g', {
        'fill': 'none', 'stroke': '#444444', 'stroke-width': '1.35',
        'stroke-linecap': 'round', 'stroke-linejoin': 'round'})
    ET.SubElement(group, f'{{{NS}}}path', {
        'id': 'document', 'data-role': 'document', 'd': document.attrib['d']})
    ET.SubElement(group, f'{{{NS}}}path', {
        'data-role': 'plus', 'd': 'M9.5 14.4875h5M12 11.9875v5'})

    target = ROOT / 'source/svgs/file-new.svg'
    target.write_text(ET.tostring(svg, encoding='unicode') + '\n', encoding='utf-8')
    print(f'Generated {target.relative_to(ROOT)} from file-file.svg')


if __name__ == '__main__':
    build_file_new()
