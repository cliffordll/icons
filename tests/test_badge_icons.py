"""Regression checks for delivered corner badges, independent of the builder."""

import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

ROOT = Path(__file__).resolve().parents[1]
NS = '{http://www.w3.org/2000/svg}'


def read(stem):
    root = ET.parse(ROOT / 'source/svgs' / (stem + '.svg')).getroot()
    return (root.find('.//'+NS+'g[@data-role="background"]'),
            root.find('.//'+NS+'g[@data-role="badge"]'))


def flatten(d):
    pen = RecordingPen()
    parse_path(d, pen)
    lines = []
    current = start = None
    for cmd, values in pen.value:
        if cmd == 'moveTo':
            current = start = values[0]
        elif cmd == 'lineTo':
            lines.append((current, values[0]))
            current = values[0]
        elif cmd in ('curveTo', 'qCurveTo'):
            controls = (current, *values)
            previous = current
            for j in range(1, 129):
                t = j/128
                degree = len(controls)-1
                xy = tuple(sum(math.comb(degree, i)*(1-t)**(degree-i)*t**i*p[k]
                               for i, p in enumerate(controls)) for k in (0, 1))
                lines.append((previous, xy))
                previous = xy
            current = values[-1]
        elif cmd == 'closePath':
            lines.append((current, start))
            current = start
    return lines


def distance(p, line):
    a, b = line
    v = (b[0]-a[0], b[1]-a[1])
    length = v[0]**2+v[1]**2
    t = min(1, max(0, ((p[0]-a[0])*v[0]+(p[1]-a[1])*v[1])/length)) if length else 0
    return math.dist(p, (a[0]+t*v[0], a[1]+t*v[1]))


