"""Shared control glyphs. Sizes vary by context; geometry and stroke do not drift."""

import xml.etree.ElementTree as ET

NS = '{http://www.w3.org/2000/svg}'
STROKE = 1.35
TRAY = 'M2.9 15.3v3.85q0 .6.6.6h17q.6 0 .6-.6V15.3'
FRAME = '<circle data-role="frame" cx="12" cy="12" r="9.3125"/>'
PLAY_WIDTH = 8.904
PLAY_HEIGHT = 8.916
COMPACT_HEIGHT = 9
PAUSE_GAP = 11*COMPACT_HEIGHT/16
ARROW_LENGTH = COMPACT_HEIGHT
ARROW_HEAD = ARROW_LENGTH*3/7
RING_HEAD_SCALE = 1.1
COMPACT_RING_HEAD_SCALE = 1.5


def fmt(value):
    return f'{value:.9f}'.rstrip('0').rstrip('.')


def play(cx=12, cy=12, height=COMPACT_HEIGHT, optical=True):
    width = height*PLAY_WIDTH/PLAY_HEIGHT
    left = cx-width/(3 if optical else 2)
    right = left+width
    return f'<path d="M{fmt(left)} {fmt(cy-height/2)}v{fmt(height)}L{fmt(right)} {fmt(cy)}Z"/>'


def pause(cx=12, cy=12, height=ARROW_LENGTH, gap=PAUSE_GAP):
    left, right = cx-gap/2, cx+gap/2
    return f'<path d="M{fmt(left)} {fmt(cy-height/2)}v{fmt(height)}M{fmt(right)} {fmt(cy+height/2)}v-{fmt(height)}"/>'


def stop(cx=12, cy=12, size=COMPACT_HEIGHT):
    return f'<rect x="{fmt(cx-size/2)}" y="{fmt(cy-size/2)}" width="{fmt(size)}" height="{fmt(size)}" rx="0.6"/>'


def arrow(direction, cx=12, cy=12, length=ARROW_LENGTH, head=ARROW_HEAD, identity=None):
    tip = cy-length/2 if direction == 'up' else cy+length/2
    tail = cy+length/2 if direction == 'up' else cy-length/2
    wing = tip+head if direction == 'up' else tip-head
    attribute = f' id="{identity}"' if identity else ''
    return (f'<path{attribute} d="M{fmt(cx)} {fmt(tail)}V{fmt(tip)}'
            f'M{fmt(cx-head)} {fmt(wing)}L{fmt(cx)} {fmt(tip)}L{fmt(cx+head)} {fmt(wing)}"/>')


def ring(kind='retry', cx=12, cy=12, compact=False):
    # Keep the same head construction, with extra small-size compensation.
    # Compact resume has a larger semantic opening than standalone retry.
    scale = COMPACT_HEIGHT/270 if compact else 1/16
    dx = cx-192*scale
    dy = cy-192*scale
    stroke = (1.35 if compact else 1.375)/scale
    start = '317.1 242.1' if compact else '325.686 210.288'
    sweep = 'M58.314 173.712A135 135 0 0 1 324.949 168.057' if kind == 'refresh' else f'M{start}A135 135 0 1 1 324.949 168.057'
    head_scale = COMPACT_RING_HEAD_SCALE if compact else RING_HEAD_SCALE
    head = f'M339 {fmt(169-60*head_scale)}V169H{fmt(339-59*head_scale)}'
    pair = f'<path d="{sweep}"/><path d="{head}" stroke-linecap="butt" stroke-linejoin="miter"/>'
    if kind == 'refresh':
        pair += f'<g transform="rotate(180 192 192)">{pair}</g>'
    elif kind == 'history':
        pair = f'<g transform="translate(384 0) scale(-1 1)">{pair}</g><path d="M192 102.4V192l88 56" stroke-width="21.6"/>'
    return f'<g transform="translate({fmt(dx)} {fmt(dy)}) scale({fmt(scale)})" stroke-width="{fmt(stroke)}">{pair}</g>'


def circle_glyphs():
    return {
        'play-start-circle': play(), 'play-pause-circle': pause(),
        'play-stop-circle': stop(), 'task-retry-circle': ring(cy=12, compact=True),
        'view-arrow-up-circle': arrow('up'), 'view-arrow-down-circle': arrow('down'),
    }


def elements(markup):
    return list(ET.fromstring('<g xmlns="http://www.w3.org/2000/svg">'+markup+'</g>'))
