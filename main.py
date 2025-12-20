import sys
import time
import pynput
import ctypes
import msvcrt
from threading import Thread
from hacks import cayofingerprint
from hacks import casinofingerprint
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


def ensureRunningAsAdminOrExit() -> None:
    # Initial startup check: if not running elevated, notify and wait for any key to exit.
    try:
        if is_admin():
            return
    except Exception:
        pass
    print("[!] This application is not running as Administrator. Please run it as Administrator.")
    print("Press any key to exit...")
    try:
        msvcrt.getch()
    except Exception:
        try:
            input()
        except Exception:
            pass
    sys.exit(1)



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
    print('    F6  - Casino fingerprint helper')
    print('    F7  - Cayo fingerprint helper')
    print('    F8  - Toggle No Save')
    print('    End - Exit')
    
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


def noSaveToggle():
    thread = Thread(target=nosave.toggle_firewall_rule)
    thread.start()
    
    
def shutdown():
    nosave.delete_firewall_rule()
    sys.exit()

 
def main():
    ensureRunningAsAdminOrExit()
    print_banner()
    printCredits()
    printHotkeys()

    bbox = checkWindow()
    if bbox:
            with pynput.keyboard.GlobalHotKeys({
            '<F6>': lambda: casinoFingerprint(bbox),
            '<F7>': lambda: cayoFingerprint(bbox),
            '<F8>': lambda: noSaveToggle(),
            '<end>': lambda: shutdown(),
              }) as h:
              h.join()

if __name__ == "__main__":
    ctypes.windll.user32.SetProcessDPIAware()
    main()
