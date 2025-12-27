import sys
import ctypes
import multiprocessing
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPainterPath, QTextDocument


# Win32 constants
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x20
WS_EX_NOACTIVATE = 0x08000000

# ---------------------------------------------------------------------------
# UI Constants
# ---------------------------------------------------------------------------

ANIM_SLIDE_MS = 180
ANIM_WIDTH_MS = 160
POLL_INTERVAL_MS = 40
AUTO_HIDE_MS = 3000

COLOR_GREEN = QColor(60, 160, 90)
COLOR_RED = QColor(180, 70, 70)
COLOR_BLUE = QColor(80, 140, 220)
COLOR_NEUTRAL = QColor(120, 120, 120)

# Banner is top-left anchored (fixed); positioning is centralized in _update_positions.


class Banner(QWidget):
    """HUD banner widget"""

    def __init__(self, screen_geom, width=130, height=48, margin=12, anim_ms=ANIM_SLIDE_MS):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus)

        self._w = width
        self._h = height
        self.margin = margin
        self.anim_ms = anim_ms
        # visual state is now driven by timers only; no boolean flag required
        self._accent_color = QColor(60, 160, 90)

        self.resize(width, height)
        self.screen_geom = screen_geom
        # positions are computed via _update_positions() after geometry setup

        # Label
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.label.setFont(QFont("Segoe UI", 12))
        self.label.setStyleSheet("color: rgba(255,255,255,230); padding-left: 0px;")

        # Reusable QTextDocument to avoid allocating one per measurement
        self._text_doc = QTextDocument()
        self._text_doc.setDefaultFont(self.label.font())

        # Anim
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setDuration(anim_ms)

        # Width animation (smoothly animate width changes)
        self._width_anim = QPropertyAnimation(self, b"minimumWidth")
        self._width_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._width_anim.setDuration(ANIM_WIDTH_MS)
        # Track connected slots to avoid noisy try/except disconnects
        self._width_anim_value_slot = None
        self._width_anim_finished_slot = None
        self._animation_finished_slot = None

        # Timer for auto-hide on OFF
        self._off_timer = QTimer()
        self._off_timer.setSingleShot(True)
        self._off_timer.timeout.connect(self.slide_out)

        # Delayed setup
        QTimer.singleShot(0, self._setup_clickthrough)
        QTimer.singleShot(0, self._setup_blur)

        # Precompute geometry
        self._update_geometry()
        # compute onscreen/offscreen positions for the configured anchor
        self._update_positions()
        # start offscreen
        self.move(self.offscreen_pos)

    # -----------------------------------------------------------------------
    # Setup
    # -----------------------------------------------------------------------

    def _setup_clickthrough(self):
        hwnd = int(self.winId())
        user32 = ctypes.windll.user32

        cur = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        new = cur | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new)

        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x2
        SWP_NOSIZE = 0x1
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE)

    def _setup_blur(self):
        hwnd = int(self.winId())
        try:
            class ACCENT_POLICY(ctypes.Structure):
                _fields_ = [
                    ("AccentState", ctypes.c_int),
                    ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_int),
                    ("AnimationId", ctypes.c_int),
                ]

            class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
                _fields_ = [
                    ("Attribute", ctypes.c_int),
                    ("Data", ctypes.c_void_p),
                    ("SizeOfData", ctypes.c_size_t),
                ]

            ACCENT_ENABLE_ACRYLIC = 4
            SetWCA = getattr(ctypes.windll.user32, "SetWindowCompositionAttribute", None)
            if not SetWCA:
                return

            policy = ACCENT_POLICY()
            policy.AccentState = ACCENT_ENABLE_ACRYLIC
            policy.AccentFlags = 2
            policy.GradientColor = (180 << 24) | (16 << 16) | (16 << 8) | 16

            data = WINDOWCOMPOSITIONATTRIBDATA()
            data.Attribute = 19
            data.Data = ctypes.byref(policy)
            data.SizeOfData = ctypes.sizeof(policy)

            SetWCA(hwnd, ctypes.byref(data))

        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Geometry cache
    # -----------------------------------------------------------------------

    def _update_geometry(self):
        padding, pill_height, accent_w = self._layout_metrics()

        self._padding = padding
        self._pill_height = pill_height
        self._pill_width = accent_w
        self._pill_radius = accent_w / 2.0

        self._pill_rect = QRectF(float(padding), float(padding), float(accent_w), float(pill_height))

        label_start = padding + accent_w + padding
        self._label_rect = (label_start, 0, self._w - label_start - padding, self._h)

        self._card_radius = int(self._h * 0.36)
        self._card_rect = QRectF(self.rect())

    def _compute_effective_width(self, text: str) -> int:
        """Compute desired width for `text`, then clamp to available screen width.

        This centralizes the padding/pill/text math and ensures a single clamped width
        is used by callers before updating positions or starting animations.
        """
        label_w = int(self._measure_text_width(text))
        padding, pill_height, accent_w = self._layout_metrics()

        desired_w = padding + accent_w + padding + label_w + padding

        # enforce reasonable min/max and available screen space
        min_w = 130
        max_w = min(int(self.screen_geom.width() * 0.5), 800)
        # available horizontal space (respect margins)
        available_w = int(self.screen_geom.width() - 2 * self.margin)
        max_w = min(max_w, available_w)

        return int(max(min_w, min(desired_w, max_w)))

    def _prepare_geometry_for_text(self, text: str) -> int:
        """Compute final clamped width for `text` and update positions.

        Returns the computed width. This centralizes width clamping and ensures
        positions (onscreen/offscreen) are computed from the final width.
        """
        new_w = self._compute_effective_width(text)
        self._update_positions(new_w)
        return int(new_w)

    def _measure_text_width(self, html_text: str) -> float:
        # Reuse a single QTextDocument instance to reduce allocations
        doc = self._text_doc
        doc.setDefaultFont(self.label.font())
        doc.setHtml(html_text)
        # idealWidth gives the natural width for the content
        try:
            w = doc.idealWidth()
        except Exception:
            w = doc.size().width()
        return float(w)

    def _layout_metrics(self):
        """Return (padding, pill_height, accent_w) for current height/width."""
        padding = max(8, int(self._h * 0.12))
        pill_height = max(8, self._h - 2 * padding)
        accent_w = min(max(10, int(pill_height * 0.28)), int(self._w * 0.18))
        if accent_w > pill_height:
            accent_w = pill_height
        return padding, pill_height, accent_w

    def _apply_width(self, new_width: int):
        if new_width == self.width():
            return

        # animate width change smoothly
        self._width_anim.stop()
        self._width_anim.setStartValue(self.width())
        self._width_anim.setEndValue(new_width)

        # Update positions deterministically for the clamped width.
        self._update_positions(new_width)

        # Helper to compute label rect for an arbitrary width without allocating
        def _compute_label_rect_for_width(w: int):
            padding = max(8, int(self._h * 0.12))
            pill_height = max(8, self._h - 2 * padding)
            accent_w = min(max(10, int(pill_height * 0.28)), int(w * 0.18))
            if accent_w > pill_height:
                accent_w = pill_height
            label_start = padding + accent_w + padding
            return (label_start, 0, max(0, w - label_start - padding), self._h)

        # Disconnect previous value/finished slots if present (cheap guard checks)
        if self._width_anim_value_slot is not None:
            try:
                self._width_anim.valueChanged.disconnect(self._width_anim_value_slot)
            except Exception:
                pass
            self._width_anim_value_slot = None

        if self._width_anim_finished_slot is not None:
            try:
                self._width_anim.finished.disconnect(self._width_anim_finished_slot)
            except Exception:
                pass
            self._width_anim_finished_slot = None

        # Per-frame width update: minimal arithmetic, no allocations
        def _on_width_changed(value):
            try:
                value = int(value)
            except Exception:
                value = new_width

            if value == self._w:
                return

            self._w = value
            # follow minimumWidth during animation
            self.setMinimumWidth(self._w)
            # update label geometry cheaply
            self.label.setGeometry(*_compute_label_rect_for_width(self._w))

        # Finalize geometry exactly once at animation end
        def _on_width_anim_finished():
            try:
                end_w = int(self._width_anim.endValue())
            except Exception:
                end_w = int(new_width)

            self._w = end_w
            self.setMinimumWidth(end_w)
            self.resize(end_w, self._h)
            self._update_geometry()
            self.label.setGeometry(*self._label_rect)

            # clear stored slot refs so future connects are consistent
            self._width_anim_value_slot = None
            self._width_anim_finished_slot = None

        # store references so disconnect can be explicit and cheap
        self._width_anim_value_slot = _on_width_changed
        self._width_anim_finished_slot = _on_width_anim_finished

        self._width_anim.valueChanged.connect(self._width_anim_value_slot)
        self._width_anim.finished.connect(self._width_anim_finished_slot)
        self._width_anim.start()


    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Card background
        card_path = QPainterPath()
        card_path.addRoundedRect(self._card_rect, self._card_radius, self._card_radius)
        p.fillPath(card_path, QColor(16, 16, 16, 140))

        # Subtle outline
        p.setPen(QColor(255, 255, 255, 18))
        p.drawPath(card_path)

        # Pill
        pill_path = QPainterPath()
        pill_path.addRoundedRect(self._pill_rect, self._pill_radius, self._pill_radius)
        p.fillPath(pill_path, QBrush(self._accent_color))

    def resizeEvent(self, event):
        self._update_geometry()
        self.label.setGeometry(*self._label_rect)
        super().resizeEvent(event)

    def slide_in(self):
        self._cancel_animation()

        start_pos = self.pos()

        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(self.onscreen_pos)

        self.show()
        self.animation.start()

    def slide_out(self):
        self._cancel_animation()

        start_pos = self.pos()
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(self.offscreen_pos)

        # Ensure we don't accumulate multiple connections to finished
        if self._animation_finished_slot is not None:
            try:
                self.animation.finished.disconnect(self._animation_finished_slot)
            except Exception:
                pass

        self._animation_finished_slot = self.hide
        self.animation.finished.connect(self._animation_finished_slot)
        self.animation.start()

    def _cancel_animation(self):
        # Stop current animation and disconnect its finished signal if connected
        self.animation.stop()
        if self._animation_finished_slot is not None:
            try:
                self.animation.finished.disconnect(self._animation_finished_slot)
            except Exception:
                pass
            self._animation_finished_slot = None

    def _update_positions(self, width: int = None):

        w = self._w if width is None else int(width)
        # enforce available horizontal space so banner never extends off-screen
        available_w = int(self.screen_geom.width() - 2 * self.margin)
        if w > available_w:
            # if called without an explicit width, shrink the current widget immediately
            if width is None:
                self._w = available_w
                # Resize and recompute geometry deterministically
                self.resize(self._w, self._h)
                self._update_geometry()
                self.label.setGeometry(*self._label_rect)
            w = available_w
        # Fixed left X (top-left anchor)
        onscreen_x = int(self.screen_geom.left() + self.margin)

        onscreen_y = int(self.screen_geom.top() + self.margin)
        offscreen_x = onscreen_x
        offscreen_y = int(self.screen_geom.top() - self._h - self.margin)

        # store positions
        self.onscreen_pos = QPoint(int(onscreen_x), int(onscreen_y))
        self.offscreen_pos = QPoint(int(offscreen_x), int(offscreen_y))

    def set_state(self, text, color: QColor, auto_hide_ms=None):
        # Centralized visual state change: color, text, sizing, animation
        self._accent_color = color
        # Compute final clamped width and update positions from it
        new_w = self._prepare_geometry_for_text(text)

        # Apply width (which will animate) and update label content
        self._apply_width(new_w)
        self.label.setText(text)
        self.update()

        # Manage auto-hide semantics (no boolean state flag)
        self._off_timer.stop()

        self.slide_in()
        if auto_hide_ms is not None:
            self._off_timer.start(auto_hide_ms)

    def update_text_only(self, text: str):
        """Update label text and width without restarting slide animation."""
        # compute and clamp width and update positions using centralized helper
        new_w = self._prepare_geometry_for_text(text)
        self.label.setText(text)
        self._apply_width(new_w)
        self.update()

