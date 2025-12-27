import os
import json
import threading
import time
import re
import urllib.request

try:
    from packaging.version import parse as _parse_version
    def _is_version_newer(current, latest):
        return _parse_version(latest) > _parse_version(current)
except Exception:
    def _normalize(v):
        v = v.lstrip('vV')
        parts = re.split(r'[.\-+]', v)
        norm = []
        for p in parts:
            if p.isdigit():
                norm.append(int(p))
            else:
                m = re.match(r'(\d+)(.*)', p)
                if m:
                    norm.append(int(m.group(1)))
                    norm.append(m.group(2))
                else:
                    norm.append(p)
        return norm

    def _cmp_lists(a, b):
        for ai, bi in zip(a, b):
            if isinstance(ai, int) and isinstance(bi, int):
                if ai < bi:
                    return -1
                if ai > bi:
                    return 1
            else:
                sa, sb = str(ai), str(bi)
                if sa < sb:
                    return -1
                if sa > sb:
                    return 1
        if len(a) < len(b):
            return -1
        if len(a) > len(b):
            return 1
        return 0

    def _is_version_newer(current, latest):
        try:
            a = _normalize(current)
            b = _normalize(latest)
            return _cmp_lists(a, b) < 0
        except Exception:
            return False


CURRENT_VERSION = 'v1.3.0'
REPO_OWNER = 'Abosmra'
REPO_NAME = 'Crest-Companion-Tool'
GITHUB_LATEST_API = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest'

# State file stored in %%APPDATA%%\CrestCompanionTool\update_state.json
def _state_path():
    base = os.getenv('APPDATA') or os.path.expanduser('~')
    d = os.path.join(base, 'CrestCompanionTool')
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return os.path.join(d, 'update_state.json')


def _load_state():
    path = _state_path()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state):
    path = _state_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f)
    except Exception:
        pass


def _should_check(state):
    # Only check if no next_check set or now >= next_check
    next_check = state.get('next_check')
    if not next_check:
        return True
    try:
        next_ts = float(next_check)
        return time.time() >= next_ts
    except Exception:
        return True


def _show_dialog(current, latest, release_url, on_remind_later, on_do_not_remind):
    try:
        import tkinter as tk
        from tkinter import ttk

        # In-memory guard
        global _dialog_shown
        try:
            _dialog_shown
        except NameError:
            _dialog_shown = False
        if _dialog_shown:
            return
        _dialog_shown = True

        def _run():
            root = tk.Tk()
            root.withdraw()

            window = tk.Toplevel(root)
            window.title('Update available')
            window.attributes('-topmost', True)
            window.resizable(False, False)

            frm = ttk.Frame(window, padding=(18, 14))
            frm.grid(sticky="nsew")

            # Header
            ttk.Label(
                frm,
                text='Crest Companion update is available',
                font=('Segoe UI', 11, 'bold')
            ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 6))

            ttk.Label(frm, text=f'Current version: {current}') \
                .grid(row=1, column=0, columnspan=2, sticky='w')

            ttk.Label(frm, text=f'Latest version:  {latest}') \
                .grid(row=2, column=0, columnspan=2, sticky='w', pady=(0, 10))

            def _update_now():
                try:
                    import webbrowser
                    webbrowser.open(release_url)
                except Exception:
                    pass
                window.destroy()

            def _remind():
                try:
                    on_remind_later()
                except Exception:
                    pass
                window.destroy()

            def _do_not_remind():
                try:
                    on_do_not_remind()
                except Exception:
                    pass
                window.destroy()

            # Configure equal-width columns
            frm.columnconfigure(0, weight=1)
            frm.columnconfigure(1, weight=1)

            # Primary buttons (span evenly)
            ttk.Button(
                frm,
                text='Update now',
                command=_update_now
            ).grid(row=3, column=0, sticky='ew', padx=(0, 6))

            ttk.Button(
                frm,
                text='Remind me later',
                command=_remind
            ).grid(row=3, column=1, sticky='ew', padx=(6, 0))

            # Secondary action spans full width
            ttk.Button(
                frm,
                text='Do not remind me again for this version',
                command=_do_not_remind
            ).grid(row=4, column=0, columnspan=2, sticky='ew', pady=(8, 0))

            # Tight sizing + centering
            window.update_idletasks()
            w = window.winfo_reqwidth()
            h = window.winfo_reqheight()
            x = (window.winfo_screenwidth() // 2) - (w // 2)
            y = (window.winfo_screenheight() // 2) - (h // 2)
            window.geometry(f'{w}x{h}+{x}+{y}')

            window.mainloop()

        import threading
        threading.Thread(target=_run, daemon=True).start()

    except Exception:
        return



def _check_now():
    try:
        state = _load_state()
        # Respect next_check if user previously chose 'Remind me later'
        if not _should_check(state):
            return

        req = urllib.request.Request(GITHUB_LATEST_API, headers={'User-Agent': 'CrestCompanionUpdater/1.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read().decode('utf-8')
        j = json.loads(data)
        latest_tag = j.get('tag_name') or j.get('name')
        html_url = j.get('html_url') or f'https://github.com/{REPO_OWNER}/{REPO_NAME}/releases'
        assets = j.get('assets', []) or []

        if not latest_tag:
            # Nothing we can do
            state['last_checked'] = time.time()
            _save_state(state)
            return

        ignored = state.get('ignored_versions', []) or []
        if latest_tag in ignored:
            # user asked not to be reminded about this version
            return

        if _is_version_newer(CURRENT_VERSION, latest_tag):
            # show dialog and allow the user to choose; do not persist time-based gates

            def _remind_later():
                # Pause checks for one week from now
                try:
                    st = _load_state()
                    st['next_check'] = time.time() + 7 * 24 * 60 * 60
                    st['last_checked'] = time.time()
                    _save_state(st)
                except Exception:
                    pass

            def _do_not_remind():
                st = _load_state()
                lst = st.get('ignored_versions', [])
                if latest_tag not in lst:
                    lst.append(latest_tag)
                st['ignored_versions'] = lst
                _save_state(st)

            # Pass assets to the dialog by setting an attribute after creating a small wrapper
            try:
                _show_dialog(CURRENT_VERSION, latest_tag, html_url, _remind_later, _do_not_remind)
            except Exception:
                pass
        else:
            # up to date — do nothing
            return

    except Exception:
        # Silent on any network / parsing / other failure
        return


def start_update_checker():
    # Start a background thread to perform the (infrequent) network check.
    try:
        t = threading.Thread(target=_check_now, daemon=True)
        t.start()
    except Exception:
        pass
