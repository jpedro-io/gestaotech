"""Recria o código de validação das participações que estiverem sem código."""
from django.core.management.base import BaseCommand

from certificados.models import Participacao, gerar_codigo


class Command(BaseCommand):
    help = "Gera códigos de validação únicos que estejam faltando."

    def handle(self, *args, **options):
        n = 0
        for p in Participacao.objects.filter(codigo=""):
            p.codigo = gerar_codigo()
            p.save(update_fields=["codigo"])
            n += 1
        self.stdout.write(self.style.SUCCESS(f"{n} código(s) gerado(s)."))
