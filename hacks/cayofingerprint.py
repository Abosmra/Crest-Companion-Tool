import cv2
import time
import keyboard
import numpy as np
from PIL import ImageGrab

targets = [
    (907, y1, 1562, y2)
    for y1, y2 in [
        (331, 431),
        (404, 504),
        (500, 600),
        (560, 660),
        (627, 727),
        (697, 809),
        (780, 883),
        (863, 975),
    ]
]


scan = [(424, 360 + 76 * i, 810, 415 + 76 * i) for i in range(8)]


def index(part, parts):
    """Return the index of 'part' in 'parts', return -1 if not found"""
    for i in range(len(parts)):
        res = cv2.matchTemplate(parts[i], part, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= 0.65)
        for pt in zip(*loc[::-1]):
            return i
    return -1

def main(bbox):
    print('[*] Cayo Fingerprint')
    im = ImageGrab.grab(bbox)
    im = im.resize((1920, 1080))

    parts = []
    for target in targets:
            part = im.crop(target)
            parts.append(cv2.cvtColor(np.array(part.resize((round(part.size[0] * 0.91), round(part.size[1] * 0.91)))), cv2.COLOR_RGB2GRAY))

    moves = []
    for i in range(len(scan)):
        j = index(cv2.cvtColor(np.array(im.crop(scan[i])), cv2.COLOR_RGB2GRAY), parts)

        if j == -1:
                continue

        path = min(i - j, i - j - 8, i - j + 8, key = abs)
        if path != 0:
            key = "d" if path > 0 else "a"
            for _ in range(abs(path)):
                moves.append(key)

        moves.append("s")

    while moves and moves[-1] == "s":
            del moves[-1]

    for key in moves:
            keyboard.press(key)
            time.sleep(0.05)
            keyboard.release(key)
            time.sleep(0.05)
    print('[*] Done!')
    print('=============================================')
