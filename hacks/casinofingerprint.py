import cv2
import time
import keyboard
import numpy as np
from PIL import Image, ImageGrab
from collections import deque, namedtuple

tofind = (950, 155, 1335, 685)

cell_w, cell_h = 102, 102
xs = [482, 627]
ys = [279, 423, 566, 711]

def is_in(img, subimg):
    template = cv2.cvtColor(np.array(subimg), cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.65
    loc = np.where(res >= threshold)
    for _ in zip(*loc[::-1]):
        return True
    return False

def find_shortest_solution(target_coordinates):
    Point = namedtuple('Point', ('x', 'y'))
    ReverseLinkedNode = namedtuple("ReverseLinkedNode", ('value', 'prev_node', 'idx'))
    rows, cols = 4, 2
    directions = [(0, 1, 's'), (1, 0, 'd'), (0, -1, 'w'), (-1, 0, 'a')]  

    target_coordinates = [p if isinstance(p, Point) else Point(*p) for p in target_coordinates]
    target_mask = 0
    for target in target_coordinates:
        target_mask |= 1 << ((target.y * cols) + target.x)

    current_pos = Point(0, 0)
    visited_mask = 1
    path_head: ReverseLinkedNode = ReverseLinkedNode(None, None, -1)
    if current_pos in target_coordinates:
        path_head = ReverseLinkedNode('return', path_head, 0)
    queue = deque([(current_pos, visited_mask, path_head)]) 

    while len(queue) > 0:
        current_pos, visited_mask, path_head = queue.popleft()

        if visited_mask & target_mask == target_mask:
            output_list = [None] * (path_head.idx + 1)
            while path_head.idx >= 0:
                output_list[path_head.idx] = path_head.value
                path_head = path_head.prev_node
            return output_list + ['tab']

        for delta_x, delta_y, key in directions:
            new_x, new_y = current_pos.x + delta_x, current_pos.y + delta_y
            if new_x == -1:
                new_x, new_y = cols-1, new_y-1
            elif new_x == cols:
                new_x, new_y = 0, new_y+1
            new_y = new_y % rows

            next_pos = Point(new_x, new_y)
            pos_mask = 1 << ((next_pos.y * cols) + next_pos.x)
            next_visited_mask = visited_mask | pos_mask
            if visited_mask == next_visited_mask:
                continue

            next_path_head = ReverseLinkedNode(key, path_head, path_head.idx+1)
            if target_mask & pos_mask != 0:
                next_path_head = ReverseLinkedNode('return', next_path_head, next_path_head.idx+1)
            queue.append((next_pos, next_visited_mask, next_path_head))

    raise Exception('No solution found')

def main(bbox):
    print('[*] Casino Fingerprint')
    im = ImageGrab.grab(bbox)
    im = im.resize((1920,1080))
    sub0_ = im.crop(tofind)
    sub0 = cv2.cvtColor(
        np.array(sub0_.resize((round(sub0_.size[0] * 0.77), round(sub0_.size[1] * 0.77)))),
        cv2.COLOR_BGR2GRAY,
    )

    parts = [
        ((x, y, x + cell_w, y + cell_h), (col, row))
        for row, y in enumerate(ys)
        for col, x in enumerate(xs)
    ]

    togo = [part[1] for part in parts if is_in(sub0, im.crop(part[0]))]

    sub0_.close()
    im.close()

    moves = find_shortest_solution(togo)
    for key in moves:
            keyboard.press(key)
            time.sleep(0.05)
            keyboard.release(key)
            time.sleep(0.05)
    print('[*] Done!')
    print('=============================================')
