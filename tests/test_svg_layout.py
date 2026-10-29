"""Exercise generator paths in an isolated copy of the split SVG layout."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SvgLayoutTests(unittest.TestCase):
    def test_generators_and_renderers_use_category_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'scripts', root / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copytree(ROOT / 'source/svgs', root / 'source/svgs')
            shutil.copyfile(ROOT / 'manifest.json', root / 'manifest.json')
            for folder in ('source', '24', '30', '36', '48'):
                for category in ('tools', 'files'):
                    (root / folder / category).mkdir(parents=True, exist_ok=True)
            commands = [
                ['build_file_icons.py'], ['build_magnifier_icons.py'],
                ['build_list_icons.py'], ['build_control_icons.py'],
                ['build_circle_control_icons.py', '--names', 'task-retry-circle'],
                ['build_badge_icons.py', '--names', 'file-search'],
                ['render_tool_icons.py', '--names', 'view-search', 'task-retry-circle'],
                ['render_file_icons.py', '--render-only', '--names', 'pdf', 'new'],
            ]
            for command in commands:
                with self.subTest(command=command):
                    result = subprocess.run([sys.executable, str(root / 'scripts' / command[0]),
                                             *command[1:]], cwd=root, capture_output=True,
                                            text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertFalse(list((root / 'source/svgs').glob('*.svg')))
            manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
            for entry in manifest['icons']:
                self.assertEqual(Path(entry['vector_source']).parent,
                                 Path('source/svgs') / entry['category'])
                self.assertTrue((root / entry['vector_source']).is_file())
            for size in (24, 30, 36, 48):
                for category, stem in [('tools', 'view-search'), ('files', 'doc-pdf'),
                                       ('files', 'other-new')]:
                    self.assertTrue((root / str(size) / category / (stem+'.png')).is_file())


if __name__ == '__main__':
    unittest.main()
