import flet as ft
import os
from view.ui import criar_interface
from viewmodel.converter_vm import ConversorViewModel

def main(page: ft.Page):
    page.title = "Documenta - Conversor de Documentos"
    
    # Configurações da janela para o novo layout
    page.window_width = 500
    page.window_height = 700
    page.window_resizable = True
    page.window_min_width = 450
    page.window_min_height = 600
    page.bgcolor = "#121212"
    page.theme_mode = ft.ThemeMode.DARK

    # Atualiza a página para aplicar as configurações
    page.update()

    # Inicializa o ViewModel e a interface
    vm = ConversorViewModel()
    page.add(criar_interface(page, vm))

    def on_close(e):
        print("Fechando a aplicação...")
        page.window_destroy()
        os._exit(0)

    # Define o evento de fechamento
    page.on_close = on_close

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")