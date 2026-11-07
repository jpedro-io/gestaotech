"""Cadastra a equipe de cada oficina como participação.

Como os CPFs ainda não foram informados, o comando aceita um CSV opcional:

    python manage.py seed_participantes --csv pessoas.csv

Formato do CSV (cabeçalho obrigatório):
    nome,cpf,oficina,papel
    João Pedro Campos Rocha,12345678909,Workspace Integrado: ...,MINISTRANTE

`oficina` aceita `TODAS` (ou `*`) para quem participou de todas as oficinas —
nesse caso é criada uma participação por oficina, cada uma com seu código:

    Maria Luiza Santos Rocha Granja,03315106509,TODAS,OUVINTE

Sem `--csv`, ele apenas cria/atualiza as participações que ainda não existem,
com `cpf_hash` vazio — e avisa quantas pessoas faltam informar o CPF.
"""
import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from certificados.dados_oficinas import NOMES_INCOMPLETOS, pessoas_por_oficina
from certificados.models import Oficina, Participacao, hash_cpf, meio_cpf
from emissao.cpf import normalizar, valido


class Command(BaseCommand):
    help = "Cadastra as participações (nome, CPF, oficina, papel)."

    def add_arguments(self, parser):
        parser.add_argument("--csv", help="CSV com nome,cpf,oficina,papel")
        parser.add_argument("--atualizar-nomes", action="store_true",
                            help="sobrescreve o nome de um registro já existente")

    def handle(self, *args, **options):
        if options["csv"]:
            return self._por_csv(Path(options["csv"]), options["atualizar_nomes"])
        return self._pelo_catalogo()

    # ── carga a partir do catálogo (sem CPF ainda) ─────────────────────────
    def _pelo_catalogo(self):
        criadas = 0
        for nome_oficina, nome, papel in pessoas_por_oficina():
            oficina = Oficina.objects.get(nome=nome_oficina)
            existe = Participacao.objects.filter(oficina=oficina, nome=nome).first()
            if existe:
                if existe.papel != papel:
                    existe.papel = papel
                    existe.save(update_fields=["papel"])
                continue
            Participacao.objects.create(nome=nome, oficina=oficina, papel=papel,
                                        cpf_hash="", cpf_meio="")
            criadas += 1

        sem_cpf = Participacao.objects.filter(cpf_hash="").count()
        self.stdout.write(self.style.SUCCESS(
            f"{criadas} participação(ões) criada(s); {Participacao.objects.count()} no banco."))
        if sem_cpf:
            self.stdout.write(self.style.WARNING(
                f"{sem_cpf} pessoa(s) ainda sem CPF — elas não conseguem emitir enquanto o CPF "
                f"não for importado (use --csv). Nomes curtos pendentes: "
                + ", ".join(sorted(NOMES_INCOMPLETOS))))

    # ── carga/atualização por CSV ──────────────────────────────────────────
    def _por_csv(self, caminho: Path, atualizar_nomes: bool):
        if not caminho.exists():
            raise SystemExit(f"CSV não encontrado: {caminho}")

        with caminho.open(encoding="utf-8-sig", newline="") as f:
            linhas = list(csv.DictReader(f))

        criadas = atualizadas = ignoradas = 0
        with transaction.atomic():
            for i, linha in enumerate(linhas, start=2):
                nome = " ".join((linha.get("nome") or "").split())
                cpf = normalizar(linha.get("cpf") or "")
                nome_oficina = (linha.get("oficina") or "").strip()
                papel = (linha.get("papel") or "OUVINTE").strip().upper()

                if not nome or not nome_oficina:
                    self.stderr.write(f"linha {i}: nome ou oficina vazio — ignorada")
                    ignoradas += 1
                    continue
                if cpf and not valido(cpf):
                    self.stderr.write(f"linha {i}: CPF inválido ({nome}) — ignorada")
                    ignoradas += 1
                    continue
                if papel not in Participacao.Papel.values:
                    self.stderr.write(f"linha {i}: papel '{papel}' inválido — ignorada")
                    ignoradas += 1
                    continue

                if nome_oficina.upper() in {"TODAS", "TODOS", "*"}:
                    destinos = list(Oficina.objects.all())
                    if not destinos:
                        self.stderr.write(f"linha {i}: nenhuma oficina cadastrada "
                                          f"(rode seed_oficinas antes) — ignorada")
                        ignoradas += 1
                        continue
                else:
                    oficina, _ = Oficina.objects.get_or_create(
                        nome=nome_oficina, defaults={"equipe": ""})
                    destinos = [oficina]

                for oficina in destinos:
                    resultado = self._gravar(nome=nome, cpf=cpf, oficina=oficina,
                                             papel=papel, atualizar_nomes=atualizar_nomes)
                    if resultado == "criada":
                        criadas += 1
                    elif resultado == "atualizada":
                        atualizadas += 1

        self.stdout.write(self.style.SUCCESS(
            f"CSV: {criadas} criada(s), {atualizadas} atualizada(s), {ignoradas} ignorada(s). "
            f"Total no banco: {Participacao.objects.count()}."))

    def _gravar(self, *, nome, cpf, oficina, papel, atualizar_nomes):
        """Cria ou atualiza uma participação (nome × oficina × papel)."""
        filtro = {"oficina": oficina, "papel": papel}
        filtro["cpf_hash"] = hash_cpf(cpf) if cpf else ""
        existente = (Participacao.objects.filter(**filtro).first()
                     or Participacao.objects.filter(nome=nome, oficina=oficina).first())

        if existente:
            campos = []
            if cpf and (existente.cpf_hash, existente.cpf_meio) != (hash_cpf(cpf), meio_cpf(cpf)):
                existente.cpf_hash, existente.cpf_meio = hash_cpf(cpf), meio_cpf(cpf)
                campos += ["cpf_hash", "cpf_meio"]
            if atualizar_nomes and existente.nome != nome:
                existente.nome = nome
                campos.append("nome")
            if campos:
                existente.save(update_fields=campos)
                return "atualizada"
            return None

        Participacao.objects.create(
            nome=nome, oficina=oficina, papel=papel,
            cpf_hash=hash_cpf(cpf) if cpf else "", cpf_meio=meio_cpf(cpf))
        return "criada"
