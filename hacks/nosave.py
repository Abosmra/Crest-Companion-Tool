import sys
import subprocess
import atexit
import traceback
import signal
import os
from pathlib import Path

# Simple firewall blocker helper
RULE_NAME = "fuckRockstar"
BLOCK_IP = "192.81.241.171"


def add_firewall_rule() -> None:
    # Add outbound block rule for BLOCK_IP
    try:
        cmd_args = (
            f"advfirewall firewall add rule name={RULE_NAME} "
            f"dir=out action=block remoteip={BLOCK_IP}"
        )
        subprocess.run(
            [
                "netsh",
                "advfirewall",
                "firewall",
                "add",
                "rule",
                f"name={RULE_NAME}",
                "dir=out",
                "action=block",
                f"remoteip={BLOCK_IP}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"[*] No Save ON")
        try:
            play_sound('ON.wav')
        except Exception:
            pass
    except Exception as e:
        print(f"[!] add_firewall_rule error: {e}")
        print(traceback.format_exc())


def delete_firewall_rule() -> None:
    # Remove the named firewall rule
    try:
        cmd_args = f"advfirewall firewall delete rule name={RULE_NAME}"
        subprocess.run(
            [
                "netsh",
                "advfirewall",
                "firewall",
                "delete",
                "rule",
                f"name={RULE_NAME}",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("[*] No Save OFF")
        try:
            play_sound('OFF.wav')
        except Exception:
            pass
        print('=============================================')
    except Exception as e:
        print(f"[!] delete_firewall_rule error: {e}")
        print(traceback.format_exc())


def toggle_firewall_rule() -> None:
    # Toggle the block rule on/off
    try:
        p = subprocess.run(
            [
                "netsh",
                "advfirewall",
                "firewall",
                "show",
                "rule",
                f"name={RULE_NAME}",
            ],
            capture_output=True,
            text=True,
        )
        out = (p.stdout or "") + (p.stderr or "")
        if "No rules match" in out or "No rules match the specified criteria" in out:
            add_firewall_rule()
        else:
            delete_firewall_rule()
    except Exception as e:
        print(f"[!] toggle_firewall_rule error: {e}")
        print(traceback.format_exc())


def play_sound(filename: str) -> None:

    # Support running from source and from a PyInstaller onefile bundle.
    base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    sound_path = base_dir / 'assets' / filename
    if not sound_path.exists():
        return

    if os.name != 'nt':
        return

    try:
        import winsound
        winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        return
