import sys
import ctypes
import subprocess
import atexit
import traceback
import signal

# Simple firewall blocker helper
RULE_NAME = "fuckRockstar"
BLOCK_IP = "192.81.241.171"


def is_admin() -> bool:
    # return True when running elevated
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def ensure_admin() -> None:
    # Relaunch elevated if not admin
    if is_admin():
        return
    try:
        params = ' '.join(f'"{a}"' if ' ' in a else a for a in sys.argv)
        res = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        if int(res) <= 32:
            print(f"[!] Elevation failed (ShellExecuteW returned {res}). Cmd: {sys.executable} {params}")
    except Exception as e:
        print(f"[!] Elevation attempt raised: {e}. Cmd: {sys.executable} {sys.argv}")
    sys.exit(0)


def _elevate_netsh(args: str) -> None:
    # Run netsh with elevation via ShellExecuteW
    ctypes.windll.shell32.ShellExecuteW(None, "runas", "netsh", args, None, 1)


def add_firewall_rule() -> None:
    # Add outbound block rule for BLOCK_IP
    try:
        cmd_args = (
            f"advfirewall firewall add rule name={RULE_NAME} "
            f"dir=out action=block remoteip={BLOCK_IP}"
        )
        if is_admin():
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
        else:
            _elevate_netsh(cmd_args)
            print("[*] Firewall add command invoked (elevation may be required)")
    except Exception as e:
        print(f"[!] add_firewall_rule error: {e}")
        print(traceback.format_exc())


def delete_firewall_rule(elevate: bool = True) -> None:
    # Remove the named firewall rule. Pass elevate=False to avoid UAC on exit.
    try:
        cmd_args = f"advfirewall firewall delete rule name={RULE_NAME}"
        if is_admin():
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
            print('=============================================')

        else:
            if elevate:
                _elevate_netsh(cmd_args)
                print("[*] Firewall delete command invoked (elevation may be required)")
            else:
                print("[!] Not running as admin: cannot remove firewall rule without elevation")
    except Exception as e:
        print(f"[!] delete_firewall_rule error: {e}")
        print(traceback.format_exc())


def init() -> None:
    # Ensure elevated and register best-effort cleanup handlers
    try:
        ensure_admin()
        atexit.register(lambda: delete_firewall_rule(elevate=False))

        def _cleanup_and_exit(signum, frame):
            try:
                delete_firewall_rule(elevate=False)
            except Exception:
                pass
            sys.exit(0)

        try:
            signal.signal(signal.SIGINT, _cleanup_and_exit)
        except Exception:
            pass
        try:
            signal.signal(signal.SIGTERM, _cleanup_and_exit)
        except Exception:
            pass
        if hasattr(signal, 'SIGBREAK'):
            try:
                signal.signal(signal.SIGBREAK, _cleanup_and_exit)
            except Exception:
                pass

    except Exception as e:
        print(f"[!] nosave.init error: {e}")
        print(traceback.format_exc())


def toggle_firewall_rule() -> None:
    # Toggle the block rule on/off; elevate when needed
    try:
        if is_admin():
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
        else:
            cmd = (
                f'netsh advfirewall firewall show rule name={RULE_NAME} >nul 2>&1 && '
                f'netsh advfirewall firewall delete rule name={RULE_NAME} || '
                f'netsh advfirewall firewall add rule name={RULE_NAME} dir=out action=block remoteip={BLOCK_IP}'
            )
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f"/c {cmd}", None, 1)
            print("[*] Toggle command invoked (elevation may be required)")
    except Exception as e:
        print(f"[!] toggle_firewall_rule error: {e}")
        print(traceback.format_exc())