def _overlay_main(queue):
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    geom = screen.availableGeometry()

    banner = Banner(geom)
    # countdown state for job warp lifecycle
    countdown = {"remaining": 0}

    # Reusable single countdown timer to avoid leaked timers and duplicate connections
    _countdown_timer = QTimer()
    _countdown_timer.setInterval(1000)

    def start_countdown(seconds=35):
        # stop existing timer and disconnect previous handler
        if _countdown_timer.isActive():
            _countdown_timer.stop()

        # Explicitly disconnect previous slot if present (cheap attribute guard)
        if hasattr(_countdown_timer, "_slot") and _countdown_timer._slot is not None:
            try:
                _countdown_timer.timeout.disconnect(_countdown_timer._slot)
            except Exception:
                pass
            _countdown_timer._slot = None

        countdown["remaining"] = int(seconds)
        # initial full set_state (slides in)
        banner.set_state(f"Job Warp <b>Started</b> · {countdown['remaining']}s", COLOR_GREEN)

        def _tick():
            countdown["remaining"] -= 1
            if countdown["remaining"] <= 0:
                if _countdown_timer.isActive():
                    _countdown_timer.stop()
                if hasattr(_countdown_timer, "_slot") and _countdown_timer._slot is not None:
                    try:
                        _countdown_timer.timeout.disconnect(_countdown_timer._slot)
                    except Exception:
                        pass
                    _countdown_timer._slot = None
                banner.set_state("Job Warp <b>Complete</b>", COLOR_BLUE, auto_hide_ms=AUTO_HIDE_MS)
                return
            # lightweight in-place update
            banner.update_text_only(f"Job Warp <b>Started</b> press F5 to abort · {countdown['remaining']}s")

        # store slot on timer so disconnect is cheap and deterministic
        _countdown_timer._slot = _tick
        _countdown_timer.timeout.connect(_countdown_timer._slot)
        _countdown_timer.start()

    def cancel_countdown():
        if _countdown_timer.isActive():
            _countdown_timer.stop()
        if hasattr(_countdown_timer, "_slot") and _countdown_timer._slot is not None:
            try:
                _countdown_timer.timeout.disconnect(_countdown_timer._slot)
            except Exception:
                pass
            _countdown_timer._slot = None
        countdown["remaining"] = 0
        banner.set_state("Job Warp <b>Cancelled</b>", COLOR_RED, auto_hide_ms=AUTO_HIDE_MS)
    def poll_queue():
        # Process all queued messages until empty; break on empty
        try:
            while True:
                try:
                    cmd = queue.get_nowait()
                except Exception:
                    break

                # Legacy toggle states
                if cmd == "ON":
                    banner.set_state("No Save <b>ON</b>", COLOR_GREEN)

                elif cmd == "OFF":
                    banner.set_state("No Save <b>OFF</b>", COLOR_RED, auto_hide_ms=AUTO_HIDE_MS)

                # Job Warp lifecycle states
                elif cmd == "JOB_STARTING":
                    # start a countdown that updates the existing banner in-place
                    start_countdown(40)

                elif cmd == "JOB_CANCELLED":
                    # cancel any running countdown and show cancelled state
                    cancel_countdown()

                elif cmd == "JOB_DONE":
                    # finish countdown early if running, show done state
                    if _countdown_timer.isActive():
                        _countdown_timer.stop()
                    if hasattr(_countdown_timer, "_slot") and _countdown_timer._slot is not None:
                        try:
                            _countdown_timer.timeout.disconnect(_countdown_timer._slot)
                        except Exception:
                            pass
                        _countdown_timer._slot = None
                    countdown["remaining"] = 0
                    banner.set_state("Job Warp <b>Complete</b>", COLOR_BLUE, auto_hide_ms=AUTO_HIDE_MS)

                # Generic message support: ("MSG", text, optional_state)
                elif isinstance(cmd, tuple) and len(cmd) >= 2 and cmd[0] == "MSG":
                    text = cmd[1]
                    state = cmd[2] if len(cmd) > 2 else None
                    if state == "ON":
                        color = COLOR_GREEN
                    elif state == "OFF":
                        color = COLOR_RED
                    else:
                        color = COLOR_NEUTRAL
                    banner.set_state(text, color, auto_hide_ms=AUTO_HIDE_MS if state == "OFF" else None)

                # Countdown text update without re-sliding
                elif isinstance(cmd, tuple) and len(cmd) == 2 and cmd[0] == "COUNTDOWN":
                    banner.update_text_only(cmd[1])

                # Shutdown
                elif cmd == "STOP":
                    app.quit()
                    return

        except Exception:
            # keep overlay robust to queue errors
            pass


    timer = QTimer()
    timer.timeout.connect(poll_queue)
    # Attach timer to banner so banner methods can restart polling when needed
    banner._poll_timer = timer
    timer.start(POLL_INTERVAL_MS)

    app.exec()

