#!/usr/bin/env python3
import sys
import os
import subprocess
import time

# Insere o diretório base para resolver os imports de forma universal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
)
from PySide6.QtCore import (
    Qt,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QPalette,
)

from server.core import create_virtual_pad, ServerSignals, ServerThread
from server.ui_components import (
    ConnectionPanel,
    TimelineBody,
    BG,
    SURFACE,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    DOT_NETWORK,
    DOT_CONNECT,
    DOT_DISCONNECT,
    DOT_NEUTRAL,
)


def check_root():
    if os.geteuid() != 0:
        cmd = [
            "pkexec",
            "env",
            f'DISPLAY={os.environ.get("DISPLAY", ":0")}',
            f'XAUTHORITY={os.environ.get("XAUTHORITY", "")}',
            sys.executable,
            os.path.abspath(sys.argv[0]),
        ]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError:
            pass
        sys.exit(0)


check_root()
os.system("sudo apt install libqt6gui6 libqt6widgets6 libqt6core6")


class VolantWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.virtual_pad = create_virtual_pad()
        self.setWindowTitle("Volant Server")
        self.setMinimumSize(380, 520)
        self.resize(390, 520)
        self._apply_style()
        self._build_ui()
        self._start_server()

    def _apply_style(self):
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background: {BG};
                color: {TEXT_PRIMARY};
                font-family: 'Inter', 'SF Pro Text', 'Segoe UI', sans-serif;
            }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent; width: 3px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """
        )

    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(10)

        title = QLabel("Volant Server")
        title.setStyleSheet(
            f"color:{TEXT_PRIMARY}; font-size:16px; font-weight:600; letter-spacing:-0.3px;"
        )
        layout.addWidget(title)

        self._conn_panel = ConnectionPanel()
        layout.addWidget(self._conn_panel)

        log_lbl = QLabel("Log")
        log_lbl.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:10px; letter-spacing:0.5px;"
        )
        layout.addWidget(log_lbl)

        self._timeline = TimelineBody()
        self._timeline.setStyleSheet("background:transparent;")

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setWidget(self._timeline)
        self._scroll.setStyleSheet("background:transparent;")
        layout.addWidget(self._scroll, stretch=1)

        stop = QPushButton("Stop Server")
        stop.setCursor(Qt.PointingHandCursor)
        stop.setFixedHeight(40)
        stop.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_MUTED};
                border: 1px solid {BORDER};
                border-radius: 10px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: #888;
                color: {TEXT_PRIMARY};
            }}
            QPushButton:pressed {{
                background: rgba(255,255,255,0.04);
            }}
        """
        )
        stop.clicked.connect(self._on_stop)
        layout.addWidget(stop)
        self.setCentralWidget(root)

    def _start_server(self):
        self._signals = ServerSignals()
        self._signals.stage_update.connect(self._on_stage)
        self._signals.log_entry.connect(self._on_log)
        self._server = ServerThread(self._signals, self.virtual_pad)
        self._server.start()

    def _on_stage(self, stage: str):
        self._conn_panel.activate_stage(stage)

    def _on_log(self, entry_type: str, title: str, detail: str):
        color_map = {
            "network": DOT_NETWORK,
            "connect": DOT_CONNECT,
            "disconnect": DOT_DISCONNECT,
        }
        dot_color = color_map.get(entry_type, DOT_NEUTRAL)
        self._timeline.append_row(time.strftime("%H:%M"), title, detail, dot_color)

        if entry_type == "connect":
            self._conn_panel.on_client_connected(detail)
        elif entry_type == "disconnect":
            self._conn_panel.on_client_disconnected()

        QTimer.singleShot(60, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        bar = self._scroll.verticalScrollBar()
        anim = QPropertyAnimation(bar, b"value", self)
        anim.setDuration(300)
        anim.setEndValue(bar.maximum())
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def _on_stop(self):
        self._server.stop()
        self.virtual_pad.close()
        self.close()

    def closeEvent(self, event):
        self._server.stop()
        self.virtual_pad.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Volant Server")

    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
    pal.setColor(QPalette.Base, QColor(SURFACE))
    pal.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
    pal.setColor(QPalette.Button, QColor(SURFACE))
    pal.setColor(QPalette.ButtonText, QColor(TEXT_PRIMARY))
    pal.setColor(QPalette.Highlight, QColor("#3a3a3c"))
    pal.setColor(QPalette.HighlightedText, QColor(TEXT_PRIMARY))
    app.setPalette(pal)

    win = VolantWindow()
    win.show()
    sys.exit(app.exec())
