import cv2
import time
import keyboard
import numpy as np
from PIL import ImageGrab

# Target templates (fixed)
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

# Scan positions
scan = [(424, 360 + 76 * i, 810, 415 + 76 * i) for i in range(8)]


def best_match_index(part, templates, threshold=0.65):
    """Return best template index or -1 if below threshold."""
    best_idx = -1
    best_score = threshold

    for i, tpl in enumerate(templates):
        _, score, _, _ = cv2.minMaxLoc(
            cv2.matchTemplate(tpl, part, cv2.TM_CCOEFF_NORMED)
        )
        if score > best_score:
            best_score = score
            best_idx = i

    return best_idx


def main(bbox):
    print('[*] Cayo Fingerprint')

    # Capture once
    img = ImageGrab.grab(bbox).resize((1920, 1080))
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

    # Precompute templates (resize once)
    templates = []
    for x1, y1, x2, y2 in targets:
        part = gray[y1:y2, x1:x2]
        part = cv2.resize(part, None, fx=0.91, fy=0.91)
        templates.append(part)

    # Precompute scan regions
    scans = [
        gray[y1:y2, x1:x2]
        for (x1, y1, x2, y2) in scan
    ]

    moves = []

    for i, scan_img in enumerate(scans):
        j = best_match_index(scan_img, templates)
        if j == -1:
            continue

        # shortest rotation path
        diff = i - j
        path = min(diff, diff - 8, diff + 8, key=abs)

        if path:
            key = 'd' if path > 0 else 'a'
            moves.extend([key] * abs(path))

        moves.append('s')

    # Remove trailing confirm
    if moves and moves[-1] == 's':
        moves.pop()

    # Execute inputs (timing preserved)
    for key in moves:
        keyboard.press(key)
        time.sleep(0.05)
        keyboard.release(key)
        time.sleep(0.05)

    print('[*] Done!')
    print('=============================================')
