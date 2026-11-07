"""Cria/atualiza as 7 oficinas do projeto. Idempotente."""
from django.core.management.base import BaseCommand

from certificados.dados_oficinas import OFICINAS
from certificados.models import Oficina


class Command(BaseCommand):
    help = "Cadastra as oficinas do Gestão Tech (pode rodar quantas vezes quiser)."

    def handle(self, *args, **options):
        criadas = atualizadas = 0
        for nome, equipe, _pessoas in OFICINAS:
            obj, nova = Oficina.objects.get_or_create(nome=nome, defaults={"equipe": equipe})
            if nova:
                criadas += 1
            elif obj.equipe != equipe:
                obj.equipe = equipe
                obj.save(update_fields=["equipe"])
                atualizadas += 1
        self.stdout.write(self.style.SUCCESS(
            f"Oficinas: {criadas} criada(s), {atualizadas} atualizada(s), "
            f"{Oficina.objects.count()} no banco."))
