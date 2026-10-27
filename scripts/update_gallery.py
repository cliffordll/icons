"""Refresh the standalone gallery's embedded icon list from manifest.json."""

import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    icons = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))['icons']
    icons.sort(key=lambda entry: (entry['category'], Path(entry['source']).name))
    path = root / 'gallery.html'
    content = path.read_text(encoding='utf-8')
    before, rest = content.split('const icons=', 1)
    _, after = rest.split(';function render()', 1)
    path.write_text(before + 'const icons=' + json.dumps(icons, ensure_ascii=False,
                    separators=(',', ':')) + ';function render()' + after, encoding='utf-8')
    print(f'Updated gallery with {len(icons)} icons.')


if __name__ == '__main__':
    main()
