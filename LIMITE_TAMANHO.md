# Limite de Tamanho de Arquivos - Conversor de Documentos

## Visão Geral

O sistema agora inclui controle automático de tamanho de arquivos para garantir que nenhum arquivo PDF gerado exceda 1GB (configurável).

## Funcionalidades Implementadas

### 1. Verificação Automática de Tamanho
- Todos os arquivos são verificados antes e após a conversão
- Arquivos que excedem o limite são automaticamente otimizados

### 2. Otimização Inteligente
- **Imagens**: Redimensionamento e compressão progressiva
- **PDFs**: Recompressão com configurações otimizadas
- **Qualidade Adaptativa**: Ajusta automaticamente a qualidade para manter o tamanho

### 3. Divisão de Arquivos Grandes
- PDFs muito grandes são divididos em múltiplas partes
- Cada parte mantém a estrutura original do documento
- Nomenclatura automática: `arquivo_parte1.pdf`, `arquivo_parte2.pdf`, etc.

### 4. Configuração Flexível
- Tamanho máximo padrão: 1GB
- Configurável via ViewModel
- Suporte para diferentes unidades (GB, MB)

## Como Funciona

### Processo de Conversão
1. **Verificação Inicial**: Analisa o tamanho do arquivo original
2. **Otimização Prévia**: Se necessário, otimiza antes da conversão
3. **Conversão**: Executa a conversão normal
4. **Verificação Final**: Confirma se o PDF gerado está dentro do limite
5. **Otimização Pós-Processamento**: Se necessário, otimiza o PDF final
6. **Divisão**: Como último recurso, divide arquivos muito grandes

### Estratégias de Otimização

#### Para Imagens:
- Redimensionamento para máximo 4000x4000 pixels
- Compressão JPEG progressiva (70% → 60% → 50% → 40% → 30% → 20%)
- Conversão para RGB se necessário

#### Para PDFs:
- Recompressão com configurações otimizadas
- Remoção de metadados desnecessários
- Divisão em partes menores se necessário

## Configuração

### Via Código
```python
# No ViewModel
vm = ConversorViewModel()
vm.configurar_tamanho_maximo(2)  # 2GB
```

### Constantes do Sistema
```python
# No modelo (model/converter.py)
MAX_TAMANHO_ARQUIVO_PADRAO = 1024 * 1024 * 1024  # 1GB
QUALIDADE_JPEG = 70  # Qualidade inicial para JPEG
```

## Logs e Monitoramento

O sistema gera logs detalhados:
- `[INFO]` - Operações bem-sucedidas
- `[AVISO]` - Arquivos que excedem o limite
- `[ERRO]` - Falhas na otimização

### Exemplos de Logs:
```
[AVISO] Arquivo imagem_grande.jpg excede 1GB (1.5GB)
[INFO] Arquivo otimizado com qualidade 50%: 0.8GB
[INFO] PDF otimizado com sucesso: 0.9GB
[INFO] PDF dividido em 3 partes
```

## Benefícios

1. **Compatibilidade**: Garante que arquivos funcionem em qualquer sistema
2. **Performance**: Arquivos menores carregam mais rápido
3. **Armazenamento**: Economiza espaço em disco
4. **Transmissão**: Facilita envio por email ou upload
5. **Flexibilidade**: Configuração adaptável às necessidades

## Tratamento de Erros

- Arquivos que não podem ser otimizados geram erro específico
- Logs detalhados para debugging
- Relatórios de erro incluem informações sobre arquivos problemáticos

## Compatibilidade

- Funciona com todos os formatos suportados
- Mantém qualidade visual aceitável
- Preserva estrutura dos documentos
- Compatível com sistemas de arquivos existentes 