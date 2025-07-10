import flet as ft
import os
import subprocess
import sys
import threading
from viewmodel.converter_vm import iniciar_conversao, iniciar_extracao, parar_conversao

def criar_interface(page, vm):
    # Responsividade: detecta largura da tela
    def largura_responsiva():
        return page.width if page.width else 500

    def largura_card():
        w = largura_responsiva()
        if w < 520:
            return w - 32 if w > 32 else w
        elif w < 700:
            return 420
        else:
            return 420

    def largura_campo():
        w = largura_responsiva()
        if w < 520:
            return w - 32 if w > 32 else w
        else:
            return 380

    # Atualiza layout ao redimensionar
    def on_resize(e):
        page.update()
    page.on_resize = on_resize

    # Paleta de cores invertida fundo/botão
    COR_FUNDO = "#979086"
    COR_CARD = "#1C1C1B"
    COR_DIVISOR = "#6A5D52"
    COR_TEXTO = "#E2E2DE"
    COR_TEXTO_SEC = "#B7AC9B"
    COR_BTN_PRINCIPAL = "#E2E2DE"
    COR_BTN_PRINCIPAL_TXT = "#1C1C1B"
    COR_BTN_SECUNDARIO = "#E2E2DE"
    COR_BTN_SECUNDARIO_TXT = "#1C1C1B"
    COR_ICONE = "#B7AC9B"
    COR_STATUS = "#1C1C1B"
    COR_STATUS_SUCESSO = "#B7AC9B"
    COR_STATUS_AVISO = "#B7AC9B"
    COR_STATUS_ERRO = "#6A5D52"

    page.bgcolor = COR_FUNDO

    # FilePickers
    file_picker_origem = ft.FilePicker()
    file_picker_destino = ft.FilePicker()
    page.overlay.extend([file_picker_origem, file_picker_destino])

    # --- CAMPOS ---
    origem = ft.TextField(
        label="Pasta de Origem",
        hint_text="Selecione a pasta com os arquivos",
        width=lambda: largura_campo(),
        read_only=True,
        bgcolor=COR_CARD,
        color=COR_TEXTO,
        border_color=COR_DIVISOR,
        focused_border_color=COR_DIVISOR,
        label_style=ft.TextStyle(color=COR_TEXTO_SEC, weight="bold"),
        prefix_icon=ft.icons.FOLDER_OPEN,
        border_radius=10,
        text_style=ft.TextStyle(size=15),
        text_align="center"
    )
    destino = ft.TextField(
        label="Pasta de Destino",
        hint_text="Onde salvar os PDFs convertidos",
        width=lambda: largura_campo(),
        read_only=True,
        bgcolor=COR_CARD,
        color=COR_TEXTO,
        border_color=COR_DIVISOR,
        focused_border_color=COR_DIVISOR,
        label_style=ft.TextStyle(color=COR_TEXTO_SEC, weight="bold"),
        prefix_icon=ft.icons.FOLDER_OPEN,
        border_radius=10,
        text_style=ft.TextStyle(size=15),
        text_align="center"
    )

    # --- STATUS E PROGRESSO ---
    status = ft.Container(
        content=ft.Text("", color=COR_TEXTO, text_align="center", size=15, weight="bold"),
        bgcolor=COR_STATUS,
        border_radius=10,
        padding=12,
        margin=ft.margin.only(top=10)
    )
    progresso = ft.Container(
        content=ft.Text("", color=COR_DIVISOR, text_align="center", size=13, weight="bold"),
        bgcolor=COR_STATUS,
        border_radius=10,
        padding=8,
        margin=ft.margin.only(top=5)
    )
    convertendo = ft.Container(
        content=ft.Row([
            ft.ProgressRing(width=18, height=18, color=COR_DIVISOR),
            ft.Text("Convertendo arquivos...", color=COR_DIVISOR, size=15, weight="bold", text_align="center")
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
        visible=False,
        bgcolor=COR_STATUS,
        border_radius=10,
        padding=15,
        margin=ft.margin.only(top=10)
    )

    # --- FUNÇÕES AUXILIARES ---
    def atualizar_origem(path):
        if path:
            origem.value = path
            page.update()
    def atualizar_destino(path):
        if path:
            destino.value = path
        else:
            pasta_padrao = os.path.join(os.path.expanduser("~"), "Desktop", "Convertidos_PDF")
            if not os.path.exists(pasta_padrao):
                os.makedirs(pasta_padrao)
            destino.value = pasta_padrao
        page.update()
    def selecionar_pasta_origem(e):
        file_picker_origem.get_directory_path(dialog_title="Selecione a pasta de origem")
    def selecionar_pasta_destino(e):
        file_picker_destino.get_directory_path(dialog_title="Selecione a pasta de destino")
    file_picker_origem.on_result = lambda e: atualizar_origem(e.path)
    file_picker_destino.on_result = lambda e: atualizar_destino(e.path)
    def abrir_pasta_destino(e):
        if destino.value:
            if sys.platform == "win32":
                os.startfile(destino.value)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", destino.value])
            else:
                subprocess.Popen(["xdg-open", destino.value])
    def extrair_arquivos(e):
        if not origem.value:
            status.content.value = "⚠️ Selecione uma pasta de origem!"
            status.bgcolor = COR_STATUS_AVISO
        else:
            status.content.value = ""
            status.bgcolor = COR_STATUS
            page.update()
            threading.Thread(target=iniciar_extracao, args=(origem.value, atualizar_status)).start()
    def converter_arquivos(e):
        if not origem.value or not destino.value:
            status.content.value = "⚠️ Selecione uma pasta de origem e destino!"
            status.bgcolor = COR_STATUS_AVISO
        else:
            status.content.value = ""
            status.bgcolor = COR_STATUS
            # Reseta o componente convertendo para o estado inicial
            convertendo.content.controls[0].visible = True  # Mostra o ProgressRing
            convertendo.content.controls[1].value = "Convertendo arquivos..."
            convertendo.content.controls[1].color = COR_DIVISOR
            convertendo.visible = True
            progresso.visible = True
            page.update()
            threading.Thread(target=iniciar_conversao, args=(origem.value, destino.value, atualizar_status)).start()
    def parar_arquivos(e):
        parar_conversao(vm)
        status.content.value = "Conversão interrompida pelo usuário."
        status.bgcolor = COR_STATUS_AVISO
        convertendo.visible = False
        progresso.visible = False
        page.update()
    def atualizar_status(mensagem, erro=None):
        if erro:
            status.content.value = f"⚠️ {erro}"
            status.bgcolor = COR_STATUS_ERRO
        else:
            status.content.value = mensagem
            if mensagem.startswith("✅") or mensagem.startswith("⚠️ Conversão concluída"):
                status.bgcolor = COR_STATUS_SUCESSO if mensagem.startswith("✅") else COR_STATUS_AVISO
                convertendo.content.controls[1].value = "Conversão finalizada"
                convertendo.content.controls[1].color = COR_STATUS_SUCESSO if mensagem.startswith("✅") else COR_STATUS_AVISO
                convertendo.content.controls[0].visible = False  # Esconde o ProgressRing
                convertendo.visible = True
                progresso.visible = False
            else:
                status.bgcolor = COR_STATUS
        if mensagem.startswith("✅") or mensagem.startswith("⚠️ Conversão concluída"):
            progresso.visible = False
        page.update()
    def fechar_janela(e):
        if not hasattr(page, 'fechado'):
            page.fechado = True
            print("Fechando a aplicação...")
            page.window_destroy()
            import sys
            sys.exit()
    page.on_window_close = fechar_janela

    # --- HEADER ---
    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.DESCRIPTION_OUTLINED, size=44, color=COR_ICONE),
                ft.Text("Documenta Planejamento e Microfilmagem", size=32, weight="bold", color=COR_TEXTO, text_align="center"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=16),
            ft.Text("Conversor de Documentos", size=18, color=COR_TEXTO_SEC, text_align="center", weight="bold"),
            ft.Text("Transforme seus documentos em PDF com facilidade", size=14, color=COR_DIVISOR, text_align="center"),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
        bgcolor=COR_CARD,
        border_radius=16,
        padding=28,
        margin=ft.margin.only(top=32, left=0, right=0, bottom=24),
        shadow=ft.BoxShadow(blur_radius=18, color="#00000033", offset=ft.Offset(0, 6)),
        width=lambda: largura_card()
    )

    # --- CARD DE CONFIGURAÇÃO ---
    config_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.FOLDER, color=COR_ICONE, size=24),
                ft.Text("Configuração de Pastas", size=20, weight="bold", color=COR_TEXTO, text_align="center"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Divider(color=COR_DIVISOR, height=1),
            ft.Row([
                origem,
                destino
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=18),
            ft.Row([
                ft.Container(
                    content=ft.ElevatedButton(
                        "Selecionar Pasta de Origem",
                        on_click=selecionar_pasta_origem,
                        bgcolor=COR_BTN_PRINCIPAL,
                        color=COR_BTN_PRINCIPAL_TXT,
                        icon_color=COR_BTN_PRINCIPAL_TXT,
                        height=48,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=ft.Padding(32, 0, 32, 0)),
                        expand=True
                    ),
                    width=lambda: int(largura_card()*0.43)
                ),
                ft.Container(
                    content=ft.ElevatedButton(
                        "Selecionar Pasta de Destino",
                        on_click=selecionar_pasta_destino,
                        bgcolor=COR_BTN_PRINCIPAL,
                        color=COR_BTN_PRINCIPAL_TXT,
                        icon_color=COR_BTN_PRINCIPAL_TXT,
                        height=48,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), padding=ft.Padding(32, 0, 32, 0)),
                        expand=True
                    ),
                    width=lambda: int(largura_card()*0.43)
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=32),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=18),
        bgcolor=COR_CARD,
        border_radius=16,
        padding=28,
        margin=ft.margin.only(bottom=24),
        shadow=ft.BoxShadow(blur_radius=12, color="#00000022", offset=ft.Offset(0, 4)),
        width=lambda: largura_card()
    )

    # --- CARD DE AÇÕES ---
    def botoes_acoes():
        w = largura_responsiva()
        if w < 520:
            return ft.Column([
                ft.ElevatedButton(
                    "Extrair ZIP",
                    icon=ft.icons.FOLDER_ZIP,
                    icon_color=COR_BTN_PRINCIPAL_TXT,
                    on_click=extrair_arquivos,
                    bgcolor=COR_BTN_PRINCIPAL,
                    color=COR_BTN_PRINCIPAL_TXT,
                    height=48,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    width="100%"
                ),
                ft.ElevatedButton(
                    "Converter PDF",
                    icon=ft.icons.PICTURE_AS_PDF,
                    icon_color=COR_BTN_PRINCIPAL_TXT,
                    on_click=converter_arquivos,
                    bgcolor=COR_BTN_PRINCIPAL,
                    color=COR_BTN_PRINCIPAL_TXT,
                    height=48,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    width="100%"
                ),
                ft.ElevatedButton(
                    "Parar",
                    icon=ft.icons.STOP,
                    icon_color=COR_BTN_SECUNDARIO_TXT,
                    on_click=parar_arquivos,
                    bgcolor=COR_BTN_SECUNDARIO,
                    color=COR_BTN_SECUNDARIO_TXT,
                    height=48,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    width="100%"
                ),
                ft.ElevatedButton(
                    "Abrir Destino",
                    icon=ft.icons.FOLDER_OPEN,
                    icon_color=COR_BTN_SECUNDARIO_TXT,
                    on_click=abrir_pasta_destino,
                    bgcolor=COR_BTN_SECUNDARIO,
                    color=COR_BTN_SECUNDARIO_TXT,
                    height=48,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    width="100%"
                ),
            ], spacing=12)
        else:
            return ft.Column([
                ft.Row([
                    ft.ElevatedButton(
                        "Extrair ZIP",
                        icon=ft.icons.FOLDER_ZIP,
                        icon_color=COR_BTN_PRINCIPAL_TXT,
                        on_click=extrair_arquivos,
                        bgcolor=COR_BTN_PRINCIPAL,
                        color=COR_BTN_PRINCIPAL_TXT,
                        height=48,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        width=180
                    ),
                    ft.ElevatedButton(
                        "Converter PDF",
                        icon=ft.icons.PICTURE_AS_PDF,
                        icon_color=COR_BTN_PRINCIPAL_TXT,
                        on_click=converter_arquivos,
                        bgcolor=COR_BTN_PRINCIPAL,
                        color=COR_BTN_PRINCIPAL_TXT,
                        height=48,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        width=180
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=24),
                ft.Row([
                    ft.ElevatedButton(
                        "Parar",
                        icon=ft.icons.STOP,
                        icon_color=COR_BTN_SECUNDARIO_TXT,
                        on_click=parar_arquivos,
                        bgcolor=COR_BTN_SECUNDARIO,
                        color=COR_BTN_SECUNDARIO_TXT,
                        height=48,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        width=180
                    ),
                    ft.ElevatedButton(
                        "Abrir Destino",
                        icon=ft.icons.FOLDER_OPEN,
                        icon_color=COR_BTN_SECUNDARIO_TXT,
                        on_click=abrir_pasta_destino,
                        bgcolor=COR_BTN_SECUNDARIO,
                        color=COR_BTN_SECUNDARIO_TXT,
                        height=48,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        width=180
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=24),
            ], spacing=18)

    actions_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.BOLT, color=COR_ICONE, size=24),
                ft.Text("Ações", size=20, weight="bold", color=COR_TEXTO, text_align="center"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Divider(color=COR_DIVISOR, height=1),
            botoes_acoes()
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=18),
        bgcolor=COR_CARD,
        border_radius=16,
        padding=28,
        margin=ft.margin.only(bottom=24),
        shadow=ft.BoxShadow(blur_radius=12, color="#00000022", offset=ft.Offset(0, 4)),
        width=lambda: largura_card()
    )

    # --- CARD DE STATUS ---
    status_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.icons.INSIGHTS, color=COR_ICONE, size=24),
                ft.Text("Status", size=20, weight="bold", color=COR_TEXTO, text_align="center"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            ft.Divider(color=COR_DIVISOR, height=1),
            convertendo,
            progresso,
            status
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        bgcolor=COR_CARD,
        border_radius=16,
        padding=28,
        margin=ft.margin.only(bottom=32),
        shadow=ft.BoxShadow(blur_radius=12, color="#00000022", offset=ft.Offset(0, 4)),
        width=lambda: largura_card()
    )

    # --- LAYOUT PRINCIPAL ---
    return ft.Column([
        ft.Row([
            ft.Container(
                content=ft.Column([
                    header,
                    config_card,
                    actions_card,
                    status_card
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                alignment=ft.alignment.center,
                expand=True,
            )
        ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    ], scroll="auto", expand=True)