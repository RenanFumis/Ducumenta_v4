#!/usr/bin/env python3
"""
Exemplo de uso da funcionalidade de limite de tamanho de arquivos
"""

import asyncio
from pathlib import Path
from viewmodel.converter_vm import ConversorViewModel

async def exemplo_limite_tamanho():
    """Demonstra como configurar e usar o limite de tamanho"""
    
    # Cria instância do ViewModel
    vm = ConversorViewModel()
    
    # Configura o tamanho máximo (em GB)
    print("=== Configuração de Tamanho Máximo ===")
    
    # Exemplo 1: Limite padrão (1GB)
    print(f"Tamanho máximo padrão: {vm.obter_tamanho_maximo()}GB")
    
    # Exemplo 2: Configurar para 2GB
    vm.configurar_tamanho_maximo(2)
    print(f"Tamanho máximo configurado: {vm.obter_tamanho_maximo()}GB")
    
    # Exemplo 3: Configurar para 500MB
    vm.configurar_tamanho_maximo(0.5)
    print(f"Tamanho máximo configurado: {vm.obter_tamanho_maximo()}GB")
    
    # Exemplo 4: Voltar para o padrão
    vm.configurar_tamanho_maximo(1)
    print(f"Tamanho máximo configurado: {vm.obter_tamanho_maximo()}GB")
    
    print("\n=== Processo de Conversão com Limite ===")
    
    # Simula uma conversão (substitua pelos caminhos reais)
    origem = Path("pasta_origem")
    destino = Path("pasta_destino")
    
    if origem.exists():
        print(f"Convertendo arquivos de: {origem}")
        print(f"Para: {destino}")
        print(f"Tamanho máximo por arquivo: {vm.obter_tamanho_maximo()}GB")
        
        # Função de callback para status
        def atualizar_status(mensagem, erro=None):
            if erro:
                print(f"❌ Erro: {erro}")
            else:
                print(f"ℹ️  {mensagem}")
        
        # Executa a conversão
        try:
            total_processado, erros = await vm.converter(origem, destino, atualizar_status)
            print(f"\n✅ Conversão concluída!")
            print(f"📊 Arquivos processados: {total_processado}")
            print(f"⚠️  Erros encontrados: {len(erros)}")
            
            if erros:
                print("\n📋 Lista de erros:")
                for erro in erros[:5]:  # Mostra apenas os primeiros 5 erros
                    print(f"   • {erro}")
                if len(erros) > 5:
                    print(f"   • ... e mais {len(erros) - 5} erros")
                    
        except Exception as e:
            print(f"❌ Falha na conversão: {e}")
    else:
        print("⚠️  Pasta de origem não encontrada. Crie a pasta 'pasta_origem' com arquivos para testar.")

def exemplo_configuracao_avancada():
    """Demonstra configurações avançadas"""
    
    print("\n=== Configurações Avançadas ===")
    
    # Diferentes cenários de uso
    cenarios = [
        ("Arquivos pequenos (emails)", 0.1),  # 100MB
        ("Documentos padrão", 1),              # 1GB
        ("Arquivos grandes", 5),               # 5GB
        ("Sem limite", 100)                    # 100GB (praticamente sem limite)
    ]
    
    for nome, tamanho in cenarios:
        vm = ConversorViewModel()
        vm.configurar_tamanho_maximo(tamanho)
        print(f"📁 {nome}: {vm.obter_tamanho_maximo()}GB")

if __name__ == "__main__":
    print("🚀 Exemplo de Uso - Limite de Tamanho de Arquivos")
    print("=" * 60)
    
    # Executa exemplos
    asyncio.run(exemplo_limite_tamanho())
    exemplo_configuracao_avancada()
    
    print("\n" + "=" * 60)
    print("📚 Para mais informações, consulte LIMITE_TAMANHO.md")
    print("🎯 O sistema automaticamente:")
    print("   • Verifica o tamanho dos arquivos")
    print("   • Otimiza imagens com compressão progressiva")
    print("   • Recomprime PDFs quando necessário")
    print("   • Divide arquivos muito grandes em partes")
    print("   • Gera logs detalhados do processo") 