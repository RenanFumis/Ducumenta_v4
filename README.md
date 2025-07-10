# Documenta - Conversor de Documentos v3.0

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flet](https://img.shields.io/badge/Flet-0.20+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Descrição

**Esse software** é um conversor de documentos desktop desenvolvido em Python com interface moderna usando Flet. O sistema converte automaticamente arquivos de imagem, PDF e documentos Word para PDF, com recursos avançados de otimização e controle de tamanho.

## ✨ Funcionalidades

### 🔄 Conversão Inteligente
- **Imagens**: JPG, JPEG, PNG, BMP, GIF, TIFF → PDF
- **Documentos**: DOC, DOCX → PDF
- **PDFs**: Otimização e divisão de arquivos grandes
- **Arquivos compactados**: Extração automática de ZIP

### 🎯 Controle de Tamanho
- **Limite configurável** por arquivo (padrão: 1GB)
- **Otimização automática** de imagens com compressão progressiva
- **Divisão inteligente** de PDFs muito grandes
- **Compressão avançada** de documentos

### 🛡️ Tratamento de Erros
- **Detecção de arquivos protegidos** por senha
- **Relatórios detalhados** de erros e arquivos não processados
- **Logs completos** do processo de conversão
- **Recuperação automática** de falhas

### 🎨 Interface Moderna
- **Design responsivo** que se adapta ao tamanho da tela
- **Tema escuro** elegante e profissional
- **Feedback em tempo real** do progresso
- **Controles intuitivos** para iniciar/parar conversão

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/documenta-conversor.git
cd documenta-conversor
```

2. **Crie um ambiente virtual:**
```bash
python -m venv venv
```

3. **Ative o ambiente virtual:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

5. **Execute a aplicação:**
```bash
python main.py
```

## 📁 Estrutura do Projeto

```
documenta-conversor/
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
├── README.md              # Documentação
├── LIMITE_TAMANHO.md      # Guia de controle de tamanho
├── assets/                # Recursos visuais
│   ├── icon.svg          # Ícone da aplicação
│   ├── Logo-Documenta.png # Logo
│   └── styles.css        # Estilos (não usado)
├── model/                 # Camada de modelo
│   ├── __init__.py
│   └── converter.py      # Lógica de conversão
├── view/                  # Camada de visualização
│   ├── __init__.py
│   └── ui.py            # Interface do usuário
└── viewmodel/            # Camada de ViewModel
    ├── __init__.py
    └── converter_vm.py  # Lógica de apresentação
```

## 🎮 Como Usar

### Interface Gráfica
1. **Execute** `python main.py`
2. **Selecione** a pasta de origem com os arquivos
3. **Selecione** a pasta de destino para os PDFs
4. **Clique** em "Converter para PDF"
5. **Aguarde** o processamento completo

### Configuração de Tamanho
O sistema permite configurar o tamanho máximo dos arquivos:

```python
from viewmodel.converter_vm import ConversorViewModel

vm = ConversorViewModel()
vm.configurar_tamanho_maximo(2)  # 2GB por arquivo
```

## 🔧 Tecnologias Utilizadas

- **Python 3.8+**: Linguagem principal
- **Flet**: Framework para interface desktop
- **Pillow (PIL)**: Processamento de imagens
- **PyPDFium2**: Manipulação de PDFs
- **python-docx2pdf**: Conversão de documentos Word
- **ReportLab**: Geração de PDFs
- **asyncio**: Processamento assíncrono

## 💿 Build e Deploy

> 📹 **Tutorial em Vídeo**: Para um guia visual completo sobre como fazer o build e deploy, assista ao [tutorial no YouTube](https://www.youtube.com/watch?v=1c9sjrWlph4&list=PLgS4VrQ-6kzeGC8DpPAP26WF0BANgGpiV&index=3).

### Compilação para Executável (PyInstaller)

Para criar um executável standalone:

```bash
# Instalar PyInstaller
pip install pyinstaller

# Compilar para Windows
pyinstaller --onefile --windowed --icon=assets/icon.ico --add-data "assets;assets" main.py

# Compilar para Linux/Mac
pyinstaller --onefile --windowed --icon=assets/icon.svg --add-data "assets:assets" main.py
```

### Build com Flet Pack

Para criar um pacote otimizado com Flet:

```bash
# Instalar Flet CLI
pip install flet-core

# Criar pacote
flet pack main.py --icon assets/icon.svg
```

### Estrutura de Build

Após a compilação, você encontrará:

```
dist/
├── main.exe          # Executável Windows
├── main              # Executável Linux/Mac
└── assets/           # Recursos incluídos
    ├── icon.svg
    ├── Logo-Documenta.png
    └── styles.css
```

### Configurações de Build

#### PyInstaller Options:
- `--onefile`: Cria um único arquivo executável
- `--windowed`: Não mostra console (Windows)
- `--icon`: Define o ícone da aplicação
- `--add-data`: Inclui arquivos de recursos

#### Flet Pack Options:
- `--icon`: Define o ícone da aplicação
- `--name`: Define o nome do executável
- `--product-name`: Define o nome do produto

### Distribuição

1. **Windows**: Distribua o arquivo `main.exe`
2. **Linux**: Distribua o arquivo `main` (sem extensão)
3. **Mac**: Distribua o arquivo `main` ou crie um `.app`

### Requisitos de Sistema

- **Windows**: Windows 10 ou superior
- **Linux**: Ubuntu 18.04+ ou similar
- **Mac**: macOS 10.14+ (Mojave ou superior)
- **RAM**: Mínimo 2GB, recomendado 4GB+
- **Espaço**: 100MB para instalação

## 📊 Recursos Avançados

### Controle de Tamanho
- **Verificação automática** do tamanho dos arquivos
- **Otimização progressiva** com diferentes qualidades
- **Divisão inteligente** de arquivos muito grandes
- **Compressão avançada** de PDFs

### Tratamento de Erros
- **Arquivos protegidos**: Movidos para pasta separada
- **Arquivos corrompidos**: Relatados com detalhes
- **Formatos não suportados**: Listados no relatório
- **Falhas de conversão**: Logs detalhados

### Performance
- **Processamento paralelo** com semáforos
- **Limpeza automática** de arquivos temporários
- **Progresso em tempo real** na interface
- **Interrupção segura** do processamento

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

- **Issues**: Use as [GitHub Issues](https://github.com/seu-usuario/documenta-conversor/issues)
- **Documentação**: Consulte os arquivos `.md` no projeto
- **Exemplos**: Veja o arquivo `LIMITE_TAMANHO.md` para casos de uso

## 🔄 Histórico de Versões

- **v3.0**: Interface moderna, controle de tamanho, tratamento avançado de erros
- **v2.0**: Conversão básica de documentos
- **v1.0**: Versão inicial

---

**Desenvolvido por Renan Fumis usando Python e Flet**