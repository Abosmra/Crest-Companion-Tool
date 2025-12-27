import multiprocessing
import sys
import time
import pynput
import webbrowser
import ctypes
import msvcrt
import threading
from threading import Thread
from hacks import cayofingerprint
from hacks import casinofingerprint
from hacks import nosave
from hacks import jobwarp
from pynput import keyboard as pynput_keyboard

_shift_down = False

try:
    from updater import start_update_checker
except Exception:
    start_update_checker = None

from colorama import init as colorama_init, Fore, Style
colorama_init()

README_URL = 'https://github.com/Abosmra/Crest-Companion-Tool?tab=readme-ov-file#how-to-use-tool'


def show_readme():
    try:
        webbrowser.open(README_URL)
    except Exception:
        pass


user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def find_window(title: str):
    return user32.FindWindowW(None, title)


def get_window_rect(hwnd):
    rect = RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return (rect.left, rect.top, rect.right, rect.bottom)
    return None


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def print_banner():
    print('''
 ██████╗██████╗ ███████╗███████╗████████╗                                   
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝                                   
██║     ██████╔╝█████╗  ███████╗   ██║                                      
██║     ██╔══██╗██╔══╝  ╚════██║   ██║             Made by Abosamra         
╚██████╗██║  ██║███████╗███████║   ██║                                      
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝                                      
                                                                            
 ██████╗ ██████╗ ███╗   ███╗██████╗  █████╗ ███╗   ██╗██╗ ██████╗ ███╗   ██╗
██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔══██╗████╗  ██║██║██╔═══██╗████╗  ██║
██║     ██║   ██║██╔████╔██║██████╔╝███████║██╔██╗ ██║██║██║   ██║██╔██╗ ██║
██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══██║██║╚██╗██║██║██║   ██║██║╚██╗██║
╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║  ██║██║ ╚████║██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝''')


def ensureRunningAsAdminOrExit():
    if is_admin():
        return

    print(Fore.RED + "[!] This application must be run as Administrator." + Style.RESET_ALL)
    print("Press any key to exit...")
    try:
        msvcrt.getch()
    except Exception:
        input()
    sys.exit(1)


current_bbox = None
gta_ready = threading.Event()

def gta_monitor():
    """Continuously monitor GTA V window presence."""
    global current_bbox

    print('[*] Searching GTA V...')
    last_seen = False

    while True:
        hwnd = find_window("Grand Theft Auto V")

        if hwnd:
            if not last_seen:
                current_bbox = get_window_rect(hwnd)
                gta_ready.set()
                print('[*] GTA V Detected!')
                print('=============================================')
            last_seen = True
        else:
            if last_seen:
                gta_ready.clear()
                current_bbox = None
                print('[!] GTA V closed. Waiting for relaunch...')
                print('=============================================')
            last_seen = False

        time.sleep(1)


_cayo_running = False
_cayo_lock = threading.Lock()

_casino_running = False
_casino_lock = threading.Lock()


def _run_guarded(lock, flag_name, target, *args):
    g = globals()
    with lock:
        if g[flag_name]:
            return
        g[flag_name] = True

    def _runner():
        try:
            target(*args)
        finally:
            with lock:
                g[flag_name] = False

    Thread(target=_runner, daemon=True).start()


def _require_gta(fn):
    def wrapper():
        if not gta_ready.is_set():
            print('[!] GTA V not detected.')
            return
        fn()
    return wrapper


@_require_gta
def jobWarp():
    if _shift_down:
        return  # Shift+F5 is reserved for README

    Thread(
        target=jobwarp.main,
        args=(current_bbox,),
        daemon=True
    ).start()


@_require_gta
def cayoFingerprint():
    if _shift_down:
        return
    _run_guarded(_cayo_lock, "_cayo_running", cayofingerprint.main, current_bbox)


@_require_gta
def casinoFingerprint():
    if _shift_down:
        return
    _run_guarded(_casino_lock, "_casino_running", casinofingerprint.main, current_bbox)


@_require_gta
def noSaveToggle():
    if _shift_down:
        return
    Thread(target=nosave.toggle_firewall_rule, daemon=True).start()

def shutdown():
    if _shift_down:
        return

    try:
        nosave.delete_firewall_rule()
    except Exception:
        pass

    sys.exit(0)

def _on_press(key):
    global _shift_down
    if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r):
        _shift_down = True

def _on_release(key):
    global _shift_down
    if key in (pynput_keyboard.Key.shift, pynput_keyboard.Key.shift_l, pynput_keyboard.Key.shift_r):
        _shift_down = False

shift_listener = pynput_keyboard.Listener(
    on_press=_on_press,
    on_release=_on_release,
    daemon=True
)
shift_listener.start()

# -------------------- Main --------------------

def main():
    print_banner()
    ensureRunningAsAdminOrExit()

    # Start update checker (non-blocking)
    if start_update_checker:
        try:
            start_update_checker()
        except Exception:
            pass

    print(Fore.YELLOW + "[!] Ensure the tool window does not overlap the game window." + Style.RESET_ALL)
    print(Fore.LIGHTYELLOW_EX + '[?] How to use tool - Shift+F5' + Style.RESET_ALL)
    print('=============================================')
    print(Style.BRIGHT + '[*] Hotkeys:' + Style.RESET_ALL)
    print('    F5  - Job warp helper')
    print('    F6  - Casino fingerprint helper')
    print('    F7  - Cayo fingerprint helper')
    print('    F8  - Toggle No Save')
    print('    End - Exit')

    # Start GTA monitor thread
    Thread(target=gta_monitor, daemon=True).start()

    hotkeys = pynput.keyboard.GlobalHotKeys({
        '<shift>+<f5>': show_readme,   # always allowed
        '<f5>': jobWarp,
        '<f6>': casinoFingerprint,
        '<f7>': cayoFingerprint,
        '<f8>': noSaveToggle,
        '<end>': shutdown,             # always allowed
    })

    hotkeys.start()
    hotkeys.join()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