class BadgeIconTests(unittest.TestCase):
    def test_background_centering_moves_subject_and_badge_together(self):
        # Expected translations come from complete subjects, before badge cutouts.
        offsets = {
            'net-cloud-search': (0.194821512, 1.661127871),
            'lock-shield-search': (0.9375, 0.25),
            'file-print-preview': (0.25, 0.5),
            'file-review': (1, 0.25), 'edit-paste': (1, 0.25),
            'play-player-setting': (0.525, 0), 'sys-remote': (0.525, 0),
        }
        stems = ['net-cloud-search', 'net-globe-search', 'lock-shield-search',
                 'file-print-preview', 'file-review', 'view-location-search',
                 'view-location-settings', 'play-player-setting', 'sys-remote',
                 'view-map-code', 'net-server-bolt', 'user-send-code',
                 'user-send-download', 'user-send-percent', 'edit-paste']
        for stem in stems:
            with self.subTest(stem=stem):
                root = ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
                group = root.find(NS+'g[@data-role="centered-composite"]')
                dx, dy = map(float, group.attrib['transform'][10:-1].split())
                for actual, expected in zip((dx, dy), offsets.get(stem, (0, 0))):
                    self.assertAlmostEqual(actual, expected, delta=0.000001)
                self.assertIsNotNone(group.find(NS+'g[@data-role="background"]'))
                self.assertIsNotNone(group.find(NS+'g[@data-role="badge"]'))
                self.assertTrue(all('transform' not in child.attrib for child in group))

    def test_location_holes_share_enlarged_radius_and_allow_badge_cutouts(self):
        root = ET.parse(ROOT / 'source/svgs/view-location.svg').getroot()
        self.assertEqual(float(root.find('.//'+NS+'circle').attrib['r']), 2.75)
        for stem in ['view-location-search', 'view-location-settings']:
            with self.subTest(stem=stem):
                back, _ = read(stem)
                outline = [line for path in back for line in flatten(path.attrib['d'])]
                # Preserve the enlarged circle away from the lower-right badge.
                for j in range(20, 64):
                    angle = 2*math.pi*j/64
                    p = (12+2.75*math.cos(angle), 9.75+2.75*math.sin(angle))
                    self.assertLess(min(distance(p, line) for line in outline), 0.002)
                missing = []
                for j in range(16):
                    angle = 2*math.pi*j/64
                    p = (12+2.75*math.cos(angle), 9.75+2.75*math.sin(angle))
                    missing.append(min(distance(p, line) for line in outline))
                self.assertGreater(max(missing), 0.05)

    def test_globe_search_keeps_full_size_globe_geometry(self):
        back, _ = read('net-globe-search')
        pen = BoundsPen(None)
        for path in back:
            parse_path(path.attrib['d'], pen)
        for actual, expected in zip(pen.bounds, (2.675, 2.675, 21.325, 21.325)):
            self.assertAlmostEqual(actual, expected, delta=0.002)
        lines = [line for path in back for line in flatten(path.attrib['d'])]
        for p in [(3, 12), (7.9, 12), (12, 2.675), (12, 21.325)]:
            self.assertLess(min(distance(p, line) for line in lines), 0.002)

    def test_all_corner_badges_use_the_raised_position(self):
        stems = ['net-cloud-search', 'net-globe-search', 'lock-shield-search',
                 'file-print-preview', 'file-review', 'view-location-search',
                 'view-location-settings', 'play-player-setting', 'sys-remote',
                 'view-map-code', 'net-server-bolt', 'user-send-code',
                 'user-send-download', 'user-send-percent', 'edit-paste']
        for stem in stems:
            with self.subTest(stem=stem):
                _, badge = read(stem)
                pen = BoundsPen(None)
                for path in badge:
                    parse_path(path.attrib['d'], pen)
                _, y0, _, y1 = pen.bounds
                self.assertAlmostEqual((y0+y1)/2, 16.75, delta=0.001)

    def test_all_corner_badges_share_ten_point_five_pixel_visual_envelope(self):
        stems = ['net-cloud-search', 'net-globe-search', 'lock-shield-search',
                 'file-print-preview', 'file-review', 'view-location-search',
                 'view-location-settings', 'play-player-setting', 'sys-remote',
                 'view-map-code', 'net-server-bolt', 'user-send-code',
                 'user-send-download', 'user-send-percent', 'edit-paste']
        for stem in stems:
            with self.subTest(stem=stem):
                _, badge = read(stem)
                pen = BoundsPen(None)
                for path in badge:
                    parse_path(path.attrib['d'], pen)
                x0, y0, x1, y1 = pen.bounds
                stroke = float(badge.attrib.get('stroke-width', '1.35'))
                width, height = x1-x0+stroke, y1-y0+stroke
                self.assertAlmostEqual(max(width, height), 10.5, delta=0.007)
                self.assertGreaterEqual(min(width, height), 9.42)

    def test_all_floating_badge_cutpoints_have_uniform_visible_gaps(self):
        stems = ['net-cloud-search', 'net-globe-search', 'lock-shield-search',
                 'file-print-preview', 'file-review', 'view-location-search',
                 'view-location-settings', 'play-player-setting', 'sys-remote',
                 'view-map-code', 'net-server-bolt', 'user-send-code',
                 'user-send-download', 'user-send-percent', 'edit-paste']
        for stem in stems:
            with self.subTest(stem=stem):
                back, badge = read(stem)
                cutpoints = [tuple(map(float, p.split(',')))
                             for p in back.attrib['data-cutpoints'].split()]
                self.assertTrue(cutpoints)
                lines = [line for p in badge for line in flatten(p.attrib['d'])]
                stroke_inset = 0.675 + float(badge.attrib.get('stroke-width', '1.35'))/2
                for p in cutpoints:
                    measured = min(distance(p, line) for line in lines)-stroke_inset
                    self.assertAlmostEqual(measured, 0.6, delta=0.004)

    def test_all_search_badges_use_identical_geometry(self):
        stems = ['net-cloud-search', 'net-globe-search', 'lock-shield-search',
                 'file-print-preview', 'file-review', 'view-location-search']
        expected = None
        for stem in stems:
            _, badge = read(stem)
            self.assertIsNotNone(badge, stem)
            geometry = [p.attrib['d'] for p in badge]
            if expected is None:
                expected = geometry
            self.assertEqual(geometry, expected, stem)

    def test_monitor_map_and_paper_plane_share_code_badge(self):
        self.assertEqual([p.attrib['d'] for p in read('view-map-code')[1]],
                         [p.attrib['d'] for p in read('user-send-code')[1]])
        self.assertEqual([p.attrib['d'] for p in read('sys-remote')[1]],
                         [p.attrib['d'] for p in read('user-send-code')[1]])

    def test_code_badge_interior_does_not_reveal_background_fragments(self):
        for stem in ['sys-remote', 'view-map-code', 'user-send-code']:
            with self.subTest(stem=stem):
                back, _ = read(stem)
                lines = [line for path in back for line in flatten(path.attrib['d'])]
                self.assertGreater(min(distance((17.5, 16.75), line) for line in lines), 2)

    def test_paper_plane_wing_gaps_are_measured_from_each_glyph(self):
        for stem in ['user-send-code', 'user-send-percent', 'user-send-download']:
            with self.subTest(stem=stem):
                back, badge = read(stem)
                cutpoints = [tuple(map(float, p.split(',')))
                             for p in back.attrib['data-cutpoints'].split()]
                self.assertEqual(len(cutpoints), 2)
                glyph_lines = [line for p in badge for line in flatten(p.attrib['d'])]
                background_lines = flatten(back[0].attrib['d'])
                for p in cutpoints:
                    measured = min(distance(p, line) for line in glyph_lines)-1.35
                    self.assertAlmostEqual(measured, 0.6, delta=0.004)
                    # The recorded cut must actually exist on the delivered path.
                    self.assertLess(min(math.dist(p, q) for line in background_lines
                                        for q in line), 0.00001)


if __name__ == '__main__':
    unittest.main()
