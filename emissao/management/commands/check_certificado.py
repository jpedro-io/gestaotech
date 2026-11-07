"""Diagnóstico: o servidor consegue gerar o PDF? (LibreOffice + fontes + modelos)"""
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from emissao.certificado import _soffice


class Command(BaseCommand):
    help = "Verifica LibreOffice, fontes e modelos antes de publicar o site."

    def handle(self, *args, **opts):
        ok = True
        soffice = _soffice()
        if soffice:
            self.stdout.write(self.style.SUCCESS(f"[ok] LibreOffice: {soffice}"))
        else:
            ok = False
            self.stdout.write(self.style.ERROR(
                "[erro] LibreOffice não encontrado. Instale o pacote ou defina "
                "SOFFICE_BIN no .env (ex.: C:\\Program Files\\LibreOffice\\program\\soffice.exe)."))

        modelos = ["ouvinte.docx", "ministrante.docx", "organizador.docx"]
        for nome in modelos:
            caminho = settings.BASE_DIR / "modelos_docx" / nome
            if caminho.exists():
                self.stdout.write(self.style.SUCCESS(f"[ok] modelo {nome}"))
            else:
                ok = False
                self.stdout.write(self.style.ERROR(f"[erro] modelo ausente: {caminho}"))

        fontes = sorted((settings.BASE_DIR / "fontes").glob("*.ttf"))
        self.stdout.write(f"[info] {len(fontes)} arquivo(s) de fonte em fontes/")
        if not fontes:
            self.stdout.write(self.style.WARNING(
                "[aviso] sem os .ttf o PDF sai com tipografia substituta."))

        self.stdout.write(f"[info] SOFFICE_BIN={settings.__dict__.get('SOFFICE_BIN', '')!r} | "
                          f"LibreOffice no PATH: {shutil.which('soffice') or shutil.which('libreoffice') or 'não'}")
        if ok:
            self.stdout.write(self.style.SUCCESS("Pronto: o download de PDF deve funcionar."))
        else:
            self.stdout.write(self.style.ERROR("Corrija os itens acima antes de publicar."))
