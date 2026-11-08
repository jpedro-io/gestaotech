"""Preenche o DOCX modelo, gera o QR Code e devolve o PDF (só a página 1)."""
import io
import os
import re
import shutil
import subprocess
import tempfile
import threading
from datetime import date
from functools import lru_cache
from pathlib import Path

import qrcode
from django.conf import settings
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Mm
from docx.text.paragraph import Paragraph
from pypdf import PdfReader, PdfWriter

MODELOS = {
    "OUVINTE": "ouvinte.docx",
    "MINISTRANTE": "ministrante.docx",
    "ORGANIZADOR": "organizador.docx",
}
TAG = re.compile(r"\(\(([A-Z_]+)\)\)")
_slot = threading.BoundedSemaphore(2)   # no máximo 2 conversões simultâneas


def _substituir(par, valores):
    """Troca ((TAG)) mesmo quando o Word a quebrou em vários 'runs'."""
    while True:
        runs = par.runs
        texto = "".join(r.text for r in runs)
        m = TAG.search(texto)
        if not m:
            return
        valor = valores[m.group(1)]          # tag desconhecida → KeyError
        ini, fim = m.span()
        pos, primeiro = 0, True
        for r in runs:
            r_ini, r_fim = pos, pos + len(r.text)
            pos = r_fim
            if r_fim <= ini or r_ini >= fim:
                continue
            a, b = max(ini, r_ini) - r_ini, min(fim, r_fim) - r_ini
            r.text = r.text[:a] + (valor if primeiro else "") + r.text[b:]
            primeiro = False


def _processar(par, valores, qr_png):
    texto = "".join(r.text for r in par.runs)
    if "((QRCODE))" in texto:
        _substituir(par, {**valores, "QRCODE": ""})
        par.add_run().add_picture(io.BytesIO(qr_png), width=Mm(25))
    else:
        _substituir(par, valores)


def _todos_os_paragrafos(doc):
    raizes = [doc.element.body]
    for s in doc.sections:
        raizes += [s.header._element, s.footer._element]
    for raiz in raizes:
        for p in raiz.iter(qn("w:p")):      # inclui tabelas e caixas de texto
            yield Paragraph(p, doc._body)


def _qr_png(url):
    buf = io.BytesIO()
    qrcode.make(url, box_size=10, border=1).save(buf, format="PNG")
    return buf.getvalue()


def _caminhos_windows():
    """Locais onde o instalador do LibreOffice coloca o soffice.exe."""
    if os.name != "nt":
        return []
    bases = [os.environ.get("ProgramFiles", r"C:\Program Files"),
             os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
             os.environ.get("LOCALAPPDATA", "")]
    return [os.path.join(b, "LibreOffice", "program", "soffice.exe")
            for b in bases if b]


def _soffice():
    """Caminho do LibreOffice: SOFFICE_BIN no .env, o do PATH ou o padrão do Windows."""
    configurado = (os.environ.get("SOFFICE_BIN") or "").strip().strip('"')
    if configurado and os.path.exists(configurado):
        return configurado
    achado = shutil.which("soffice") or shutil.which("libreoffice")
    if achado:
        return achado
    for candidato in _caminhos_windows():
        if os.path.exists(candidato):
            return candidato
    return None


def _docx_para_pdf(docx_bytes):
    with tempfile.TemporaryDirectory() as tmp, _slot:
        entrada = Path(tmp) / "cert.docx"
        entrada.write_bytes(docx_bytes)
        exe = _soffice()
        if not exe:
            raise RuntimeError(
                "LibreOffice não encontrado. Instale o LibreOffice ou defina "
                "SOFFICE_BIN no .env (ex.: C:/Program Files/LibreOffice/program/soffice.exe).")
        subprocess.run(
            [exe, f"-env:UserInstallation=file://{tmp}/perfil",
             "--headless", "--convert-to", "pdf", "--outdir", tmp, str(entrada)],
            check=True, timeout=settings.LIBREOFFICE_TIMEOUT, capture_output=True,
        )
        return (Path(tmp) / "cert.pdf").read_bytes()


def _so_primeira_pagina(pdf_bytes):
    leitor = PdfReader(io.BytesIO(pdf_bytes))
    saida = PdfWriter()
    saida.add_page(leitor.pages[0])
    buf = io.BytesIO()
    saida.write(buf)
    return buf.getvalue()


@lru_cache(maxsize=64)   # o mesmo certificado sempre sai igual; evita reconverter
def _gerar(codigo, nome, oficina, papel, cpf_parcial, emitido_em):
    site = settings.SITE_URL.rstrip("/")
    valores = {
        "NOME": nome,
        "CPF": cpf_parcial,
        "OFICINA": oficina,
        "CODIGO": codigo,
        "DATA_EMISSAO": emitido_em,
        "URL_VALIDACAO": site.replace("https://", "").replace("http://", "") + "/validar",
        "QRCODE": "",
    }
    qr = _qr_png(f"{site}/validar/{codigo}/")

    doc = Document(Path(settings.BASE_DIR) / "modelos_docx" / MODELOS[papel])
    for par in _todos_os_paragrafos(doc):
        _processar(par, valores, qr)

    buf = io.BytesIO()
    doc.save(buf)
    return _so_primeira_pagina(_docx_para_pdf(buf.getvalue()))


def gerar_pdf(p):
    emitido = p.get("emitido_em") or date.today()
    if not isinstance(emitido, str):
        emitido = emitido.strftime("%d/%m/%Y")
    return _gerar(p["codigo"], p["nome"], p["oficina"], p["papel"],
                  p["cpf_parcial"], emitido)
