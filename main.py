import multiprocessing
import sys
import time
import pynput
import webbrowser
import ctypes
import msvcrt
from threading import Thread
from hacks import cayofingerprint
from hacks import casinofingerprint
from hacks import nosave
from colorama import init as colorama_init, Fore, Style
colorama_init()

README_URL = 'https://github.com/Abosmra/Crest-Companion-Tool?tab=readme-ov-file#how-to-use-the-fingerprint-helpers'

def show_readme() -> None:
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
    try:
        if is_admin():
            return
    except Exception:
        pass
    print(Fore.RED + "[!] This application is not running as Administrator. Please run it as Administrator." + Style.RESET_ALL)
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

def print_fingerprint_visibility_notice():
    notice = "[INFO] When running, make sure the tool's terminal window does not cover or overlap the game window.\n"
    print(Fore.YELLOW + notice + Style.RESET_ALL)
    
def printHotkeys():
    print(Style.BRIGHT + '[*] Hotkeys:' + Style.RESET_ALL)
    print('    ' + Fore.LIGHTYELLOW_EX + '[?] How to use tool - Shift+F5' + Style.RESET_ALL)
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


def get_current_bbox():
    hwnd = find_window("Grand Theft Auto V")
    if hwnd:
        return get_window_rect(hwnd)
    return None

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
    print_fingerprint_visibility_notice()
    printHotkeys()

    hotkeys = pynput.keyboard.GlobalHotKeys({
        '<F6>': lambda: (lambda b: casinoFingerprint(b) if b else print('[!] GTA V not found.'))(get_current_bbox()),
        '<F7>': lambda: (lambda b: cayoFingerprint(b) if b else print('[!] GTA V not found.'))(get_current_bbox()),
        '<shift>+<f5>': lambda: show_readme(),
        '<F8>': lambda: noSaveToggle(),
        '<end>': lambda: shutdown(),
    })

    hotkeys.start()

    try:
        bbox = checkWindow()
        hotkeys.join()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
