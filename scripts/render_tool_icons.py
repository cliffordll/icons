"""Render registered SVG tool icons directly at every supported PNG size."""

import argparse
import json
from pathlib import Path
import tempfile

import wx
import wx.svg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT if (PROJECT_ROOT / 'manifest.json').is_file() else PROJECT_ROOT / 'icons'
SOURCE_SIZE = 384


def save_image(image, path):
    """Replace a PNG only after its complete new image has been written."""
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.png', delete=False) as output:
        temporary = Path(output.name)
    try:
        if not image.SaveFile(str(temporary), wx.BITMAP_TYPE_PNG):
            raise OSError(f'Cannot write icon: {path}')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--names', nargs='+', help='Render only these SVG tool icons')
    selection.add_argument('--all', action='store_true', help='Render every registered SVG tool icon')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    tools = {entry['name']: entry for entry in manifest['icons']
             if entry['category'] == 'tools' and entry.get('vector_source')}
    if args.names:
        unknown = set(args.names) - tools.keys()
        if unknown:
            parser.error(f'Tool icons without a registered SVG: {sorted(unknown)}')
        tools = {name: tools[name] for name in dict.fromkeys(args.names)}
    entries = list(tools.values())
    for entry in entries:
        for key in ('vector_source', 'source'):
            path = (ROOT / entry[key]).resolve()
            valid = (path.is_file() if key == 'vector_source'
                     else path.parent.is_dir() and path.suffix.lower() == '.png'
                     and (not path.exists() or path.is_file()))
            if not path.is_relative_to(ROOT.resolve()) or not valid:
                parser.error(f'Invalid icon {key}: {entry[key]}')

    app = wx.App(False)
    vectors = {}
    changed = 0
    checked = 0
    for entry in entries:
        source = entry['vector_source']
        if source not in vectors:
            vectors[source] = wx.svg.SVGimage.CreateFromFile(str(ROOT / source))
        vector = vectors[source]
        for size in (SOURCE_SIZE, *manifest['sizes']):
            path = ROOT / entry['source'] if size == SOURCE_SIZE else (
                ROOT / str(size) / entry['category'] / Path(entry['source']).name)
            image = vector.ConvertToBitmap(
                scale=size / vector.width, width=size, height=size).ConvertToImage()
            if not image.IsOk() or not image.HasAlpha():
                raise ValueError(f'Invalid SVG rendering: {source} at {size}px')
            previous = wx.Image(str(path), wx.BITMAP_TYPE_PNG) if path.is_file() else None
            equal = (previous is not None and previous.IsOk()
                     and previous.GetSize() == image.GetSize() and previous.HasAlpha()
                     and bytes(previous.GetData()) == bytes(image.GetData())
                     and bytes(previous.GetAlpha()) == bytes(image.GetAlpha()))
            if not equal:
                save_image(image, path)
                changed += 1
            checked += 1
    print(f'Rendered {len(tools)} SVG tool icons; '
          f'{changed} PNGs updated, {checked} PNGs checked.')


if __name__ == '__main__':
    main()
