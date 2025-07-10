import os
import zipfile
import tarfile
import shutil
import time
import asyncio
from pathlib import Path
from PIL import Image
import pypdfium2 as pdfium
from docx2pdf import convert as docx2pdf_convert
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import tempfile

#Configurações
MAX_TAREFAS_SIMULTANEAS = 4
PAGINAS_POR_LOTE = 150
DPI_PDF = 100  # Reduzido de 150 para 100
QUALIDADE_JPEG = 70  # Reduzido de 85 para 70
MAX_TAMANHO_ARQUIVO_PADRAO = 1024 * 1024 * 1024  # 1GB em bytes

#Diretório temporário
TEMP_DIR = Path(tempfile.gettempdir()) / "flet_converter_temp"
TEMP_DIR.mkdir(exist_ok=True)

class ConversorModel:
    @staticmethod
    async def limpar_temp():
        #Aqui limpa os arquivos temporários
        for file in TEMP_DIR.glob("*"):
            try:
                file.unlink()
            except Exception as e:
                print(f"[AVISO] Falha ao limpar arquivo temporário {file}: {e}")

    @staticmethod
    async def verificar_e_otimizar_tamanho(caminho_arquivo, qualidade_inicial=70, tamanho_maximo=None):
        """Verifica o tamanho do arquivo e otimiza se necessário"""
        if tamanho_maximo is None:
            tamanho_maximo = MAX_TAMANHO_ARQUIVO_PADRAO
            
        try:
            tamanho_atual = caminho_arquivo.stat().st_size
            
            if tamanho_atual <= tamanho_maximo:
                return True  # Arquivo está dentro do limite
                
            print(f"[AVISO] Arquivo {caminho_arquivo.name} excede 1GB ({tamanho_atual / (1024**3):.2f}GB)")
            
            # Tenta otimizar com diferentes qualidades
            qualidades = [60, 50, 40, 30, 20]
            
            for qualidade in qualidades:
                if qualidade >= qualidade_inicial:
                    continue
                    
                # Cria arquivo temporário otimizado
                temp_path = TEMP_DIR / f"otimizado_{caminho_arquivo.name}"
                
                try:
                    with Image.open(caminho_arquivo) as img:
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Redimensiona se a imagem for muito grande
                        largura, altura = img.size
                        if largura > 4000 or altura > 4000:
                            # Calcula nova escala mantendo proporção
                            escala = min(4000 / largura, 4000 / altura)
                            nova_largura = int(largura * escala)
                            nova_altura = int(altura * escala)
                            img = img.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
                        
                        # Salva com qualidade reduzida
                        img.save(temp_path, 'JPEG', quality=qualidade, optimize=True)
                        
                        # Verifica se o tamanho está adequado
                        novo_tamanho = temp_path.stat().st_size
                        if novo_tamanho <= tamanho_maximo:
                            # Substitui o arquivo original
                            temp_path.replace(caminho_arquivo)
                            print(f"[INFO] Arquivo otimizado com qualidade {qualidade}%: {novo_tamanho / (1024**3):.2f}GB")
                            return True
                        else:
                            temp_path.unlink()  # Remove arquivo temporário
                            
                except Exception as e:
                    print(f"[ERRO] Falha ao otimizar com qualidade {qualidade}%: {e}")
                    if temp_path.exists():
                        temp_path.unlink()
                    continue
            
            # Se chegou aqui, não conseguiu otimizar
            print(f"[ERRO] Não foi possível otimizar {caminho_arquivo.name} para menos de 1GB")
            return False
            
        except Exception as e:
            print(f"[ERRO] Erro ao verificar tamanho do arquivo: {e}")
            return False

    @staticmethod
    async def dividir_pdf_grande(caminho_pdf, caminho_destino, tamanho_maximo=None):
        """Divide um PDF muito grande em múltiplos arquivos menores"""
        if tamanho_maximo is None:
            tamanho_maximo = MAX_TAMANHO_ARQUIVO_PADRAO
            
        try:
            pdf = pdfium.PdfDocument(caminho_pdf)
            total_paginas = len(pdf)
            
            if total_paginas <= 1:
                print(f"[AVISO] PDF tem apenas {total_paginas} página, não é possível dividir")
                return False
            
            # Calcula quantas páginas por arquivo (tentando manter cada arquivo < 1GB)
            paginas_por_arquivo = max(1, total_paginas // 2)
            
            arquivos_criados = []
            for i in range(0, total_paginas, paginas_por_arquivo):
                fim = min(i + paginas_por_arquivo, total_paginas)
                
                # Cria nome do arquivo dividido
                nome_base = caminho_destino.stem
                extensao = caminho_destino.suffix
                parte = i // paginas_por_arquivo + 1
                caminho_parte = caminho_destino.parent / f"{nome_base}_parte{parte}{extensao}"
                
                # Cria novo PDF com as páginas
                novo_pdf = pdfium.PdfDocument.new()
                paginas_para_importar = list(range(i, fim))
                novo_pdf.import_pages(pdf, paginas_para_importar)
                
                # Salva com compressão
                novo_pdf.save(caminho_parte)
                
                # Verifica tamanho
                tamanho_parte = caminho_parte.stat().st_size
                if tamanho_parte <= tamanho_maximo:
                    arquivos_criados.append(caminho_parte)
                    print(f"[INFO] Parte {parte} criada: {tamanho_parte / (1024**3):.2f}GB")
                else:
                    print(f"[AVISO] Parte {parte} ainda excede o limite: {tamanho_parte / (1024**3):.2f}GB")
                    caminho_parte.unlink()
            
            # Remove o arquivo original se as partes foram criadas com sucesso
            if arquivos_criados:
                caminho_pdf.unlink()
                print(f"[INFO] PDF dividido em {len(arquivos_criados)} partes")
                return True
            else:
                print("[ERRO] Não foi possível criar partes menores do PDF")
                return False
                
        except Exception as e:
            print(f"[ERRO] Falha ao dividir PDF: {e}")
            return False

    @staticmethod
    async def otimizar_pdf_existente(caminho_pdf, tamanho_maximo=None):
        """Tenta otimizar um PDF existente para reduzir seu tamanho"""
        if tamanho_maximo is None:
            tamanho_maximo = MAX_TAMANHO_ARQUIVO_PADRAO
            
        try:
            tamanho_original = caminho_pdf.stat().st_size
            print(f"[INFO] Tentando otimizar PDF: {tamanho_original / (1024**3):.2f}GB")
            
            # Cria arquivo temporário otimizado
            temp_path = TEMP_DIR / f"otimizado_{caminho_pdf.name}"
            
            # Abre o PDF original
            pdf = pdfium.PdfDocument(caminho_pdf)
            
            # Cria novo PDF com compressão máxima
            novo_pdf = pdfium.PdfDocument.new()
            
            # Copia páginas com compressão
            paginas_para_importar = list(range(len(pdf)))
            novo_pdf.import_pages(pdf, paginas_para_importar)
            
            # Salva com compressão máxima
            novo_pdf.save(temp_path)
            
            # Verifica se a otimização foi bem-sucedida
            if temp_path.exists():
                tamanho_otimizado = temp_path.stat().st_size
                if tamanho_otimizado <= tamanho_maximo:
                    # Substitui o arquivo original
                    temp_path.replace(caminho_pdf)
                    print(f"[INFO] PDF otimizado com sucesso: {tamanho_otimizado / (1024**3):.2f}GB")
                    return True
                else:
                    print(f"[AVISO] PDF ainda excede o limite após otimização: {tamanho_otimizado / (1024**3):.2f}GB")
                    temp_path.unlink()
                    
                    # Tenta dividir o PDF em partes menores
                    print("[INFO] Tentando dividir PDF em partes menores...")
                    if await ConversorModel.dividir_pdf_grande(caminho_pdf, caminho_pdf, tamanho_maximo):
                        return True
                    else:
                        return False
            else:
                print("[ERRO] Falha ao criar PDF otimizado")
                return False
                
        except Exception as e:
            print(f"[ERRO] Falha ao otimizar PDF: {e}")
            if 'temp_path' in locals() and temp_path.exists():
                temp_path.unlink()
            return False

    @staticmethod
    async def gerar_relatorio_erros(erros, arquivos_invalidos, arquivos_com_senha, pasta_destino):
        """Gera um relatório de erros em arquivo .txt"""
        try:
            # Cria o nome do arquivo com timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"relatorio_erros_{timestamp}.txt"
            caminho_relatorio = pasta_destino / nome_arquivo

            with open(caminho_relatorio, 'w', encoding='utf-8') as f:
                f.write("=" * 50 + "\n")
                f.write("RELATÓRIO DE ERROS E ARQUIVOS NÃO PROCESSADOS\n")
                f.write("=" * 50 + "\n\n")

                # Seção de erros de conversão
                if erros:
                    f.write("ERROS DE CONVERSÃO:\n")
                    f.write("-" * 30 + "\n")
                    for erro in erros:
                        partes = erro.split(": ", 1)
                        if len(partes) == 2:
                            nome_arquivo, mensagem_erro = partes
                            # Limpeza do motivo para casos conhecidos
                            if "Arquivo corrompido" in mensagem_erro:
                                motivo = "Arquivo corrompido"
                            else:
                                motivo = mensagem_erro
                            f.write(f"Arquivo: {nome_arquivo}\n")
                            f.write(f"Motivo: {motivo}\n")
                            f.write("-" * 30 + "\n")
                        else:
                            f.write(f"{erro}\n")
                            f.write("-" * 30 + "\n")
                    f.write("\n")

                # Seção de arquivos não suportados
                if arquivos_invalidos:
                    f.write("ARQUIVOS NÃO SUPORTADOS:\n")
                    f.write("-" * 30 + "\n")
                    for arquivo in arquivos_invalidos:
                        f.write(f"• {arquivo}\n")
                    f.write("\n")

                # Seção de arquivos com senha
                if arquivos_com_senha:
                    f.write("ARQUIVOS COM SENHA:\n")
                    f.write("-" * 30 + "\n")
                    for arquivo in arquivos_com_senha:
                        f.write(f"• {arquivo.name}\n")
                    f.write("\n")
                    f.write("Estes arquivos foram movidos para a pasta: arquivos_com_senha\n")

                # Rodapé
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Relatório gerado em: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")

            return caminho_relatorio
        except Exception as e:
            print(f"[ERRO] Falha ao gerar relatório: {e}")
            return None

    @staticmethod
    async def converter_para_pdf(origem, destino, atualizar_status=None, parar=False, tamanho_maximo=None):
        #Converte arquivos para PDF com tratamento completo de erros
        #Gera um PDF por página para arquivos multipágina (PDF, imagens multipágina, DOCX)
        #Retorna: (total_pdfs_gerados, erros_detalhados)
        
        await ConversorModel.limpar_temp()
        origem = Path(origem)
        destino = Path(destino)

        if not origem.exists():
            erro = f"Pasta de origem não existe: {origem}"
            if atualizar_status:
                atualizar_status(f"⚠️ {erro}")
            return 0, [erro]

        try:
            destino.mkdir(parents=True, exist_ok=True)
            # Cria pasta para arquivos com senha
            pasta_senha = destino / "arquivos_com_senha"
            pasta_senha.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            erro = f"Falha ao criar pasta destino {destino}: {e}"
            if atualizar_status:
                atualizar_status(f"⚠️ {erro}")
            return 0, [erro]

        #Contagem e validação de arquivos
        arquivos_para_processar = []
        arquivos_invalidos = []
        arquivos_com_senha = []
        
        for root, _, files in os.walk(origem):
            for file in files:
                caminho_arquivo = Path(root) / file
                ext = caminho_arquivo.suffix.lower()
                
                if ext in ['.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff', '.doc', '.docx']:
                    # Verifica se é um arquivo protegido
                    protegido, _ = await ConversorModel.verificar_arquivo_protegido(caminho_arquivo)
                    if protegido:
                        arquivos_com_senha.append(caminho_arquivo)
                    else:
                        arquivos_para_processar.append(caminho_arquivo)
                else:
                    arquivos_invalidos.append(caminho_arquivo.name)

        # Processa arquivos protegidos
        await ConversorModel.processar_arquivos_protegidos(arquivos_com_senha, pasta_senha, atualizar_status)

        if not arquivos_para_processar and not arquivos_com_senha:
            erro = "Nenhum arquivo suportado encontrado para conversão"
            if atualizar_status:
                atualizar_status(f"⚠️ {erro}")
            return 0, [erro]

        #Este é o processamento principal
        arquivos_processados = 0
        erros_detalhados = []
        start_time = time.time()
        semaforo = asyncio.Semaphore(MAX_TAREFAS_SIMULTANEAS)

        async def processar_arquivo(caminho_arquivo):
            nonlocal arquivos_processados, erros_detalhados
            async with semaforo:
                if parar:
                    return

                try:
                    caminho_relativo = caminho_arquivo.relative_to(origem)
                    ext = caminho_arquivo.suffix.lower()
                    
                    #Define destino com extensão .pdf
                    destino_arquivo = destino / caminho_relativo
                    destino_arquivo = destino_arquivo.with_suffix('.pdf')
                    
                    #Cria estrutura de pastas
                    try:
                        destino_arquivo.parent.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        raise Exception(f"Falha ao criar diretório: {e}")

                    #Executa conversão conforme tipo de arquivo (um PDF por página)
                    if ext == '.pdf':
                        arquivos_gerados = await ConversorModel.converter_pdf_para_paginas_individuais(caminho_arquivo, destino_arquivo, tamanho_maximo)
                    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tif', '.tiff']:
                        arquivos_gerados = await ConversorModel.converter_imagem_multipagina_para_paginas_individuais(caminho_arquivo, destino_arquivo, tamanho_maximo)
                    elif ext in ['.doc', '.docx']:
                        arquivos_gerados = await ConversorModel.converter_word_para_paginas_individuais(caminho_arquivo, destino_arquivo, tamanho_maximo)

                    #Atualiza status (incrementa pelo número de PDFs gerados)
                    arquivos_processados += arquivos_gerados
                    if atualizar_status:
                        status_msg = (
                            f"⏳ Convertendo: {caminho_arquivo.name} ({arquivos_gerados} PDFs gerados)\n"
                            f"Progresso: {arquivos_processados} PDFs criados\n"
                            f"Erros: {len(erros_detalhados)}"
                        )
                        atualizar_status(status_msg)

                except Exception as e:
                    erro_msg = f"{caminho_arquivo.name}: {type(e).__name__} - {str(e)}"
                    erros_detalhados.append(erro_msg)
                    if atualizar_status:
                        atualizar_status("", erro=erro_msg)  #Passa o erro para a interface
                    print(f"[ERRO] {erro_msg}")

        #Executa tarefas em paralelo
        tasks = [processar_arquivo(arquivo) for arquivo in arquivos_para_processar]
        await asyncio.gather(*tasks)

        #Gera relatório de erros
        if erros_detalhados or arquivos_invalidos or arquivos_com_senha:
            await ConversorModel.gerar_relatorio_erros(erros_detalhados, arquivos_invalidos, arquivos_com_senha, destino)

        #Limpa arquivos temporários
        await ConversorModel.limpar_temp()

        #Calcula tempo total e formata em HH:MM:SS
        tempo_total = time.time() - start_time
        horas = int(tempo_total // 3600)
        minutos = int((tempo_total % 3600) // 60)
        segundos = int(tempo_total % 60)
        tempo_formatado = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

        if atualizar_status:
            if erros_detalhados:
                atualizar_status(
                    f"⚠️ Conversão concluída em {tempo_formatado}\n"
                    f"Total de PDFs gerados: {arquivos_processados}\n"
                    f"Total de erros: {len(erros_detalhados)}"
                )
            else:
                atualizar_status(
                    f"✅ Conversão concluída com sucesso em {tempo_formatado}\n"
                    f"Total de PDFs gerados: {arquivos_processados}"
                )

        return arquivos_processados, erros_detalhados

    @staticmethod
    async def converter_pdf_para_paginas_individuais(caminho_origem, caminho_destino, tamanho_maximo=None):
        """Converte um PDF em múltiplos PDFs, um para cada página"""
        try:
            # Abre o PDF original
            pdf = pdfium.PdfDocument(caminho_origem)
            total_paginas = len(pdf)
            
            if total_paginas <= 1:
                # Se tem apenas uma página, converte normalmente
                await ConversorModel.ajustar_pdf(caminho_origem, caminho_destino, tamanho_maximo)
                return 1
            
            # Para múltiplas páginas, cria um PDF por página
            arquivos_criados = 0
            nome_base = caminho_destino.stem
            extensao = caminho_destino.suffix
            
            for i in range(total_paginas):
                # Cria nome do arquivo para esta página
                caminho_pagina = caminho_destino.parent / f"{nome_base}_pagina{i+1}{extensao}"
                
                # Cria novo PDF com apenas esta página
                novo_pdf = pdfium.PdfDocument.new()
                novo_pdf.import_pages(pdf, [i])
                
                # Salva com compressão
                novo_pdf.save(caminho_pagina)
                
                # Verifica se o PDF gerado não excede o limite
                if caminho_pagina.exists():
                    tamanho_pdf = caminho_pagina.stat().st_size
                    tamanho_maximo_verificar = tamanho_maximo or MAX_TAMANHO_ARQUIVO_PADRAO
                    if tamanho_pdf > tamanho_maximo_verificar:
                        print(f"[AVISO] PDF da página {i+1} excede o limite ({tamanho_pdf / (1024**3):.2f}GB)")
                        # Tenta otimizar o PDF
                        await ConversorModel.otimizar_pdf_existente(caminho_pagina, tamanho_maximo_verificar)
                    
                    arquivos_criados += 1
            
            return arquivos_criados
            
        except Exception as e:
            raise Exception(f"Falha ao converter PDF para páginas individuais: {str(e)}")

    @staticmethod
    async def converter_imagem_multipagina_para_paginas_individuais(caminho_origem, caminho_destino, tamanho_maximo=None):
        """Converte uma imagem multipágina em múltiplos PDFs, um para cada página"""
        try:
            # Verifica se o arquivo existe e tem tamanho
            if not caminho_origem.exists():
                raise Exception("Arquivo não encontrado")
            
            if caminho_origem.stat().st_size == 0:
                raise Exception("Arquivo está vazio")

            # Verifica e otimiza o tamanho da imagem antes da conversão
            otimizado = await ConversorModel.verificar_e_otimizar_tamanho(caminho_origem, QUALIDADE_JPEG, tamanho_maximo)
            if not otimizado:
                raise Exception("Imagem muito grande e não foi possível otimizar para o tamanho máximo configurado")

            try:
                with Image.open(caminho_origem) as img:
                    # Verifica se a imagem foi carregada corretamente
                    if img.size[0] == 0 or img.size[1] == 0:
                        raise Exception("Imagem inválida: dimensões zero")

                    # Verifica se é uma imagem multipágina
                    try:
                        # Tenta acessar múltiplas páginas
                        paginas = []
                        i = 0
                        while True:
                            try:
                                img.seek(i)
                                paginas.append(img.copy())
                                i += 1
                            except EOFError:
                                break
                    except:
                        # Se não conseguiu acessar múltiplas páginas, trata como imagem única
                        paginas = [img]

                    if len(paginas) <= 1:
                        # Se tem apenas uma página, converte normalmente
                        await ConversorModel.converter_imagem_para_pdf(caminho_origem, caminho_destino, tamanho_maximo)
                        return 1

                    # Para múltiplas páginas, cria um PDF por página
                    arquivos_criados = 0
                    nome_base = caminho_destino.stem
                    extensao = caminho_destino.suffix

                    for i, pagina_img in enumerate(paginas):
                        # Cria nome do arquivo para esta página
                        caminho_pagina = caminho_destino.parent / f"{nome_base}_pagina{i+1}{extensao}"

                        # Converte para RGB se necessário
                        if pagina_img.mode in ['RGBA', 'LA']:
                            background = Image.new('RGB', pagina_img.size, (255, 255, 255))
                            background.paste(pagina_img, mask=pagina_img.split()[-1])
                            pagina_img = background
                        elif pagina_img.mode != 'RGB':
                            pagina_img = pagina_img.convert('RGB')

                        # Calcula dimensões para A4
                        largura_a4, altura_a4 = A4
                        largura_img, altura_img = pagina_img.size
                        
                        # Calcula escala para caber na página
                        escala_largura = largura_a4 / largura_img
                        escala_altura = altura_a4 / altura_img
                        escala = min(escala_largura, escala_altura)
                        
                        # Calcula novas dimensões
                        nova_largura = largura_img * escala
                        nova_altura = altura_img * escala
                        
                        # Calcula posição central
                        x = (largura_a4 - nova_largura) / 2
                        y = (altura_a4 - nova_altura) / 2

                        # Cria PDF
                        buffer = io.BytesIO()
                        c = canvas.Canvas(buffer, pagesize=A4)
                        
                        # Comprime a imagem antes de adicionar ao PDF
                        img_buffer = io.BytesIO()
                        pagina_img.save(img_buffer, format='JPEG', quality=QUALIDADE_JPEG, optimize=True)
                        img_buffer.seek(0)
                        
                        c.drawImage(ImageReader(img_buffer), x, y, width=nova_largura, height=nova_altura)
                        c.save()
                        
                        # Salva PDF
                        buffer.seek(0)
                        with open(caminho_pagina, 'wb') as f:
                            f.write(buffer.getvalue())

                        # Verifica se o PDF gerado não excede o limite
                        if caminho_pagina.exists():
                            tamanho_pdf = caminho_pagina.stat().st_size
                            tamanho_maximo_verificar = tamanho_maximo or MAX_TAMANHO_ARQUIVO_PADRAO
                            if tamanho_pdf > tamanho_maximo_verificar:
                                print(f"[AVISO] PDF da página {i+1} excede o limite ({tamanho_pdf / (1024**3):.2f}GB)")
                                # Tenta otimizar o PDF
                                await ConversorModel.otimizar_pdf_existente(caminho_pagina, tamanho_maximo_verificar)
                            
                            arquivos_criados += 1

                    return arquivos_criados

            except IOError as e:
                if "cannot identify image file" in str(e).lower():
                    raise Exception("Formato de imagem não suportado ou arquivo corrompido")
                elif "permission denied" in str(e).lower():
                    raise Exception("Arquivo está sendo usado por outro programa")
                elif str(e) == "-2" or "tiff" in str(e).lower():
                    raise Exception("Arquivo corrompido")
                else:
                    raise Exception(f"Erro ao abrir imagem: {str(e)}")

        except Exception as e:
            raise Exception(f"Falha ao converter imagem multipágina para páginas individuais: {str(e)}")

    @staticmethod
    async def converter_word_para_paginas_individuais(caminho_origem, caminho_destino, tamanho_maximo=None):
        """Converte um arquivo Word em múltiplos PDFs, um para cada página"""
        try:
            # Primeiro converte o DOCX para PDF
            pdf_temp = caminho_destino.parent / f"temp_{caminho_destino.name}"
            await ConversorModel.converter_word_para_pdf(caminho_origem, pdf_temp)
            
            # Depois divide o PDF resultante em páginas individuais
            arquivos_criados = await ConversorModel.converter_pdf_para_paginas_individuais(pdf_temp, caminho_destino, tamanho_maximo)
            
            # Remove o arquivo temporário
            if pdf_temp.exists():
                pdf_temp.unlink()
            
            return arquivos_criados
            
        except Exception as e:
            raise Exception(f"Falha ao converter Word para páginas individuais: {str(e)}")

    @staticmethod
    async def converter_imagem_para_pdf(caminho_origem, caminho_destino, tamanho_maximo=None):
        #Converte uma imagem para PDF usando Pillow e ReportLab
        try:
            #Verifica se o arquivo existe e tem tamanho
            if not caminho_origem.exists():
                raise Exception("Arquivo não encontrado")
            
            if caminho_origem.stat().st_size == 0:
                raise Exception("Arquivo está vazio")

            # Verifica e otimiza o tamanho da imagem antes da conversão
            otimizado = await ConversorModel.verificar_e_otimizar_tamanho(caminho_origem, QUALIDADE_JPEG, tamanho_maximo)
            if not otimizado:
                raise Exception("Imagem muito grande e não foi possível otimizar para o tamanho máximo configurado")

            #Tenta abrir a imagem com tratamento específico para TIFF
            try:
                with Image.open(caminho_origem) as img:
                    #Verifica se a imagem foi carregada corretamente
                    if img.size[0] == 0 or img.size[1] == 0:
                        raise Exception("Imagem inválida: dimensões zero")

                    #Converte para RGB se necessário
                    if img.mode in ['RGBA', 'LA']:
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')

                    #Calcula dimensões para A4
                    largura_a4, altura_a4 = A4
                    largura_img, altura_img = img.size
                    
                    #Calcula escala para caber na página
                    escala_largura = largura_a4 / largura_img
                    escala_altura = altura_a4 / altura_img
                    escala = min(escala_largura, escala_altura)
                    
                    #Calcula novas dimensões
                    nova_largura = largura_img * escala
                    nova_altura = altura_img * escala
                    
                    #Calcula posição central
                    x = (largura_a4 - nova_largura) / 2
                    y = (altura_a4 - nova_altura) / 2

                    #Cria PDF
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A4)
                    
                    #Comprime a imagem antes de adicionar ao PDF
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='JPEG', quality=QUALIDADE_JPEG, optimize=True)
                    img_buffer.seek(0)
                    
                    c.drawImage(ImageReader(img_buffer), x, y, width=nova_largura, height=nova_altura)
                    c.save()
                    
                    #Salva PDF
                    buffer.seek(0)
                    with open(caminho_destino, 'wb') as f:
                        f.write(buffer.getvalue())

                    # Verifica se o PDF gerado não excede o limite
                    if caminho_destino.exists():
                        tamanho_pdf = caminho_destino.stat().st_size
                        tamanho_maximo_verificar = tamanho_maximo or MAX_TAMANHO_ARQUIVO_PADRAO
                        if tamanho_pdf > tamanho_maximo_verificar:
                            print(f"[AVISO] PDF gerado excede o limite ({tamanho_pdf / (1024**3):.2f}GB)")
                            # Tenta otimizar o PDF
                            await ConversorModel.otimizar_pdf_existente(caminho_destino, tamanho_maximo_verificar)

            except IOError as e:
                if "cannot identify image file" in str(e).lower():
                    raise Exception("Formato de imagem não suportado ou arquivo corrompido")
                elif "permission denied" in str(e).lower():
                    raise Exception("Arquivo está sendo usado por outro programa")
                elif str(e) == "-2" or "tiff" in str(e).lower():
                    raise Exception("Arquivo corrompido")
                else:
                    raise Exception(f"Erro ao abrir imagem: {str(e)}")

        except Exception as e:
            raise Exception(f"Falha ao converter imagem: {str(e)}")

    @staticmethod
    async def ajustar_pdf(caminho_origem, caminho_destino, tamanho_maximo=None):
        #Otimiza e ajusta PDFs existentes
        try:
            #Abre o PDF
            pdf = pdfium.PdfDocument(caminho_origem)
            
            #Cria novo PDF
            novo_pdf = pdfium.PdfDocument.new()
            
            #Copia páginas
            for i in range(len(pdf)):
                novo_pdf.import_pages(pdf, [i])
            
            #Salva otimizado com compressão
            novo_pdf.save(caminho_destino)
            
            # Verifica se o PDF otimizado não excede o limite
            if caminho_destino.exists():
                tamanho_pdf = caminho_destino.stat().st_size
                tamanho_maximo_verificar = tamanho_maximo or MAX_TAMANHO_ARQUIVO_PADRAO
                if tamanho_pdf > tamanho_maximo_verificar:
                    print(f"[AVISO] PDF otimizado ainda excede o limite ({tamanho_pdf / (1024**3):.2f}GB)")
                    # Tenta otimizar ainda mais
                    await ConversorModel.otimizar_pdf_existente(caminho_destino, tamanho_maximo_verificar)
            
        except Exception as e:
            raise Exception(f"Falha ao ajustar PDF: {str(e)}")

    @staticmethod
    async def converter_word_para_pdf(caminho_origem, caminho_destino):
        #Converte arquivos Word para PDF
        try:
            docx2pdf_convert(caminho_origem, caminho_destino)
        except Exception as e:
            raise Exception(f"Falha ao converter Word: {str(e)}")

    @staticmethod
    async def verificar_arquivo_protegido(caminho_arquivo):
        #Verifica se um arquivo está protegido por senha
        try:
            if caminho_arquivo.suffix.lower() == '.pdf':
                pdf = pdfium.PdfDocument(caminho_arquivo)
                return False, None
            return False, None
        except Exception as e:
            if "password" in str(e).lower():
                return True, str(e)
            return False, None

    @staticmethod
    async def mover_arquivo_protegido(arquivo, pasta_destino):
        #Move um arquivo protegido para a pasta de destino
        try:
            destino = pasta_destino / arquivo.name
            shutil.copy2(arquivo, destino)
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao mover arquivo protegido {arquivo}: {e}")
            return False

    @staticmethod
    async def processar_arquivos_protegidos(arquivos, pasta_destino, atualizar_status=None):
        #Processa arquivos protegidos por senha
        if not arquivos:
            return

        for arquivo in arquivos:
            if await ConversorModel.mover_arquivo_protegido(arquivo, pasta_destino):
                if atualizar_status:
                    atualizar_status(f"⚠️ Arquivo com senha movido: {arquivo.name}")

def extrair_todos_zips(caminho_origem, atualizar_status=None):
    #Extrai todos os arquivos ZIP encontrados
    caminho_origem = Path(caminho_origem)
    arquivos_processados = 0
    erros = []

    for root, _, files in os.walk(caminho_origem):
        for file in files:
            if file.lower().endswith('.zip'):
                try:
                    caminho_arquivo = Path(root) / file
                    pasta_destino = caminho_arquivo.parent / caminho_arquivo.stem
                    
                    #Cria pasta de destino
                    pasta_destino.mkdir(parents=True, exist_ok=True)
                    
                    #Extrai arquivo
                    with zipfile.ZipFile(caminho_arquivo, 'r') as zip_ref:
                        zip_ref.extractall(pasta_destino)
                    
                    arquivos_processados += 1
                    if atualizar_status:
                        atualizar_status(f"✅ Extraído: {file}")

                except Exception as e:
                    erro = f"{file}: {str(e)}"
                    erros.append(erro)
                    if atualizar_status:
                        atualizar_status("", erro=erro)

    if atualizar_status:
        if erros:
            atualizar_status(f"⚠️ Extração concluída com {len(erros)} erros")
        else:
            atualizar_status(f"✅ Extração concluída com sucesso")

    return arquivos_processados, erros