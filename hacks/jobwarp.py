import keyboard
import time
import threading

def tap_key(key, hold_time=0.05, gap_time=0.05):
    keyboard.press(key)
    time.sleep(hold_time)
    keyboard.release(key)
    time.sleep(gap_time)

def countdown(seconds, abort_event):
    for remaining in range(seconds, 0, -1):
        if abort_event.is_set():
            return True  # aborted
        print(
            f'\r[*] Job Warp Started. Press ESC to abort. Time left: {remaining:02d}s',
            end='',
            flush=True
        )
        time.sleep(1)
    print()  # move to next line after countdown finishes
    return False


def main(bbox=None):
    abort_event = threading.Event()
    hotkey_id = keyboard.add_hotkey('esc', lambda: abort_event.set())
    try:
        tap_key('space')
        tap_key('enter')

        keyboard.press('alt')
        time.sleep(0.05)
        tap_key('f4')
        keyboard.release('alt')
        time.sleep(0.05)

        if countdown(35, abort_event):
            print('\n[*] Job Warp cancelled')
            print('=============================================')
            return

        tap_key('esc')
        print('[*] Job Warp successful!')
        print('=============================================')

    finally:
        try:
            keyboard.remove_hotkey(hotkey_id)
        except Exception:
            pass
