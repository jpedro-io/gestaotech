"""Exporta as participações para CSV (nome, cpf não é exportado, oficina, papel, código)."""
import csv

from django.core.management.base import BaseCommand

from certificados.models import Participacao


class Command(BaseCommand):
    help = "Gera um CSV com nome, oficina, papel e código (sem CPF)."

    def add_arguments(self, parser):
        parser.add_argument("--saida", default="participacoes.csv")

    def handle(self, *args, **options):
        with open(options["saida"], "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["nome", "oficina", "papel", "codigo", "cpf_parcial", "revogado"])
            for p in Participacao.objects.select_related("oficina").order_by("nome"):
                w.writerow([p.nome, p.oficina.nome, p.papel, p.codigo,
                            p.cpf_parcial, "sim" if p.revogado else "não"])
        self.stdout.write(self.style.SUCCESS(f"CSV salvo em {options['saida']}"))
