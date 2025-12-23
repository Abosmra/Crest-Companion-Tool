import sys
import ctypes
import multiprocessing
from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QRectF
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPainterPath


# Win32 constants
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x20
WS_EX_NOACTIVATE = 0x08000000


class Banner(QWidget):
    """HUD banner widget"""

    def __init__(self, screen_geom, width=130, height=48, margin=12, anim_ms=180):
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
        self._is_on = False
        self._accent_color = QColor(60, 160, 90)

        self.resize(width, height)
        self.screen_geom = screen_geom

        self.onscreen_pos = QPoint(
            screen_geom.right() - width - margin, screen_geom.top() + margin
        )
        self.offscreen_pos = QPoint(
            screen_geom.right() - width - margin,
            screen_geom.top() - height - margin
        )
        self.move(self.offscreen_pos)

        # Label
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.label.setFont(QFont("Segoe UI", 12))
        self.label.setStyleSheet("color: rgba(255,255,255,230); padding-left: 0px;")

        # Anim
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setDuration(anim_ms)

        # Timer for auto-hide on OFF
        self._off_timer = QTimer()
        self._off_timer.setSingleShot(True)
        self._off_timer.timeout.connect(self.slide_out)

        # Delayed setup
        QTimer.singleShot(0, self._setup_clickthrough)
        QTimer.singleShot(0, self._setup_blur)

        # Precompute geometry
        self._update_geometry()

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
        padding = max(8, int(self._h * 0.12))
        pill_height = max(8, self._h - 2 * padding)

        accent_w = min(max(10, int(pill_height * 0.28)), int(self._w * 0.18))
        if accent_w > pill_height:
            accent_w = pill_height

        self._padding = padding
        self._pill_height = pill_height
        self._pill_width = accent_w
        self._pill_radius = accent_w / 2.0

        self._pill_rect = QRectF(
            float(padding),
            float(padding),
            float(accent_w),
            float(pill_height),
        )

        label_start = padding + accent_w + padding
        self._label_rect = (
            label_start,
            0,
            self._w - label_start - padding,
            self._h,
        )

        self._card_radius = int(self._h * 0.36)
        self._card_rect = QRectF(self.rect())

    # -----------------------------------------------------------------------
    # Painting
    # -----------------------------------------------------------------------

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

    # -----------------------------------------------------------------------
    # State + Animations
    # -----------------------------------------------------------------------

    def _set_green(self):
        self._accent_color = QColor(60, 160, 90)
        self._is_on = True
        self._off_timer.stop()
        self.label.setText("No Save <b>ON</b>")
        self.update()

    def _set_red(self):
        self._accent_color = QColor(180, 70, 70)
        self._is_on = False
        self.label.setText("No Save <b>OFF</b>")
        self.update()

    def slide_in(self):
        self._cancel_animation()

        start_pos = self.pos()

        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(self.onscreen_pos)

        self.show()
        self.animation.start()

    def slide_out(self):
        if self._is_on:
            return

        self._cancel_animation()

        start_pos = self.pos()
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(self.offscreen_pos)

        self.animation.finished.connect(self.hide)
        self.animation.start()

    def _cancel_animation(self):
        try:
            self.animation.stop()
        except Exception:
            pass
        try:
            self.animation.finished.disconnect()
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Overlay Process (uses ultra-light timer loop)
# ---------------------------------------------------------------------------

def _overlay_main(queue):
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    geom = screen.availableGeometry()

    banner = Banner(geom)

    def poll_queue():
        try:
            while True:
                cmd = queue.get_nowait()
                if cmd == "ON":
                    banner._cancel_animation()
                    banner._off_timer.stop()
                    banner._set_green()
                    banner.slide_in()


                elif cmd == "OFF":
                    banner._cancel_animation()
                    banner._set_red()
                    banner.show()
                    banner._off_timer.stop()
                    banner._off_timer.start(3000)


                elif cmd == "STOP":
                    app.quit()
                    return
        except Exception:
            pass

    timer = QTimer()
    timer.timeout.connect(poll_queue)
    timer.start(40)

    app.exec()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_ctx = multiprocessing.get_context("spawn")
_proc = None
_queue = None


def _ensure_started():
    global _proc, _queue
    if _proc is None or not _proc.is_alive():
        _queue = _ctx.Queue()
        _proc = _ctx.Process(target=_overlay_main, args=(_queue,), daemon=True)
        _proc.start()


def show_on():
    _ensure_started()
    _queue.put("ON")


def show_off():
    _ensure_started()
    _queue.put("OFF")


def stop():
    global _proc, _queue
    if _queue:
        _queue.put("STOP")
    if _proc:
        _proc.join(timeout=1)
