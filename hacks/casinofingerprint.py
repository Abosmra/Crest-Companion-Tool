import cv2
import time
import keyboard
import numpy as np
from PIL import ImageGrab
from collections import deque, namedtuple

tofind = (950, 155, 1335, 685)

cell_w, cell_h = 102, 102
xs = [482, 627]
ys = [279, 423, 566, 711]


def contains(template_gray, cell_gray, threshold=0.65):
    _, score, _, _ = cv2.minMaxLoc(
        cv2.matchTemplate(template_gray, cell_gray, cv2.TM_CCOEFF_NORMED)
    )
    return score >= threshold


def find_shortest_solution(target_coordinates):
    Point = namedtuple('Point', ('x', 'y'))
    ReverseLinkedNode = namedtuple("ReverseLinkedNode", ('value', 'prev_node', 'idx'))

    rows, cols = 4, 2
    directions = [(0, 1, 's'), (1, 0, 'd'), (0, -1, 'w'), (-1, 0, 'a')]

    target_coordinates = [Point(*p) for p in target_coordinates]

    target_mask = 0
    for t in target_coordinates:
        target_mask |= 1 << (t.y * cols + t.x)

    start = Point(0, 0)
    queue = deque([(start, 1, ReverseLinkedNode(None, None, -1))])

    while queue:
        pos, visited, path = queue.popleft()

        if visited & target_mask == target_mask:
            out = [None] * (path.idx + 1)
            while path.idx >= 0:
                out[path.idx] = path.value
                path = path.prev_node
            return out + ['tab']

        for dx, dy, key in directions:
            nx = (pos.x + dx) % cols
            ny = (pos.y + dy) % rows
            npos = Point(nx, ny)

            bit = 1 << (ny * cols + nx)
            if visited & bit:
                continue

            npath = ReverseLinkedNode(key, path, path.idx + 1)
            if target_mask & bit:
                npath = ReverseLinkedNode('return', npath, npath.idx + 1)

            queue.append((npos, visited | bit, npath))

    raise RuntimeError("No solution found")


def main(bbox):
    print('[*] Casino Fingerprint')

    # Capture once
    img = ImageGrab.grab(bbox).resize((1920, 1080))
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)

    # Extract main template once
    x1, y1, x2, y2 = tofind
    template = gray[y1:y2, x1:x2]
    template = cv2.resize(template, None, fx=0.77, fy=0.77)

    # Build cell positions
    cells = [
        ((x, y, x + cell_w, y + cell_h), (col, row))
        for row, y in enumerate(ys)
        for col, x in enumerate(xs)
    ]

    togo = []
    for (x1, y1, x2, y2), pos in cells:
        cell = gray[y1:y2, x1:x2]
        if contains(template, cell):
            togo.append(pos)

    moves = find_shortest_solution(togo)

    for key in moves:
        keyboard.press(key)
        time.sleep(0.05)
        keyboard.release(key)
        time.sleep(0.05)

    print('[*] Done!')
    print('=============================================')
