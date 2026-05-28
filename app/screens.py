import socket
import threading
import math
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.storage.jsonstore import JsonStore
from app.ui_components import (
    ControleBotao,
    AnalogicoWidget,
    GatilhoWidget,
    ControleToggle,
)

try:
    from plyer import accelerometer
except ImportError:
    accelerometer = None


class InterfaceConexao(Screen):
    pass


class InterfaceBusca(Screen):
    def on_enter(self):
        self.iniciar_busca()

    def iniciar_busca(self):
        self.ids.lista_dispositivos.clear_widgets()
        threading.Thread(target=self._executar_scan, daemon=True).start()

    def _executar_scan(self):
        encontrados = []
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind(("", 5000))
            sock.settimeout(2.0)
            for _ in range(5):
                try:
                    data, addr = sock.recvfrom(1024)
                    ip = addr[0]
                    if ip not in encontrados:
                        encontrados.append(ip)
                        Clock.schedule_once(lambda dt, i=ip: self.adicionar_item(i))
                except socket.timeout:
                    break
            sock.close()
        except:
            pass

    def adicionar_item(self, ip):
        btn = ControleBotao(text=f"Servidor: {ip}", size_hint_y=None, height=dp(80))
        btn.bind(on_release=lambda x: App.get_running_app().conectar_servidor(ip))
        self.ids.lista_dispositivos.add_widget(btn)


class InterfacePrincipal(Screen):
    infoConexao = StringProperty("Offline")
    modoEdicaoAtivo = BooleanProperty(False)
    giroscopioAtivo = False
    last_tilt = 0.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore("layout_config.json")
        self.configurar_controles()

    def obter_posicao(self, key, default_x, default_y):
        if self.store.exists(key):
            pos = self.store.get(key)
            return pos["x"], pos["y"]
        return default_x, default_y

    def configurar_controles(self):
        botoes = [
            ("A", 0.8239583333333333, 0.08333333333333334, "BTN_A"),
            ("B", 0.94375, 0.08148148148148146, "BTN_B"),
            ("X", 0.6979166666666666, 0.0777777777777778, "BTN_NORTH"),
            ("Y", 0.821875, 0.24259259259259258, "BTN_WEST"),
            ("LB", 0.36875, 0.9148148148148149, "BTN_TL"),
            ("RB", 0.640625, 0.912962962962963, "BTN_TR"),
            ("SEL", 0.22916666666666666, 0.912962962962963, "BTN_SELECT"),
            ("STR", 0.7635416666666667, 0.9074074074074074, "BTN_START"),
        ]
        dpad = [
            ("↑", 0.22, 0.38, "ABS_HAT0Y", -1),
            ("↓", 0.22, 0.12, "ABS_HAT0Y", 1),
            ("←", 0.12, 0.25, "ABS_HAT0X", -1),
            ("→", 0.32, 0.25, "ABS_HAT0X", 1),
        ]

        for t, px, py, c in botoes:
            cx, cy = self.obter_posicao(t, px, py)
            btn = ControleBotao(
                text=t,
                size_hint=(0.08, 0.13),
                pos_hint={"center_x": cx, "center_y": cy},
            )
            btn.store_key = t
            btn.bind(on_press=lambda inst, code=c: self.enviar("key", code, 1))
            btn.bind(on_release=lambda inst, code=c: self.enviar("key", code, 0))
            self.ids.area_controles.add_widget(btn)

        for t, px, py, c, v in dpad:
            cx, cy = self.obter_posicao(t, px, py)
            btn = ControleBotao(
                text=t,
                size_hint=(0.08, 0.13),
                pos_hint={"center_x": cx, "center_y": cy},
            )
            btn.store_key = t
            btn.bind(on_press=lambda inst, code=c, val=v: self.enviar("abs", code, val))
            btn.bind(on_release=lambda inst, code=c: self.enviar("abs", code, 0))
            self.ids.area_controles.add_widget(btn)

        cx, cy = self.obter_posicao("analogMain", 0.18, 0.58)
        self.analogMain = AnalogicoWidget(
            "main", self.enviar_an, pos_hint={"center_x": cx, "center_y": cy}
        )
        self.analogMain.store_key = "analogMain"

        cx, cy = self.obter_posicao("analogCam", 0.82, 0.58)
        self.analogCam = AnalogicoWidget(
            "cam", self.enviar_an, pos_hint={"center_x": cx, "center_y": cy}
        )
        self.analogCam.store_key = "analogCam"

        self.ids.area_controles.add_widget(self.analogMain)
        self.ids.area_controles.add_widget(self.analogCam)

        cx, cy = self.obter_posicao("gatilhoLT", 0.05, 0.50)
        self.gatilhoLT = GatilhoWidget(
            "ABS_Z", self.enviar, pos_hint={"center_x": cx, "center_y": cy}
        )
        self.gatilhoLT.store_key = "gatilhoLT"

        cx, cy = self.obter_posicao("gatilhoRT", 0.95, 0.50)
        self.gatilhoRT = GatilhoWidget(
            "ABS_RZ", self.enviar, pos_hint={"center_x": cx, "center_y": cy}
        )
        self.gatilhoRT.store_key = "gatilhoRT"

        self.ids.area_controles.add_widget(self.gatilhoLT)
        self.ids.area_controles.add_widget(self.gatilhoRT)

        cx, cy = self.obter_posicao("btn_giro", 0.5, 0.4)
        self.btn_giro = ControleToggle(
            text="VOLANTE",
            size_hint=(0.15, 0.12),
            pos_hint={"center_x": cx, "center_y": cy},
        )
        self.btn_giro.store_key = "btn_giro"
        self.btn_giro.bind(
            state=lambda inst, val: self.toggle_giroscopio(val == "down")
        )
        self.ids.area_controles.add_widget(self.btn_giro)

    def alternar_edicao(self, estado):
        self.modoEdicaoAtivo = estado
        for c in self.ids.area_controles.children:
            if hasattr(c, "modoEdicao"):
                c.modoEdicao = estado

    def salvar_layout(self):
        for c in self.ids.area_controles.children:
            wid = getattr(c, "store_key", None)
            if wid and "center_x" in c.pos_hint and "center_y" in c.pos_hint:
                self.store.put(wid, x=c.pos_hint["center_x"], y=c.pos_hint["center_y"])
        self.alternar_edicao(False)

    def toggle_giroscopio(self, estado):
        self.giroscopioAtivo = estado
        if estado:
            self.last_tilt = 0.0
            try:
                if accelerometer:
                    accelerometer.enable()
                    Clock.schedule_interval(self.update_giro, 1.0 / 60.0)
            except:
                pass
        else:
            Clock.unschedule(self.update_giro)
            self.enviar("abs", "ABS_X", 0)

    def update_giro(self, dt):
        if not self.giroscopioAtivo or not accelerometer:
            return
        try:
            acc = accelerometer.acceleration
            if acc:
                y = acc[1]
                alvo = (max(min(y, 7.0), -7.0) / 7.0) * 255
                self.last_tilt = (0.3 * alvo) + (0.7 * self.last_tilt)
                self.enviar("abs", "ABS_X", int(self.last_tilt))
        except:
            pass

    def enviar(self, t, c, v):
        App.get_running_app().enviar_socket({"type": t, "code": c, "value": v})

    def enviar_an(self, id_an, x, y):
        px = "ABS_X" if id_an == "main" else "ABS_RX"
        py = "ABS_Y" if id_an == "main" else "ABS_RY"
        if not (id_an == "main" and self.giroscopioAtivo):
            self.enviar("abs", px, x)
        self.enviar("abs", py, y)
