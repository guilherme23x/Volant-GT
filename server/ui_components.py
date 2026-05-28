import math
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    Property,
    QPointF,
    QRectF,
)
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QFontMetrics
from server.core import WEBSOCKET_PORT

# ── Design tokens ─────────────────────────────────────────────────────────────
BG = "#1e1e20"
SURFACE = "#2a2a2c"
BORDER = "#363638"
TEXT_PRIMARY = "#efefef"
TEXT_MUTED = "#666668"
TEXT_DIM = "#3e3e40"
LINE_COLOR = "#303032"

ACTIVE_STROKE = QColor("#d0d0d2")
IDLE_STROKE = QColor("#3e3e40")
DOT_CONNECT = QColor("#c8c8ca")
DOT_DISCONNECT = QColor("#666668")
DOT_NETWORK = QColor("#909092")
DOT_NEUTRAL = QColor("#3e3e40")

DOT_D = 14
RAIL_X = 20
GUTTER = 48

BOOT_ORDER = ["wifi", "ws", "uinput"]
ALL_STAGES = ["device", "wifi", "ws", "uinput"]
STAGE_LABELS = {
    "device": "Device",
    "wifi": "Wi-Fi",
    "ws": "WebSocket",
    "uinput": "UInput",
}
STAGE_ORDER = ["device", "wifi", "ws", "uinput"]


# ── Components ────────────────────────────────────────────────────────────────
class ConnectionIcon(QWidget):
    def __init__(self, label: str, icon_type: str, parent=None):
        super().__init__(parent)
        self._label = label
        self._icon_type = icon_type
        self._progress = 0.0
        self._phase = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._tick)
        self.setFixedSize(64, 72)
        self._anim = QPropertyAnimation(self, b"progress", self)
        self._anim.setDuration(700)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_progress(self) -> float:
        return self._progress

    def set_progress(self, v: float):
        self._progress = v
        self.update()

    progress = Property(float, get_progress, set_progress)

    def activate(self):
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._pulse_timer.start(30)

    def deactivate(self):
        self._pulse_timer.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _tick(self):
        self._phase = (self._phase + 0.045) % (2 * math.pi)
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2.0, 28.0
        t = self._progress
        val = int(0x3E + (0xD0 - 0x3E) * t)
        stroke = QColor(val, val, val + 2)

        p.setPen(QPen(stroke, 1.2 + 0.6 * t, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        p.save()
        p.translate(cx - 12, cy - 12)
        self._draw_icon(p, stroke)
        p.restore()

        label_v = int(0x44 + (0xEF - 0x44) * t)
        p.setPen(QColor(label_v, label_v, label_v + 2))
        font = QFont("Inter", 9)
        p.setFont(font)
        tw = QFontMetrics(font).horizontalAdvance(self._label)
        p.drawText(int(cx - tw / 2), int(cy + 42), self._label)

    def _draw_icon(self, p, stroke):
        t = self._icon_type
        p.setBrush(Qt.NoBrush)
        if t == "device":
            p.drawRoundedRect(QRectF(5, 1, 14, 22), 2.5, 2.5)
            p.setBrush(QBrush(stroke))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(12, 19.5), 1.1, 1.1)
        elif t == "wifi":
            for r in [3.0, 6.5, 10.0]:
                p.drawArc(
                    QRectF(12 - r, 13 - r, r * 2, r * 2), int(210 * 16), int(120 * 16)
                )
            p.setBrush(QBrush(stroke))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(12, 20.8), 1.2, 1.2)
        elif t == "ws":
            p.drawEllipse(QRectF(2, 2, 20, 20))
            p.drawLine(QPointF(12, 2), QPointF(12, 22))
            p.drawLine(QPointF(2, 12), QPointF(22, 12))
            p.drawArc(QRectF(6, 2, 12, 20), 0, int(180 * 16))
            p.drawArc(QRectF(6, 2, 12, 20), int(180 * 16), int(180 * 16))
        elif t == "uinput":
            p.drawRoundedRect(QRectF(2, 7, 20, 10), 2, 2)
            p.drawLine(QPointF(5.5, 12), QPointF(8.5, 12))
            p.drawLine(QPointF(7, 10.5), QPointF(7, 13.5))
            p.setBrush(QBrush(stroke))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(15.0, 11.5), 0.9, 0.9)
            p.drawEllipse(QPointF(17.5, 11.5), 0.9, 0.9)


