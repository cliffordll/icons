"""Validate the file SVG contract, geometric gaps and font-free PNG rendering."""

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from PIL import Image
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path

from scripts import render_file_icons as renderer

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'


class FileVectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        cls.entries = [e for e in cls.manifest['icons'] if e['category'] == 'files']

    def test_format_circles_and_outlined_labels_follow_manifest(self):
        self.assertEqual(len(self.entries), 120)
        for entry in self.entries:
            with self.subTest(icon=entry['name']):
                svg = ET.parse(ROOT / entry['vector_source']).getroot()
                circle = svg.find('.//*[@data-role="format-circle"]')
                if entry['name'] == 'new':
                    self.assertIsNone(circle)
                    continue
                self.assertEqual(circle.get('fill'), entry['circle_color'])
                self.assertEqual([float(circle.get(k)) for k in ('cx', 'cy', 'r')], [12, 13.5, 7.5])
                label = svg.find('.//*[@data-role="label"]')
                self.assertEqual(label.get('fill'), '#3B3B3B')
                self.assertEqual(len(label.findall(NS+'path')), len(entry['display_label']))

    def test_gapped_frames_leave_both_sides_open_and_keep_the_fold(self):
        metrics = self.manifest['file_frame']['text_metrics']
        base = ET.parse(ROOT / 'source/svgs/tools/file-file.svg').find('.//*[@id="document"]').get('d')
        for entry in self.entries:
            if entry['name'] == 'new':
                continue
            with self.subTest(icon=entry['name']):
                svg = ET.parse(ROOT / entry['vector_source']).getroot()
                document = svg.find('.//*[@id="document"]')
                record = metrics[entry['name']]
                if not record['frame_gaps']:
                    self.assertEqual(document.get('d'), base)
                    continue
                self.assertEqual(document.get('stroke-linecap'), 'butt')
                self.assertEqual(svg.find('.//*[@data-role="fold"]').get('d'), 'M14.5 2.8V7.6H19.3')
                top = record['baseline']-record['cap_height']-2
                bottom = record['baseline']+2
                pen = RecordingPen()
                parse_path(document.get('d'), pen)
                # The upper contour must wrap continuously around the original
                # top-left start. A third subpath leaves two antialiased caps.
                self.assertEqual(sum(command == 'moveTo' for command, _ in pen.value), 2)
                for index, (command, values) in enumerate(pen.value):
                    if command != 'moveTo':
                        continue
                    start = values[0]
                    end = pen.value[index+1:]
                    next_move = next((i for i, item in enumerate(end) if item[0] == 'moveTo'), len(end))
                    finish = next(values[-1] for _, values in reversed(end[:next_move]) if values)
                    for point in (start, finish):
                        self.assertIn(point[0], (4.7, 19.3))
                        self.assertTrue(any(abs(point[1]-y)<1e-8 for y in (top, bottom)))
                current = None
                cut_ends = []
                for command, values in pen.value:
                    if command == 'moveTo':
                        current = values[0]
                    elif command == 'lineTo':
                        target = values[0]
                        if current[0] == target[0] and current[0] in (4.7, 19.3):
                            low, high = sorted((current[1], target[1]))
                            self.assertTrue(high <= top+1e-8 or low >= bottom-1e-8)
                            cut_ends.extend((current, target))
                        current = target
                    elif values:
                        current = values[-1]
                for x in (4.7, 19.3):
                    for y in (top, bottom):
                        self.assertTrue(any(abs(p[0]-x)<1e-8 and abs(p[1]-y)<1e-8 for p in cut_ends))

    def test_all_png_sizes_are_rendered_from_the_registered_file_svg(self):
        for entry in self.entries:
            svg = ET.parse(ROOT / entry['vector_source']).getroot()
            for size in (384, *self.manifest['sizes']):
                with self.subTest(icon=entry['name'], size=size):
                    png = (ROOT / entry['source'] if size == 384 else
                           ROOT / str(size) / 'files' / Path(entry['source']).name)
                    with Image.open(png) as actual:
                        expected = renderer.rasterize_svg(svg, size)
                        self.assertEqual(actual.convert('RGBA').tobytes(), expected.tobytes())

    def test_special_new_keeps_the_tool_svg_geometry(self):
        def geometry(path):
            return [(node.tag, node.attrib) for node in ET.parse(path).getroot().iter()]
        self.assertEqual(geometry(ROOT / 'source/svgs/files/other-new.svg'),
                         geometry(ROOT / 'source/svgs/tools/file-new.svg'))

    def test_render_only_works_without_font_access(self):
        entry = next(e for e in self.entries if e['name'] == 'txt')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'manifest.json').write_text(json.dumps(self.manifest), encoding='utf-8')
            vector = root / entry['vector_source']
            vector.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / entry['vector_source'], vector)
            for folder in ('source', '24', '30', '36', '48'):
                (root / folder / 'files').mkdir(parents=True, exist_ok=True)
            with patch.object(renderer, 'ROOT', root), patch.object(sys, 'argv',
                    ['render_file_icons.py', '--render-only', '--names', 'txt', '--font', 'missing.ttf']), \
                    patch.object(renderer, 'outline_font', side_effect=AssertionError('Font accessed')):
                renderer.main()
            self.assertEqual((root / 'manifest.json').read_text(), json.dumps(self.manifest))
            for size in self.manifest['sizes']:
                with Image.open(root / str(size) / 'files' / Path(entry['source']).name) as image:
                    self.assertEqual(image.size, (size, size))


if __name__ == '__main__':
    unittest.main()
