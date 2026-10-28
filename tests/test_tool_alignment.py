"""Check rendered subject alignment and shared geometry of paired tools."""

import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from PIL import Image
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import SVGPath, parse_path


ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'
CENTERED = [
    'edit-text-add', 'edit-line-break-remove', 'edit-case-check',
    'edit-handwriting', 'net-websocket', 'view-locations', 'file-tags',
    'sys-run-debug', 'user-feedback', 'lock-lock', 'user-user', 'user-contact',
    'edit-align-left', 'edit-align-center', 'edit-align-right', 'edit-columns',
    'edit-stripes', 'edit-text-off', 'file-barcode', 'file-image', 'file-qrcode', 'file-save',
    'edit-plus-square', 'edit-minus-square', 'edit-change', 'view-list-bullet', 'view-list-circle',
    'view-list-circle-two', 'view-list-square-two', 'view-list-square', 'task-batch', 'edit-list-ordered',
]


def visible_bounds(path):
    with Image.open(path) as image:
        return image.getchannel('A').point(lambda value: 255 if value >= 128 else 0).getbbox()


class ToolAlignmentTests(unittest.TestCase):
    def test_boxed_plus_minus_and_change_share_symbol_geometry(self):
        groups = [ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot().find(NS+'g')
                  for stem in ['edit-plus-square', 'edit-minus-square', 'edit-change']]
        plus, minus, change = [group.findall(NS+'path') for group in groups]
        self.assertEqual(plus[0].attrib['d'], minus[0].attrib['d'])
        lengths = []
        for paths in [plus, minus, change]:
            for path in paths:
                pen = RecordingPen()
                parse_path(path.attrib['d'], pen)
                start, end = pen.value[0][1][0], pen.value[1][1][0]
                lengths.append(math.dist(start, end))
        self.assertTrue(all(abs(length-lengths[0]) < 0.000001 for length in lengths))
        self.assertTrue(all(group[0].attrib == groups[0][0].attrib for group in groups))

    def test_list_family_shares_rows_ink_gap_and_right_edge(self):
        counts = {'view-list-circle': 3, 'view-list-circle-two': 2,
                  'view-list-square': 3, 'view-list-square-two': 2,
                  'task-batch': 3, 'edit-list-ordered': 2}
        shared_rows = {}
        for stem, count in counts.items():
            with self.subTest(stem=stem):
                root = ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
                group = root.find(NS+'g')
                self.assertEqual(group.attrib['stroke-width'], '1.35')
                self.assertTrue(all('transform' not in node.attrib for node in root.iter()))
                markers = group.findall('*[@data-role="marker"]')
                rows = group.findall('*[@data-role="row"]')
                self.assertEqual(len(markers), count)
                self.assertEqual(len(rows), count)
                positions = []
                for marker, row in zip(markers, rows):
                    pen = BoundsPen(None)
                    wrapper = ET.Element(NS+'svg')
                    wrapper.append(marker)
                    SVGPath.fromstring(ET.tostring(wrapper)).draw(pen)
                    x0, y0, x1, y1 = pen.bounds
                    half = 0 if marker.attrib.get('stroke') == 'none' else 0.675
                    row_pen = RecordingPen()
                    parse_path(row.attrib['d'], row_pen)
                    start, end = row_pen.value[0][1][0], row_pen.value[1][1][0]
                    self.assertAlmostEqual(start[1], end[1], delta=0.000001)
                    self.assertAlmostEqual((y0+y1)/2, start[1], delta=0.001)
                    self.assertAlmostEqual(end[0], 20.575, delta=0.000001)
                    self.assertAlmostEqual(x0-half, 2.75, delta=0.001)
                    self.assertAlmostEqual(start[0]-0.675-(x1+half), 1.35, delta=0.001)
                    positions.append(start[1])
                if count not in shared_rows:
                    shared_rows[count] = positions
                self.assertEqual(positions, shared_rows[count])

    def test_task_batch_reuses_empty_square_layout_and_keeps_check_inside(self):
        roots = [ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
                 for stem in ['task-batch', 'view-list-square']]
        for role in ['marker', 'row']:
            self.assertEqual([e.attrib for e in roots[0].findall('.//*[@data-role="'+role+'"]')],
                             [e.attrib for e in roots[1].findall('.//*[@data-role="'+role+'"]')])
        marker = roots[0].findall('.//*[@data-role="marker"]')[1]
        check = roots[0].find('.//*[@data-role="check"]')
        self.assertIsNotNone(check)
        self.assertEqual(float(check.attrib['stroke-width']), 1.0)
        check_half = float(check.attrib['stroke-width'])/2
        pen = BoundsPen(None)
        parse_path(check.attrib['d'], pen)
        x0, y0, x1, y1 = pen.bounds
        bx, by = float(marker.attrib['x']), float(marker.attrib['y'])
        bw, bh = float(marker.attrib['width']), float(marker.attrib['height'])
        self.assertGreaterEqual(x0-check_half, bx+0.675)
        self.assertGreaterEqual(y0-check_half, by+0.675)
        self.assertLessEqual(x1+check_half, bx+bw-0.675)
        self.assertLessEqual(y1+check_half, by+bh-0.675)

    def test_alignment_and_columns_share_list_envelope_and_rows(self):
        reference = visible_bounds(ROOT / 'source/tools/view-list.png')
        rows = None
        for stem in ['edit-align-left', 'edit-align-center', 'edit-align-right', 'edit-columns']:
            with self.subTest(stem=stem):
                actual = visible_bounds(ROOT / 'source/tools' / (stem+'.png'))
                self.assertEqual(actual, reference)
                root = ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
                pen = RecordingPen()
                parse_path(root.find('.//'+NS+'path').attrib['d'], pen)
                ys = sorted({p[1] for _, points in pen.value for p in points})
                if rows is None:
                    rows = ys
                self.assertEqual(len(ys), 4)
                self.assertEqual(ys, rows)

    def test_text_off_retains_visible_gap_after_compacting(self):
        root = ET.parse(ROOT / 'source/svgs/edit-text-off.svg').getroot()
        text = root.find('.//*[@data-role="text"]')
        cuts = [tuple(map(float, point.split(','))) for point in text.attrib['data-cutpoints'].split()]
        self.assertEqual(len(cuts), 6)
        pen = RecordingPen()
        parse_path(text.attrib['d'], pen)
        endpoints = [p for _, points in pen.value for p in points]
        for x, y in cuts:
            gap = abs(x-y)/math.sqrt(2)-1.35
            self.assertAlmostEqual(gap, 0.6, delta=0.000001)
            self.assertLess(min(math.dist((x, y), p) for p in endpoints), 0.000001)

    def test_image_and_qrcode_share_grid_size_without_scaled_strokes(self):
        for stem in ['file-image', 'file-qrcode']:
            with self.subTest(stem=stem):
                root = ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
                pen = BoundsPen(None)
                SVGPath.fromstring(ET.tostring(root)).draw(pen)
                for actual, expected in zip(pen.bounds, (3.675, 3.675, 20.325, 20.325)):
                    self.assertAlmostEqual(actual, expected, delta=0.001)
                self.assertEqual(root.find(NS+'g').attrib['stroke-width'], '1.35')
                self.assertTrue(all('transform' not in node.attrib for node in root.iter()))
                for rectangle in root.findall('.//'+NS+'rect'):
                    if 'rx' in rectangle.attrib:
                        self.assertEqual(rectangle.attrib['rx'], '0.6')

    def test_framed_symbols_share_bounds_and_have_inner_clearance(self):
        stems = ['edit-align-right-frame', 'edit-text-vertical-frame', 'sys-html-round',
                 'lock-lock-frame', 'lock-password-frame', 'lock-key-frame',
                 'edit-plus-square', 'edit-minus-square', 'edit-change']
        outer = {'x': '3.675', 'y': '3.675', 'width': '16.65', 'height': '16.65', 'rx': '0.6'}
        for stem in stems:
            with self.subTest(stem=stem):
                root = ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
                group = root.find(NS+'g')
                self.assertEqual(group[0].attrib, outer)
                self.assertEqual(group.attrib['stroke-width'], '1.35')
                self.assertTrue(all('transform' not in node.attrib for node in root.iter()))
                for element in list(group)[1:]:
                    pen = BoundsPen(None)
                    wrapper = ET.Element(NS+'svg')
                    wrapper.append(element)
                    SVGPath.fromstring(ET.tostring(wrapper)).draw(pen)
                    x0, y0, x1, y1 = pen.bounds
                    half_stroke = 0 if element.attrib.get('stroke') == 'none' else 0.675
                    # Border's inner edges are 4.35 and 19.65; measure ink edges.
                    padding = min(x0-half_stroke-4.35, y0-half_stroke-4.35,
                                  19.65-x1-half_stroke, 19.65-y1-half_stroke)
                    self.assertGreaterEqual(padding, 1.2)

    def test_text_crop_keeps_fullscreen_corners(self):
        crop = ET.parse(ROOT / 'source/svgs/edit-text-crop.svg').getroot()
        fullscreen = ET.parse(ROOT / 'source/svgs/view-fullscreen.svg').getroot()
        self.assertEqual(crop.find('.//'+NS+'path').attrib['d'],
                         fullscreen.find('.//'+NS+'path').attrib['d'])

    def test_rendered_subjects_are_centered_at_source_and_native_sizes(self):
        for stem in CENTERED:
            for folder, size in [('source', 384), ('24', 24), ('30', 30), ('36', 36), ('48', 48)]:
                with self.subTest(stem=stem, size=size):
                    x0, y0, x1, y1 = visible_bounds(ROOT / folder / 'tools' / (stem+'.png'))
                    tolerance = 0.04*size/24 if size == 384 else 0.5
                    self.assertAlmostEqual((x0+x1)/2, size/2, delta=tolerance)
                    self.assertAlmostEqual((y0+y1)/2, size/2, delta=tolerance)

    def test_lock_pair_shares_body_keyhole_and_stem(self):
        roots = [ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
                 for stem in ['lock-lock', 'lock-unlock']]
        for role in ['lock-body', 'key-hole', 'key-stem']:
            elements = [root.find('.//*[@data-role="'+role+'"]') for root in roots]
            self.assertIsNotNone(elements[0], role)
            self.assertIsNotNone(elements[1], role)
            self.assertEqual(elements[0].attrib, elements[1].attrib, role)
        for root in roots:
            group = root.find(NS+'g')
            self.assertEqual(group.attrib['stroke-width'], '1.35')
            self.assertTrue(all('transform' not in node.attrib for node in root.iter()))
            hole = root.find('.//*[@data-role="key-hole"]')
            self.assertEqual(hole.attrib['r'], '1')
        # The open shackle changes its upper bound. Align the shared body,
        # rather than independently moving the unlock icon by its whole bbox.
        x0, y0, x1, y1 = visible_bounds(ROOT / 'source/tools/lock-unlock.png')
        self.assertAlmostEqual((x0+x1)/32, 12, delta=0.04)
        self.assertLessEqual(abs((y0+y1)/32-12), 0.2)


if __name__ == '__main__':
    unittest.main()
