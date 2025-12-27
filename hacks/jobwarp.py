import keyboard
import time
import threading
from hacks import overlay

_run_lock = threading.Lock()
_abort_event = None
_running = False


def _safe_overlay(fn):
    try:
        fn()
    except Exception:
        pass


def tap_key(key, hold_time=0.05, gap_time=0.05):
    keyboard.press(key)
    time.sleep(hold_time)
    keyboard.release(key)
    time.sleep(gap_time)


def tap_combo(keys, hold_time=0.05, gap_time=0.05):
    for k in keys:
        keyboard.press(k)
    time.sleep(hold_time)
    for k in reversed(keys):
        keyboard.release(k)
    time.sleep(gap_time)


def main(bbox=None):
    global _abort_event, _running

    with _run_lock:
        # TOGGLE BEHAVIOR
        if _running:
            if _abort_event and not _abort_event.is_set():
                _abort_event.set()
            return

        # Start fresh run
        _running = True
        _abort_event = threading.Event()
        abort_event = _abort_event

    try:
        _safe_overlay(overlay.jobwarpstarting)

        tap_key('space')
        tap_key('enter')
        tap_combo(['alt', 'f4'])

        # Cancel-aware wait
        if abort_event.wait(timeout=40.0):
            tap_key('esc')
            _safe_overlay(overlay.jobwarpcancelling)
            return

        tap_key('esc')
        _safe_overlay(overlay.jobwarpdone)

    finally:
        with _run_lock:
            _running = False
            if _abort_event is abort_event:
                _abort_event = None