class ConnectionRail(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fill = 0.0
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._anim = QPropertyAnimation(self, b"fill", self)
        self._anim.setDuration(600)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def get_fill(self) -> float:
        return self._fill

    def set_fill(self, v: float):
        self._fill = v
        self.update()

    fill = Property(float, get_fill, set_fill)

    def animate_to(self, target: float):
        self._anim.setStartValue(self._fill)
        self._anim.setEndValue(max(0.0, min(1.0, target)))
        self._anim.start()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(TEXT_DIM)))
        p.setPen(Qt.NoPen)
        p.drawRect(0, 0, self.width(), 1)
        if self._fill > 0:
            p.setBrush(QBrush(QColor(ACTIVE_STROKE)))
            p.drawRect(0, 0, max(1, int(self.width() * self._fill)), 1)


class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor(TEXT_DIM)
        self._is_active = False
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setFixedSize(22, 22)

    def set_active(self, color: QColor, active: bool):
        self._color = color
        self._is_active = active
        self._timer.start(30) if active else self._timer.stop()
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.05) % (2 * math.pi)
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = self.width() / 2.0
        if self._is_active:
            halo = QColor(self._color)
            halo.setAlphaF(0.18 * (0.5 + 0.5 * math.sin(self._phase)))
            p.setBrush(QBrush(halo))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(c, c), 7, 7)
        p.setBrush(QBrush(self._color))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(c, c), 3.5, 3.5)


class ConnectionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = set()
        self._sessions = 0
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        card = QFrame()
        card.setObjectName("CP")
        card.setStyleSheet(
            f"QFrame#CP {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 16px; }}"
        )
        outer.addWidget(card)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(12)
        hrow = QHBoxLayout()
        hrow.setSpacing(0)
        name = QLabel("Xbox 360 Controller")
        name.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:13px; font-weight:500; background:transparent;"
        )
        hrow.addWidget(name)
        hrow.addStretch()

        self._session_lbl = QLabel("")
        self._session_lbl.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:10px; background:transparent;"
        )
        hrow.addWidget(self._session_lbl, alignment=Qt.AlignRight | Qt.AlignVCenter)
        inner.addLayout(hrow)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{BORDER}; border:none;")
        inner.addWidget(sep)

        icon_row = QWidget()
        icon_row.setStyleSheet("background:transparent;")
        il = QHBoxLayout(icon_row)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(0)

        self._icons, self._rails = {}, []
        for i, stage in enumerate(STAGE_ORDER):
            icon = ConnectionIcon(STAGE_LABELS[stage], stage)
            self._icons[stage] = icon
            il.addWidget(icon, alignment=Qt.AlignHCenter)
            if i < len(STAGE_ORDER) - 1:
                rail = ConnectionRail()
                self._rails.append(rail)
                il.addWidget(rail, alignment=Qt.AlignVCenter)
        inner.addWidget(icon_row)

        srow = QHBoxLayout()
        srow.setSpacing(7)
        self._dot = StatusDot()
        self._status_lbl = QLabel("Initializing")
        self._status_lbl.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:11px; background:transparent;"
        )
        srow.addWidget(self._dot)
        srow.addWidget(self._status_lbl)
        srow.addStretch()
        inner.addLayout(srow)

    def activate_stage(self, stage: str):
        if stage in self._active:
            return
        self._active.add(stage)
        self._icons[stage].activate()
        for i, rail in enumerate(self._rails):
            if STAGE_ORDER[i] in self._active and STAGE_ORDER[i + 1] in self._active:
                rail.animate_to(1.0)
        self._refresh_status(stage)

    def _refresh_status(self, last: str):
        msgs = {
            "wifi": ("Scanning network", False),
            "ws": (f"Listening  :{WEBSOCKET_PORT}", True),
            "uinput": ("Ready — waiting for device", True),
            "device": ("Client connected", True),
        }
        text, active = msgs.get(last, ("Initializing", False))
        self._dot.set_active(
            QColor(ACTIVE_STROKE) if active else QColor(TEXT_DIM), active
        )
        self._status_lbl.setText(text)
        self._status_lbl.setStyleSheet(
            f"color:{TEXT_PRIMARY if active else TEXT_MUTED}; font-size:11px; background:transparent;"
        )

    def on_client_connected(self, ip: str):
        self._sessions += 1
        self._session_lbl.setText(
            f"{self._sessions} session{'s' if self._sessions != 1 else ''}"
        )
        self._dot.set_active(QColor(ACTIVE_STROKE), True)
        self._status_lbl.setText(f"Connected  ·  {ip}")
        self._status_lbl.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:11px; background:transparent;"
        )

    def on_client_disconnected(self):
        self._icons["device"].deactivate()
        self._active.discard("device")
        for i, rail in enumerate(self._rails):
            if STAGE_ORDER[i] in ("uinput", "device") or STAGE_ORDER[i + 1] == "device":
                rail.animate_to(
                    0.0
                    if STAGE_ORDER[i + 1] == "device" or STAGE_ORDER[i] == "device"
                    else 1.0
                )
        self._dot.set_active(QColor(TEXT_DIM), False)
        self._status_lbl.setText("Idle — waiting for device")
        self._status_lbl.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:11px; background:transparent;"
        )


