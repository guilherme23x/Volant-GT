import sys
import socket
import time
import json
import threading
import asyncio
import websockets
from evdev import UInput, ecodes as e, AbsInfo
from PySide6.QtCore import QThread, Signal, QObject

BROADCAST_PORT = 5000
WEBSOCKET_PORT = 8080
DEVICE_NAME = "Microsoft X-Box 360 pad"

ABS_RANGE_STICK = AbsInfo(
    value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0
)
ABS_RANGE_TRIGGER = AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)
ABS_RANGE_DPAD = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)

CAPABILITIES = {
    e.EV_KEY: [
        e.BTN_SOUTH,
        e.BTN_EAST,
        e.BTN_NORTH,
        e.BTN_WEST,
        e.BTN_TL,
        e.BTN_TR,
        e.BTN_SELECT,
        e.BTN_START,
        e.BTN_MODE,
        e.BTN_THUMBL,
        e.BTN_THUMBR,
    ],
    e.EV_ABS: [
        (e.ABS_X, ABS_RANGE_STICK),
        (e.ABS_Y, ABS_RANGE_STICK),
        (e.ABS_RX, ABS_RANGE_STICK),
        (e.ABS_RY, ABS_RANGE_STICK),
        (e.ABS_Z, ABS_RANGE_TRIGGER),
        (e.ABS_RZ, ABS_RANGE_TRIGGER),
        (e.ABS_HAT0X, ABS_RANGE_DPAD),
        (e.ABS_HAT0Y, ABS_RANGE_DPAD),
    ],
}

BUTTON_MAP = {
    "BTN_A": e.BTN_SOUTH,
    "BTN_B": e.BTN_EAST,
    "BTN_X": e.BTN_WEST,
    "BTN_Y": e.BTN_NORTH,
    "BTN_NORTH": e.BTN_NORTH,
    "BTN_SOUTH": e.BTN_SOUTH,
    "BTN_EAST": e.BTN_EAST,
    "BTN_WEST": e.BTN_WEST,
    "BTN_TL": e.BTN_TL,
    "BTN_TR": e.BTN_TR,
    "BTN_SELECT": e.BTN_SELECT,
    "BTN_START": e.BTN_START,
    "BTN_MODE": e.BTN_MODE,
    "BTN_THUMBL": e.BTN_THUMBL,
    "BTN_THUMBR": e.BTN_THUMBR,
}


def create_virtual_pad():
    try:
        return UInput(
            CAPABILITIES,
            name=DEVICE_NAME,
            vendor=0x045E,
            product=0x028E,
            version=0x110,
            bustype=0x03,
        )
    except Exception as ex:
        print(f"UInput error: {ex}")
        sys.exit(1)


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class ServerSignals(QObject):
    stage_update = Signal(str)
    log_entry = Signal(str, str, str)


class ServerThread(QThread):
    def __init__(self, signals: ServerSignals, virtual_pad):
        super().__init__()
        self._signals = signals
        self.ui = virtual_pad
        self._is_running = True
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event: asyncio.Event | None = None

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        threading.Thread(target=self._broadcast_presence, daemon=True).start()

        local_ip = get_local_ip()
        self._signals.stage_update.emit("wifi")
        time.sleep(0.3)
        self._signals.stage_update.emit("ws")
        time.sleep(0.3)
        self._signals.stage_update.emit("uinput")
        self._signals.log_entry.emit(
            "network", "Server Active", f"{local_ip}:{WEBSOCKET_PORT}"
        )

        self._loop.run_until_complete(self._run_server())

    async def _run_server(self):
        self._stop_event = asyncio.Event()
        async with websockets.serve(self._handle_client, "0.0.0.0", WEBSOCKET_PORT):
            await self._stop_event.wait()

    def _broadcast_presence(self):
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        payload = json.dumps(
            {
                "name": "Xbox 360 Controller",
                "ip": get_local_ip(),
                "port": WEBSOCKET_PORT,
                "type": "volant_server",
            }
        ).encode()
        while self._is_running:
            try:
                udp.sendto(payload, ("<broadcast>", BROADCAST_PORT))
                time.sleep(2)
            except Exception:
                time.sleep(5)

    async def _handle_client(self, websocket):
        client_ip = websocket.remote_address[0]
        self._signals.stage_update.emit("device")
        self._signals.log_entry.emit("connect", "Client Connected", client_ip)
        try:
            async for message in websocket:
                data = json.loads(message)
                code_str, value, msg_type = (
                    data.get("code"),
                    int(data.get("value", 0)),
                    data.get("type"),
                )
                if msg_type == "key" and (
                    code := BUTTON_MAP.get(code_str) or getattr(e, code_str, None)
                ):
                    self.ui.write(e.EV_KEY, code, value)
                    self.ui.syn()
                elif msg_type == "abs" and hasattr(e, code_str):
                    code = getattr(e, code_str)
                    self.ui.write(
                        e.EV_ABS,
                        code,
                        (
                            int((value / 255.0) * 32767)
                            if code in (e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY)
                            else value
                        ),
                    )
                    self.ui.syn()
        except Exception:
            pass
        finally:
            self._signals.log_entry.emit("disconnect", "Client Disconnected", client_ip)

    def stop(self):
        self._is_running = False
        if self._loop and self._stop_event:
            self._loop.call_soon_threadsafe(self._stop_event.set)
