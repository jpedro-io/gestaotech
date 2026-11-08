"""Cadastra uma pessoa sem precisar montar CSV.

    python manage.py add_participante --nome "Fulano de Tal" --cpf 123.456.789-09 \
        --oficina notion --papel OUVINTE

- valida o CPF (dígito verificador) antes de gravar;
- acha a oficina pelo nome (aceita trecho, sem diferenciar maiúsculas);
- se a pessoa já existir naquela oficina/papel, atualiza em vez de duplicar;
- mostra o código de validação gerado.
"""
from django.core.management.base import BaseCommand, CommandError

from certificados.models import Oficina, Participacao, hash_cpf, meio_cpf
from emissao.cpf import normalizar, valido


class Command(BaseCommand):
    help = "Cadastra ou atualiza uma participação (uma pessoa por vez)."

    def add_arguments(self, parser):
        parser.add_argument("--nome", required=True)
        parser.add_argument("--cpf", required=True)
        parser.add_argument("--oficina", required=True,
                            help="nome (ou trecho) da oficina; use TODAS para todas")
        parser.add_argument("--papel", default="OUVINTE",
                            help="OUVINTE (padrão), MINISTRANTE ou ORGANIZADOR")
        parser.add_argument("--seco", action="store_true", help="não grava, só mostra o que faria")

    def handle(self, *args, **o):
        nome = " ".join(o["nome"].split())
        cpf = normalizar(o["cpf"])
        papel = (o["papel"] or "OUVINTE").strip().upper()

        if not valido(cpf):
            raise CommandError(f"CPF inválido: {o['cpf']}")
        if papel not in Participacao.Papel.values:
            raise CommandError(f"Papel inválido: {papel}. Use OUVINTE, MINISTRANTE ou ORGANIZADOR.")

        alvo = o["oficina"].strip()
        if alvo.upper() in {"TODAS", "TODOS", "*"}:
            destinos = list(Oficina.objects.all())
        else:
            destinos = list(Oficina.objects.filter(nome__icontains=alvo))
            if not destinos:
                nomes = "\n  - ".join(Oficina.objects.values_list("nome", flat=True))
                raise CommandError(f"Nenhuma oficina com '{alvo}'. Disponíveis:\n  - {nomes}")
            if len(destinos) > 1:
                nomes = "\n  - ".join(d.nome for d in destinos)
                raise CommandError(f"'{alvo}' casa com mais de uma oficina:\n  - {nomes}\n"
                                   f"Use um trecho mais específico.")

        for oficina in destinos:
            existente = (Participacao.objects
                         .filter(oficina=oficina, papel=papel)
                         .filter(cpf_hash=hash_cpf(cpf)).first()
                         or Participacao.objects.filter(oficina=oficina, nome=nome).first())
            acao = "atualizada" if existente else "criada"
            if o["seco"]:
                self.stdout.write(f"[seco] {nome} · {oficina.nome} · {papel} → {acao}")
                continue
            if existente:
                existente.nome = nome
                existente.cpf_hash, existente.cpf_meio = hash_cpf(cpf), meio_cpf(cpf)
                existente.save(update_fields=["nome", "cpf_hash", "cpf_meio"])
                p = existente
            else:
                p = Participacao.objects.create(
                    nome=nome, oficina=oficina, papel=papel,
                    cpf_hash=hash_cpf(cpf), cpf_meio=meio_cpf(cpf))
            self.stdout.write(self.style.SUCCESS(
                f"{acao}: {p.nome} · {oficina.nome} · {papel} · CPF {p.cpf_parcial} · {p.codigo}"))