class _DotMarker(QWidget):
    def __init__(self, color: QColor, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedWidth(GUTTER)
        self.setMinimumHeight(DOT_D + 20)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cy, r = self.height() // 2, DOT_D // 2
        halo = QColor(self._color)
        halo.setAlpha(25)
        p.setBrush(QBrush(halo))
        p.setPen(Qt.NoPen)
        p.drawEllipse(RAIL_X - r - 4, cy - r - 4, (r + 4) * 2, (r + 4) * 2)
        p.setBrush(QBrush(self._color))
        p.drawEllipse(RAIL_X - r, cy - r, DOT_D, DOT_D)


class _RailLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(GUTTER)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, _e):
        p = QPainter(self)
        pen = QPen(QColor(LINE_COLOR), 1)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(RAIL_X, 0, RAIL_X, self.height())


class TimelineRow(QWidget):
    def __init__(
        self, timestamp: str, title: str, subtitle: str, dot_color: QColor, parent=None
    ):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(_DotMarker(dot_color), 0, Qt.AlignTop)
        card = QFrame()
        card.setObjectName("TLC")
        card.setStyleSheet(
            f"QFrame#TLC {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 11px; }}"
        )
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 9, 12, 9)
        cl.setSpacing(2)
        tl = QLabel(timestamp)
        tl.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:10px; font-family:monospace; background:transparent; border:none;"
        )
        ttl = QLabel(title)
        ttl.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:12px; font-weight:500; background:transparent; border:none;"
        )
        cl.addWidget(tl)
        cl.addWidget(ttl)
        if subtitle:
            sl = QLabel(subtitle)
            sl.setStyleSheet(
                f"color:{TEXT_MUTED}; font-size:11px; background:transparent; border:none;"
            )
            sl.setWordWrap(True)
            cl.addWidget(sl)
        row.addWidget(card)
        row.addSpacing(2)

    def animate_in(self):
        self._anim = QPropertyAnimation(self, b"maximumHeight", self)
        self._anim.setDuration(380)
        self._anim.setStartValue(0)
        self._anim.setEndValue(self.sizeHint().height() + 4)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self.setMaximumHeight(0)
        self._anim.finished.connect(lambda: self.setMaximumHeight(16777215))
        self._anim.start(QPropertyAnimation.DeleteWhenStopped)


class TimelineBody(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._count, self._rail = 0, _RailLine(self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 6, 0, 6)
        self._layout.setSpacing(6)
        self._layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rail.setGeometry(0, 0, GUTTER, self.height())
        self._rail.lower()

    def append_row(self, timestamp: str, title: str, subtitle: str, dot_color: QColor):
        row = TimelineRow(timestamp, title, subtitle, dot_color)
        stretch = self._layout.takeAt(self._layout.count() - 1)
        self._layout.addWidget(row)
        self._layout.addItem(stretch)
        QTimer.singleShot(min(self._count * 45, 240), row.animate_in)
        self._count += 1
