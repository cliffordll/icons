"""Build outline-circle controls from one shared frame."""

import argparse
from pathlib import Path

if __package__:
    from .control_geometry import FRAME, circle_glyphs
else:
    from control_geometry import FRAME, circle_glyphs


ROOT = Path(__file__).resolve().parents[1]
GLYPHS = {
    'play-wave-circle': '<path d="M7 10.5v3M9.5 9v6M12 7.5v9M14.5 9.5v5M17 10.5v3"/>',
}
GLYPHS.update(circle_glyphs())


def build(stem):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="384" height="384" viewBox="0 0 24 24">\n'
        '  <g fill="none" stroke="#444444" stroke-width="1.35" '
        'stroke-linecap="round" stroke-linejoin="round">\n'
        f'    {FRAME}\n'
        f'    {GLYPHS[stem]}\n'
        '  </g>\n'
        '</svg>\n'
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--names', nargs='+', choices=sorted(GLYPHS),
                        help='Prefixed SVG stems; omit to build the full group')
    args = parser.parse_args()
    for stem in args.names or GLYPHS:
        (ROOT / 'source/svgs/tools' / (stem+'.svg')).write_text(build(stem), encoding='utf-8')
    print(f'Built {len(args.names or GLYPHS)} circle controls.')


if __name__ == '__main__':
    main()
