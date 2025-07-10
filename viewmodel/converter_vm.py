import os
import time
import asyncio
from model.converter import ConversorModel, extrair_todos_zips
from datetime import datetime
from pathlib import Path

class ConversorViewModel:
    def __init__(self):
        self.parar = False
        self.status_atual = ""
        self.erro_atual = None
        self.tamanho_maximo_gb = 1  # Tamanho máximo em GB (padrão: 1GB)

    def atualizar_status(self, mensagem, erro=None):
        """Atualiza o status atual do processamento"""
        self.status_atual = mensagem
        self.erro_atual = erro

    async def extrair_arquivos(self, caminho_origem, callback_status=None):
        """Extrai arquivos compactados"""
        try:
            erros = extrair_todos_zips(caminho_origem, callback_status)
            return len(erros) == 0, erros
        except Exception as e:
            return False, [str(e)]

    async def converter(self, origem, destino, callback_status=None):
        """Inicia o processo de conversão"""
        try:
            self.parar = False
            tamanho_maximo = self.tamanho_maximo_gb * 1024 * 1024 * 1024  # Converte GB para bytes
            return await ConversorModel.converter_para_pdf(
                origem, destino, callback_status, self.parar, tamanho_maximo
            )
        except Exception as e:
            return (0, [str(e)])

    def parar_conversao(self):
        """Para o processo de conversão"""
        self.parar = True

    def configurar_tamanho_maximo(self, tamanho_gb):
        """Configura o tamanho máximo dos arquivos em GB"""
        if tamanho_gb > 0:
            self.tamanho_maximo_gb = tamanho_gb
            return True
        return False

    def obter_tamanho_maximo(self):
        """Retorna o tamanho máximo configurado em GB"""
        return self.tamanho_maximo_gb

def iniciar_conversao(origem, destino, callback_status=None):
    """Função auxiliar para iniciar a conversão em uma thread separada"""
    vm = ConversorViewModel()
    asyncio.run(vm.converter(origem, destino, callback_status))

def iniciar_extracao(origem, callback_status=None):
    """Função auxiliar para iniciar a extração em uma thread separada"""
    vm = ConversorViewModel()
    asyncio.run(vm.extrair_arquivos(origem, callback_status))

def parar_conversao(vm):
    """Função auxiliar para parar a conversão"""
    if vm:
        vm.parar_conversao()