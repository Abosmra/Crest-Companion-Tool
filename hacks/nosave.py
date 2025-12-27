import sys
import subprocess
import os
from pathlib import Path
from colorama import Fore, Style

try:
    from . import overlay
except Exception:
    overlay = None

RULE_NAME = "fuckRockstar"
BLOCK_IP = "192.81.241.171"

_firewall_enabled = False  # in-process state


def _run_netsh(args):
    subprocess.run(
        ["netsh", "advfirewall", "firewall"] + args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _safe_overlay(fn):
    try:
        fn()
    except Exception:
        pass


def add_firewall_rule():
    global _firewall_enabled

    _run_netsh([
        "add", "rule",
        f"name={RULE_NAME}",
        "dir=out",
        "action=block",
        f"remoteip={BLOCK_IP}",
    ])

    _firewall_enabled = True
    print(f"[*] No Save {Fore.LIGHTGREEN_EX}ON{Style.RESET_ALL}")

    if overlay:
        _safe_overlay(overlay.show_on)

    _safe_overlay(lambda: play_sound("ON.wav"))


def delete_firewall_rule():
    global _firewall_enabled

    _run_netsh([
        "delete", "rule",
        f"name={RULE_NAME}",
    ])

    _firewall_enabled = False
    print(f"[*] No Save {Fore.LIGHTRED_EX}OFF{Style.RESET_ALL}")

    if overlay:
        _safe_overlay(overlay.show_off)

    _safe_overlay(lambda: play_sound("OFF.wav"))
    print('=============================================')


def toggle_firewall_rule():
    if _firewall_enabled:
        delete_firewall_rule()
    else:
        add_firewall_rule()


def play_sound(filename: str):
    if os.name != 'nt':
        return

    base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    sound_path = base_dir / 'assets' / filename
    if not sound_path.exists():
        return

    try:
        import winsound
        winsound.PlaySound(
            str(sound_path),
            winsound.SND_FILENAME | winsound.SND_ASYNC
        )
    except Exception:
        pass
