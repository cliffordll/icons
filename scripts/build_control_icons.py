"""Build the full playback, transfer and ring-arrow families from shared glyphs."""

from pathlib import Path
import xml.etree.ElementTree as ET

if __package__:
    from . import control_geometry as geometry
else:
    import control_geometry as geometry

ROOT = Path(__file__).resolve().parents[1]
NS = geometry.NS
ET.register_namespace('', NS[1:-1])


def svg(markup):
    return ET.fromstring('<svg xmlns="http://www.w3.org/2000/svg" width="384" height="384" viewBox="0 0 24 24">'
                        '<g fill="none" stroke="#444444" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">'
                        +markup+'</g></svg>')


def save(stem, root):
    ET.indent(root, space='  ')
    (ROOT / 'source/svgs' / (stem+'.svg')).write_text(
        ET.tostring(root, encoding='unicode')+'\n', encoding='utf-8')


def build():
    result = {
        'play-start': geometry.play(height=16, optical=False),
        'play-pause': geometry.pause(height=16, gap=11), 'play-stop': geometry.stop(size=16),
        'task-task-start': geometry.play(cy=8.5, optical=False), 'task-task-pause': geometry.pause(cy=8.5),
        'task-task-stop': geometry.stop(cy=8.5), 'task-task-resume': geometry.ring(cy=8.5, compact=True),
        'task-task-download': geometry.arrow('down', cy=8.5),
        'task-task-upload': geometry.arrow('up', cy=8.5),
        'task-download-all': geometry.arrow('down', cx=7, cy=8.5)+geometry.arrow('down', cx=17, cy=8.5),
        'task-upload-all': geometry.arrow('up', cx=7, cy=8.5)+geometry.arrow('up', cx=17, cy=8.5),
        'task-retry': geometry.ring(), 'sys-refresh': geometry.ring('refresh'),
        'info-history': geometry.ring('history'),
    }
    for stem, glyph in result.items():
        if stem.startswith('task-task-') or stem in ('task-download-all', 'task-upload-all'):
            glyph += f'<path data-role="tray" d="{geometry.TRAY}"/>'
        save(stem, svg(glyph))
    for stem, glyph in geometry.circle_glyphs().items():
        save(stem, svg(geometry.FRAME+glyph))
    # Preserve the approved cloud silhouette, with narrower 45-degree arrowheads
    # to fit its opening. Only the arrow primitive changes.
    for stem, direction, cy in [('task-download', 'down', 17.1625), ('task-upload', 'up', 15.9625)]:
        root = ET.parse(ROOT / 'source/svgs' / (stem+'.svg')).getroot()
        old = root.find('.//*[@id="action-arrow"]')
        replacement = geometry.elements(geometry.arrow(direction, cy=cy, length=7.975, head=2.05, identity='action-arrow'))[0]
        replacement.attrib.update(fill='none', stroke='#444444', **{'stroke-width': '1.35', 'stroke-linecap': 'round', 'stroke-linejoin': 'round'})
        for parent in root.iter():
            if old in list(parent):
                index = list(parent).index(old)
                parent.remove(old)
                parent.insert(index, replacement)
                break
        save(stem, root)
    player = ET.parse(ROOT / 'source/svgs/play-player.svg').getroot()
    group = player.find(NS+'g')
    group.remove(list(group)[-1])
    group.extend(geometry.elements(geometry.play(cx=12, cy=9.6875, height=6)))
    save('play-player', player)
    # The insect occludes the lower-left part of the same play triangle.
    debug = ET.parse(ROOT / 'source/svgs/sys-run-debug.svg').getroot()
    height = 14*geometry.PLAY_HEIGHT/geometry.PLAY_WIDTH
    top = 11.5-height/2
    lower_end = 11.5+height/4
    path = debug.find('.//'+NS+'path')
    path.set('d', f'M7 6.5V{geometry.fmt(top)}L21 11.5L14 {geometry.fmt(lower_end)}')
    subject = debug.find('.//*[@data-role="centered-subject"]')
    # Recenter the complete composition after reducing the triangle height.
    shift_y = 12-(top-.675+20.375)/2+.00625
    subject.set('transform', f'translate(0.34375 {geometry.fmt(shift_y)})')
    subject.set('data-center-shift', f'0.34375,{geometry.fmt(shift_y)}')
    save('sys-run-debug', debug)


if __name__ == '__main__':
    build()
