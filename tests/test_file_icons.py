import json
from pathlib import Path
import unittest

from PIL import Image
from scripts.render_file_icons import character_gap_units, MASTER_SCALE


class FileIconTests(unittest.TestCase):
    def test_file_icons_inherit_shared_style_defaults(self):
        manifest_path = Path(__file__).resolve().parents[1] / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        defaults = manifest['file_frame']['style_defaults']
        icons = [icon for icon in manifest['icons'] if icon['category'] == 'files']

        self.assertEqual(defaults['font_family'], 'Segoe UI')
        self.assertEqual(defaults['font_style'], 'Semibold')
        self.assertEqual(defaults['font_size'], 8.5)
        self.assertEqual(defaults['character_gap'], 1.0)
        self.assertEqual(defaults['character_gap_by_length'], {'4': 0.75})
        self.assertEqual(defaults['pair_spacing']['AV'], 0.25)
        self.assertEqual(defaults['pair_spacing']['TC'], 0.25)
        self.assertEqual(defaults['pair_spacing']['TO'], 0.25)
        self.assertEqual(defaults['pair_spacing']['TG'], 0.25)
        self.assertEqual(defaults['pair_spacing']['YA'], 0.25)
        self.assertEqual(defaults['pair_spacing']['YM'], 0.25)
        self.assertEqual(defaults['pair_spacing']['RT'], 0.25)
        self.assertEqual(defaults['text_offset_y'], 1.5)
        self.assertEqual(defaults['circle_offset_y'], 1.5)
        for icon in icons:
            for key in ('frame_template', 'text_offset_y', 'character_gap', 'font_size',
                        'circle_offset_y', 'circle_bounds', 'pair_spacing'):
                self.assertNotIn(key, icon, f"{icon['name']} duplicates shared style key {key}")

    def test_four_character_file_labels_use_shared_narrower_spacing(self):
        manifest_path = Path(__file__).resolve().parents[1] / 'manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        defaults = manifest['file_frame']['style_defaults']
        four_character_icons = [icon for icon in manifest['icons']
                                if icon['category'] == 'files'
                                and len(icon.get('display_label', icon['label'])) == 4]

        self.assertTrue(four_character_icons)
        self.assertEqual(defaults['character_gap_by_length']['4'], 0.75)
        self.assertTrue(all('character_gap' not in icon for icon in four_character_icons))
        self.assertEqual(manifest['file_frame']['text_metrics']['heic']['character_gap'], 0.75)

    def test_slanted_pairs_use_shared_gap_without_tightening_other_pairs(self):
        pair_spacing = {'RT': 0.25, 'AV': 0.25, 'TO': 0.25}
        self.assertEqual(character_gap_units('RTMP', round(0.75 * MASTER_SCALE), pair_spacing),
                         [round(0.25 * MASTER_SCALE), round(0.75 * MASTER_SCALE),
                          round(0.75 * MASTER_SCALE)])
        self.assertEqual(character_gap_units('AVC', MASTER_SCALE, pair_spacing),
                         [round(0.25 * MASTER_SCALE), MASTER_SCALE])
        self.assertEqual(character_gap_units('TOML', round(0.625 * MASTER_SCALE), pair_spacing),
                         [round(0.25 * MASTER_SCALE), round(0.625 * MASTER_SCALE),
                          round(0.625 * MASTER_SCALE)])

    def test_registered_file_and_tool_resources_are_complete(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        for entry in manifest['icons']:
            if entry['category'] not in ('files', 'tools'):
                continue
            with self.subTest(category=entry['category'], name=entry['name']):
                self.assertTrue((root / entry['source']).is_file())
                if entry.get('vector_source'):
                    self.assertTrue((root / entry['vector_source']).is_file())
                for size in manifest['sizes']:
                    path = root / str(size) / entry['category'] / Path(entry['source']).name
                    with Image.open(path) as image:
                        self.assertEqual(image.size, (size, size))
                        self.assertEqual(image.mode, 'RGBA')

    def test_library_excludes_consumer_app_assets(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        self.assertTrue(all(entry['category'] in ('tools', 'files')
                            for entry in manifest['icons']))
        for folder in ('source', '24', '30', '36', '48'):
            self.assertFalse((root / folder / 'app').exists())

    def test_prefixes_and_gallery_match_manifest(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        gallery = (root / 'gallery.html').read_text(encoding='utf-8')
        embedded = json.loads(gallery.split('const icons=', 1)[1].split(';function render()', 1)[0])
        key = lambda entry: (entry['category'], entry['name'])
        self.assertEqual(sorted(embedded, key=key), sorted(manifest['icons'], key=key))
        for category in ('tools', 'files'):
            entries = [e for e in manifest['icons'] if e['category'] == category]
            expected = {Path(e['source']).name for e in entries}
            for directory in ('source', *(str(s) for s in manifest['sizes'])):
                actual = {p.name for p in (root / directory / category).glob('*.png')}
                self.assertEqual(actual, expected)
            for entry in entries:
                self.assertRegex(entry['group'], r'^[a-z]{3,5}$')
                self.assertEqual(Path(entry['source']).stem, f"{entry['group']}-{entry['name']}")
                if entry.get('vector_source'):
                    self.assertEqual(Path(entry['vector_source']).stem, Path(entry['source']).stem)
                    self.assertEqual(Path(entry['vector_source']).parent,
                                     Path('source/svgs'))
            self.assertFalse(list((root / 'source' / category).glob('*.svg')))


if __name__ == '__main__':
    unittest.main()
