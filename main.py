import sys
import time
import pynput
import ctypes
from threading import Thread
from hacks import cayofingerprint
from hacks import casinofingerprint
from hacks import casinokeypad
from hacks import nosave


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
    ok = user32.GetWindowRect(hwnd, ctypes.byref(rect))
    if ok:
        return (rect.left, rect.top, rect.right, rect.bottom)
    return None


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def ensure_elevated_console():
    if is_admin() or "--elevated" in sys.argv:
        return
    script = sys.argv[0]
    args = " ".join(a for a in sys.argv[1:] if a != "--elevated")
    params = f'"{script}" --elevated {args}'.strip()
    try:
        res = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        if int(res) <= 32:
            print(f"[!] Elevation failed (ShellExecuteW returned {res}). Command: {sys.executable} {params}")
    except Exception as e:
        print(f"[!] Elevation attempt raised: {e}. Cmd: {sys.executable} {params}")
    sys.exit(0)

 

def print_banner():
    print('''
          
  ██████╗██████╗ ███████╗███████╗████████╗                                  
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝                                   
██║     ██████╔╝█████╗  ███████╗   ██║                                      
██║     ██╔══██╗██╔══╝  ╚════██║   ██║                                      
╚██████╗██║  ██║███████╗███████║   ██║                                      
 ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝                                      
                                                                            
 ██████╗ ██████╗ ███╗   ███╗██████╗  █████╗ ███╗   ██╗██╗ ██████╗ ███╗   ██╗
██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔══██╗████╗  ██║██║██╔═══██╗████╗  ██║
██║     ██║   ██║██╔████╔██║██████╔╝███████║██╔██╗ ██║██║██║   ██║██╔██╗ ██║
██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══██║██║╚██╗██║██║██║   ██║██║╚██╗██║
╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║  ██║██║ ╚████║██║╚██████╔╝██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                            ''')

def printCredits():
    print('''
Made by Abosamra 
    ''')
    
def printHotkeys():
    print('[*] Hotkeys:')
    print('    F5  - Casino keypad helper')
    print('    F6  - Casino fingerprint helper')
    print('    F7  - Cayo fingerprint helper')
    print('    F8  - Toggle Block/Unblock IP (no-save)')
    print('    End - Exit')
#    print('    PgDn - not implemented yet')
    
def checkWindow():
    print('[*] Searching GTA V...')

    while True:
        hwnd = find_window("Grand Theft Auto V")
        
        if hwnd:
            print('[*] GTA V Detected!')
            print('=============================================')
            return get_window_rect(hwnd)
        
        time.sleep(1)

def cayoFingerprint(bbox):
    thread = Thread(target=cayofingerprint.main, args=(bbox,))
    thread.start()

def casinoFingerprint(bbox):
    thread = Thread(target=casinofingerprint.main, args=(bbox,))
    thread.start()
    
def casinoKeypad(bbox):
    thread = Thread(target=casinokeypad.main, args=(bbox,))
    thread.start()

def shutdown():
    sys.exit()

 

def main():
    ensure_elevated_console()
    nosave.init()
    print_banner()
    printCredits()
    printHotkeys()

    bbox = checkWindow()
    if bbox:
        with pynput.keyboard.GlobalHotKeys({
            '<F5>': lambda: casinoKeypad(bbox),
            '<F6>': lambda: casinoFingerprint(bbox),
            '<F7>': lambda: cayoFingerprint(bbox),
            '<F8>': lambda: nosave.toggle_firewall_rule(),
            '<end>': lambda: shutdown(),
            #'<page_down>': lambda: notImplemented(),
              }) as h:
            
            h.join()

if __name__ == "__main__":
    ctypes.windll.user32.SetProcessDPIAware()
    main()
