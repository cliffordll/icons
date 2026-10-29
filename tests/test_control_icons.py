"""Check shared controls across independent, framed and compound icons."""

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'


def root(stem):
    return ET.parse(ROOT / 'source/svgs/tools' / (stem+'.svg')).getroot()


def points(node):
    pen = RecordingPen()
    parse_path(node.attrib['d'], pen)
    return [p for _, values in pen.value for p in values]


class ControlIconsTests(unittest.TestCase):
    def test_play_triangles_keep_the_same_aspect_ratio(self):
        for stem in ('play-start', 'task-task-start', 'play-start-circle', 'play-player'):
            with self.subTest(stem=stem):
                node = root(stem).findall('.//'+NS+'path')[-1 if stem == 'play-player' else 0]
                ps = points(node)
                width = max(p[0] for p in ps)-min(p[0] for p in ps)
                height = max(p[1] for p in ps)-min(p[1] for p in ps)
                self.assertAlmostEqual(width/height, 8.904/8.916, places=7)
        ps = points(root('sys-run-debug').find('.//'+NS+'path'))
        self.assertAlmostEqual((ps[2][0]-ps[1][0])/(ps[2][1]-ps[1][1]),
                               2*8.904/8.916, places=7)

    def test_pause_uses_context_spacing_and_fixed_stroke(self):
        for stem, height, gap in [('play-pause', 16, 11), ('task-task-pause', 9, 6.1875),
                                  ('play-pause-circle', 9, 6.1875)]:
            with self.subTest(stem=stem):
                svg = root(stem)
                ps = points(svg.find('.//'+NS+'path'))
                self.assertAlmostEqual(max(p[0] for p in ps)-min(p[0] for p in ps), gap)
                self.assertAlmostEqual(max(p[1] for p in ps)-min(p[1] for p in ps), height)
                self.assertEqual(svg.find(NS+'g').attrib['stroke-width'], '1.35')

    def test_compact_states_share_height_and_only_change_context_position(self):
        for suffix in ('start', 'pause', 'stop'):
            tray = root('task-task-'+suffix)
            circle = root('play-'+suffix+'-circle')
            if suffix == 'stop':
                nodes = [s.find('.//'+NS+'rect') for s in (tray, circle)]
                for node, cy in zip(nodes, (8.5, 12)):
                    self.assertEqual(float(node.attrib['height']), 9)
                    self.assertEqual(float(node.attrib['width']), 9)
                    self.assertEqual(float(node.attrib['y'])+4.5, cy)
            else:
                for svg, cy in ((tray, 8.5), (circle, 12)):
                    ps = points(svg.find('.//'+NS+'path'))
                    ys = [p[1] for p in ps]
                    self.assertEqual(max(ys)-min(ys), 9)
                    self.assertEqual((max(ys)+min(ys))/2, cy)

    def test_all_eight_trays_remain_identical(self):
        stems = ['task-task-'+suffix for suffix in ('start', 'pause', 'stop', 'resume', 'download', 'upload')]
        stems += ['task-download-all', 'task-upload-all']
        trays = [root(stem).find('.//*[@data-role="tray"]').attrib['d'] for stem in stems]
        self.assertEqual(len(set(trays)), 1)
        self.assertEqual(trays[0], 'M2.9 15.3v3.85q0 .6.6.6h17q.6 0 .6-.6V15.3')

    def test_transfer_arrowheads_have_45_degree_wings(self):
        for stem in ('task-task-download', 'task-task-upload', 'task-download-all',
                     'task-upload-all', 'view-arrow-up-circle', 'view-arrow-down-circle',
                     'task-download', 'task-upload'):
            with self.subTest(stem=stem):
                svg = root(stem)
                nodes = ([svg.find('.//*[@id="action-arrow"]')] if stem in ('task-download', 'task-upload')
                         else [n for n in svg.findall('.//'+NS+'path') if n.attrib.get('data-role') != 'tray'])
                for node in nodes:
                    wing, tip, other = points(node)[-3:]
                    for end in (wing, other):
                        self.assertAlmostEqual(abs(end[0]-tip[0]), abs(end[1]-tip[1]), places=7)

    def test_retry_variants_share_arrowhead_and_compact_arc(self):
        heads = []
        for stem in ('task-retry', 'sys-refresh', 'info-history'):
            paths = root(stem).findall('.//'+NS+'path')
            heads.append(next(n.attrib['d'] for n in paths if n.attrib.get('stroke-linejoin') == 'miter'))
        self.assertEqual(len(set(heads)), 1)
        compact = [root(s).findall('.//'+NS+'path')[0].attrib['d']
                   for s in ('task-task-resume', 'task-retry-circle')]
        self.assertEqual(compact[0], compact[1])
        compact_heads = [next(n for n in root(s).findall('.//'+NS+'path')
                              if n.attrib.get('stroke-linejoin') == 'miter')
                         for s in ('task-task-resume', 'task-retry-circle')]
        self.assertEqual(compact_heads[0].attrib['d'], compact_heads[1].attrib['d'])
        # Small contexts need longer head legs while retaining their angle/proportion.
        full_points, small_points = points(ET.fromstring(f'<path d="{heads[0]}"/>')), points(compact_heads[0])
        self.assertEqual(full_points[1], small_points[1])
        self.assertGreater(small_points[1][1]-small_points[0][1], full_points[1][1]-full_points[0][1])


if __name__ == '__main__':
    unittest.main()
