# Volant-GT

<p align="center">
  <img src="assets/images/icon.svg" width="120" alt="Volant-GT Icon">
</p>

Bem-vindo ao **Volant-GT**, uma solução completa para utilizar seu dispositivo Android como um controle virtual ou volante para Linux, utilizando conexões WebSocket de baixa latência e emulação de input no kernel (`uinput`).

## 📌 Visão Geral
O projeto é composto de duas partes essenciais:
1. **App Mobile (Android)**: Interface construída em Kivy, capturando toques na tela e dados do giroscópio.
2. **Servidor (Linux)**: Aplicação PyQt6/PySide6 rodando em modo `root` (via `pkexec`) que emula um controle de Xbox 360 através do `evdev/uinput`.

## 📂 Estrutura do Projeto
A base de código foi refatorada e organizada de forma modular para fácil manutenção.

- `app/`
  - `main.py`
  - `__init__.py`
  - `ui_components.py`
  - `screens.py`
- `server/`
  - `main-server.py`
  - `__init__.py`
  - `core.py`
  - `ui_components.py`
  - `build-server.sh`
- `assets/images/`
- `build/`
  - `build-app.sh`

## ⚙️ Requisitos e Dependências

O projeto usa a ferramenta **`uv`** para um gerenciamento super-rápido de pacotes e ambientes Python.

### Dependências do Sistema (Linux)
O servidor requer algumas bibliotecas do sistema para interface gráfica e manipulação de entrada. Caso não as tenha, execute:
```bash
sudo apt update
sudo apt install libqt6gui6 libqt6widgets6 libqt6core6 policykit-1
```

## 🚀 Build e Execução

**1. Configurar o Ambiente Virtual (usando `uv`)**
Crie e ative seu ambiente virtual na raiz do projeto:
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

**2. Rodar o App Mobile**
```bash
uv run app/main.py
```

**3. Rodar o Servidor**
```bash
sudo apt install libqt6gui6 libqt6widgets6 libqt6core6
uv run server/main-server.py
```

**4. Gerar as Builds**
- App Android: `bash build/build-app.sh`
- Servidor Debian: `bash build/build-server.sh`
