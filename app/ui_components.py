import math
from kivy.metrics import dp
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.floatlayout import FloatLayout

KV = """
<ControleBotao>:
    background_normal: ''
    background_down: ''
    background_color: (0, 0, 0, 0)
    canvas.before:
        Color:
            rgba: (0.94, 0.94, 0.94, 1) if self.state == 'normal' else (0.4, 0.4, 0.4, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height * 0.3]
    canvas.after:
        Color:
            rgba: (0, 0.8, 1, 1) if self.modoEdicao else (0, 0, 0, 0)
        Line:
            width: dp(1.5)
            rectangle: (self.x - dp(2), self.y - dp(2), self.width + dp(4), self.height + dp(4))
    color: (0.13, 0.13, 0.13, 1) if self.state == 'normal' else (1, 1, 1, 1)
    font_size: '16sp'
    bold: True

<ControleToggle>:
    background_normal: ''
    background_down: ''
    background_color: (0, 0, 0, 0)
    canvas.before:
        Color:
            rgba: (0, 0.8, 1, 1) if self.state == 'down' else (0.2, 0.2, 0.2, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.height * 0.3]
    canvas.after:
        Color:
            rgba: (0, 0.8, 1, 1) if self.modoEdicao else (0, 0, 0, 0)
        Line:
            width: dp(1.5)
            rectangle: (self.x - dp(2), self.y - dp(2), self.width + dp(4), self.height + dp(4))
    color: (0.13, 0.13, 0.13, 1) if self.state == 'down' else (0.94, 0.94, 0.94, 1)
    font_size: '14sp'
    bold: True

<GatilhoWidget>:
    orientation: 'vertical'
    min: 0
    max: 255
    value: 0
    size_hint: None, None
    size: dp(50), dp(220)
    canvas.before:
        Color:
            rgba: (0.2, 0.2, 0.2, 1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    canvas.after:
        Color:
            rgba: (0, 0.8, 1, 1) if self.modoEdicao else (0, 0, 0, 0)
        Line:
            width: dp(1.5)
            rectangle: (self.x - dp(2), self.y - dp(2), self.width + dp(4), self.height + dp(4))
    cursor_size: (dp(50), dp(25))
    cursor_image: ''
    value_track: True
    value_track_color: (0.94, 0.94, 0.94, 1)
    value_track_width: dp(50)

<AnalogicoWidget>:
    size_hint: None, None
    size: dp(190), dp(190)
    canvas.before:
        Color:
            rgba: (0.4, 0.4, 0.4, 0.2)
        Ellipse:
            pos: self.pos
            size: self.size
        Color:
            rgba: (0.94, 0.94, 0.94, 0.8)
        Ellipse:
            pos: (self.center_x - dp(35) + self.deslocamento_x, self.center_y - dp(35) + self.deslocamento_y)
            size: dp(70), dp(70)
    canvas.after:
        Color:
            rgba: (0, 0.8, 1, 1) if self.modoEdicao else (0, 0, 0, 0)
        Line:
            width: dp(1.5)
            rectangle: (self.x - dp(2), self.y - dp(2), self.width + dp(4), self.height + dp(4))

<InterfaceConexao>:
    canvas.before:
        Color:
            rgba: (0.13, 0.13, 0.13, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(50)
        spacing: dp(25)
        Label:
            text: "VOLANT CONTROLLER"
            font_size: '36sp'
            color: (0.94, 0.94, 0.94, 1)
            bold: True
        ControleBotao:
            text: "BUSCAR SERVIDORES"
            size_hint_y: 0.2
            on_press: root.manager.current = 'tela_busca'
        ControleBotao:
            text: "CONECTAR VIA USB (CABO)"
            size_hint_y: 0.2
            on_press: app.conectar_servidor('127.0.0.1')
        ControleBotao:
            text: "CONFIGURAR LAYOUT (OFFLINE)"
            size_hint_y: 0.2
            on_press: app.iniciar_modo_offline()

<InterfaceBusca>:
    canvas.before:
        Color:
            rgba: (0.13, 0.13, 0.13, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: dp(20)
        spacing: dp(10)
        Label:
            text: "DISPOSITIVOS NA REDE"
            size_hint_y: 0.1
            color: (0.94, 0.94, 0.94, 1)
            bold: True
        ScrollView:
            GridLayout:
                id: lista_dispositivos
                cols: 1
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
        BoxLayout:
            size_hint_y: 0.15
            spacing: dp(10)
            ControleBotao:
                text: "ATUALIZAR"
                on_press: root.iniciar_busca()
            ControleBotao:
                text: "VOLTAR"
                on_press: root.manager.current = 'tela_conexao'
<InterfacePrincipal>:
    canvas.before:
        Color:
            rgba: (0.13, 0.13, 0.13, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    FloatLayout:
        id: area_controles
    
    BoxLayout:
        size_hint: 1, 0.12
        pos_hint: {'top': 1}
        padding: [dp(15), dp(8)]
        spacing: dp(15)
        
        Label:
            text: root.infoConexao
            color: (0.94, 0.94, 0.94, 0.5)
            halign: 'left'
            text_size: self.size
            valign: 'middle'

    ControleBotao:
        text: "SALVAR" if root.modoEdicaoAtivo else "EDITAR"
        size_hint: 0.18, 0.1
        pos_hint: {'center_x': 0.5, 'y': 0.01}
        on_press: root.salvar_layout() if root.modoEdicaoAtivo else root.alternar_edicao(True)
"""