_ctx = multiprocessing.get_context("spawn")
_proc = None
_queue = None


def _ensure_started():
    global _proc, _queue
    if _proc is None or not _proc.is_alive():
        _queue = _ctx.Queue()
        _proc = _ctx.Process(target=_overlay_main, args=(_queue,), daemon=True)
        _proc.start()
    else:
        # Best-effort: nudge a running overlay process to ensure it will poll
        try:
            if _queue is not None:
                # put a no-op message to keep behaviour unchanged; overlay will process when polling
                _queue.put(("MSG", "", None))
        except Exception:
            pass


def show_on():
    _ensure_started()
    _queue.put("ON")


def show_off():
    _ensure_started()
    _queue.put("OFF")


def jobwarpstarting():
    _ensure_started()
    _queue.put("JOB_STARTING")


def jobwarpcancelling():
    _ensure_started()
    _queue.put("JOB_CANCELLED")


def jobwarpdone():
    _ensure_started()
    _queue.put("JOB_DONE")


def show_msg(text, state=None):
    """Show a custom message in the overlay. `state` may be 'ON' or 'OFF'."""
    _ensure_started()
    if state:
        _queue.put(("MSG", text, state))
    else:
        _queue.put(("MSG", text))


def update_countdown(text):
    """Send a COUNTDOWN message to update text/width without re-sliding."""
    _ensure_started()
    _queue.put(("COUNTDOWN", text))


def stop():
    global _proc, _queue
    if _queue:
        _queue.put("STOP")
    if _proc:
        _proc.join(timeout=1)
        # Defensive cleanup: if still alive after join timeout, attempt terminate
        try:
            if _proc.is_alive():
                _proc.terminate()
        except Exception:
            pass