class GatilhoWidget(Slider):
    modoEdicao = BooleanProperty(False)

    def __init__(self, identificador, callback, **kwargs):
        super().__init__(**kwargs)
        self.identificador = identificador
        self.callback = callback

    def on_value(self, instance, value):
        if not self.modoEdicao:
            self.callback("abs", self.identificador, int(value))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.modoEdicao:
                touch.grab(self)
                return True
            return super().on_touch_down(touch)
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self.modoEdicao:
                self.pos_hint = {
                    "center_x": touch.x / self.parent.width,
                    "center_y": touch.y / self.parent.height,
                }
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self.modoEdicao:
                touch.ungrab(self)
                return True
            else:
                res = super().on_touch_up(touch)
                self.value = 0
                return res
        return super().on_touch_up(touch)


class AnalogicoWidget(FloatLayout):
    deslocamento_x = NumericProperty(0)
    deslocamento_y = NumericProperty(0)
    modoEdicao = BooleanProperty(False)

    def __init__(self, identificador, callback, **kwargs):
        super().__init__(**kwargs)
        self.identificador = identificador
        self.callback = callback
        self.raio_max = dp(65)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            if not self.modoEdicao:
                self.atualizar_posicao(touch)
            return True
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self.modoEdicao:
                self.pos_hint = {
                    "center_x": touch.x / self.parent.width,
                    "center_y": touch.y / self.parent.height,
                }
            else:
                self.atualizar_posicao(touch)
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if not self.modoEdicao:
                self.deslocamento_x = 0
                self.deslocamento_y = 0
                self.callback(self.identificador, 0, 0)
            return True
        return False

    def atualizar_posicao(self, touch):
        dx = touch.x - self.center_x
        dy = touch.y - self.center_y
        distancia = math.sqrt(dx**2 + dy**2)
        if distancia > self.raio_max:
            escala = self.raio_max / distancia
            dx *= escala
            dy *= escala
        self.deslocamento_x = dx
        self.deslocamento_y = dy
        norm_x = (dx / self.raio_max) * 255
        norm_y = -(dy / self.raio_max) * 255
        self.callback(self.identificador, int(norm_x), int(norm_y))


class ControleBotao(Button):
    modoEdicao = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.modoEdicao:
                touch.grab(self)
                return True
            return super().on_touch_down(touch)
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self.modoEdicao:
                self.pos_hint = {
                    "center_x": touch.x / self.parent.width,
                    "center_y": touch.y / self.parent.height,
                }
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self.modoEdicao:
                touch.ungrab(self)
                return True
        return super().on_touch_up(touch)


class ControleToggle(ToggleButton):
    modoEdicao = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.modoEdicao:
                touch.grab(self)
                return True
            return super().on_touch_down(touch)
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self.modoEdicao:
                self.pos_hint = {
                    "center_x": touch.x / self.parent.width,
                    "center_y": touch.y / self.parent.height,
                }
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            if self.modoEdicao:
                touch.ungrab(self)
                return True
        return super().on_touch_up(touch)
