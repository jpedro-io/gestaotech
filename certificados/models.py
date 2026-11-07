"""Modelos do banco de certificados.

Duas tabelas:

- Oficina: as oficinas do projeto Gestão Tech (com a equipe responsável).
- Participacao: uma linha por pessoa × oficina × papel. É o que gera o certificado.

Privacidade: o CPF completo **não é gravado**. Guardamos
  - `cpf_hash`   → SHA-256 com pepper (usado na busca)
  - `cpf_meio`   → os 6 dígitos do meio (para montar ***.123.456-**)
"""
import hashlib
import secrets
import string

from django.conf import settings
from django.db import models

ALFABETO_CODIGO = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"


def hash_cpf(cpf: str) -> str:
    """SHA-256 do CPF (só dígitos) com o pepper do settings."""
    limpo = "".join(ch for ch in (cpf or "") if ch.isdigit())
    return hashlib.sha256((limpo + settings.CPF_PEPPER).encode()).hexdigest()


def meio_cpf(cpf: str) -> str:
    limpo = "".join(ch for ch in (cpf or "") if ch.isdigit())
    return limpo[3:9] if len(limpo) == 11 else ""


def gerar_codigo() -> str:
    """Código no formato OFC-XXXX-XXXX-XXXX."""
    blocos = ["".join(secrets.choice(ALFABETO_CODIGO) for _ in range(4)) for _ in range(3)]
    return "OFC-" + "-".join(blocos)


class Oficina(models.Model):
    nome = models.CharField("nome da oficina", max_length=200, unique=True)
    equipe = models.CharField("equipe responsável", max_length=300, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "oficina"
        verbose_name_plural = "oficinas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Participacao(models.Model):
    class Papel(models.TextChoices):
        OUVINTE = "OUVINTE", "Ouvinte"
        MINISTRANTE = "MINISTRANTE", "Ministrante"
        ORGANIZADOR = "ORGANIZADOR", "Organizador(a)"

    nome = models.CharField("nome completo", max_length=160)
    cpf_hash = models.CharField("hash do CPF", max_length=64, db_index=True)
    cpf_meio = models.CharField("dígitos do meio do CPF", max_length=6, blank=True)
    oficina = models.ForeignKey(Oficina, on_delete=models.PROTECT, related_name="participacoes")
    papel = models.CharField("forma de participação", max_length=12,
                             choices=Papel.choices, default=Papel.OUVINTE)
    codigo = models.CharField("código de validação", max_length=18, unique=True,
                              default=gerar_codigo, editable=False)
    revogado = models.BooleanField(default=False)
    emitido_em = models.DateField("emitido em", null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "participação"
        verbose_name_plural = "participações"
        ordering = ["nome", "oficina__nome"]
        constraints = [
            # só vale para quem já tem CPF: quem ainda está sem CPF não pode colidir
            models.UniqueConstraint(
                fields=["cpf_hash", "oficina", "papel"],
                condition=~models.Q(cpf_hash=""),
                name="unico_cpf_oficina_papel",
            ),
        ]
        indexes = [models.Index(fields=["codigo"])]

    def __str__(self):
        return f"{self.nome} · {self.papel} · {self.oficina_id}"

    # ── helpers ────────────────────────────────────────────────────────────
    @property
    def cpf_parcial(self) -> str:
        m = self.cpf_meio or ""
        if len(m) != 6:
            return "***.***.***-**"
        return f"***.{m[:3]}.{m[3:6]}-**"

    @classmethod
    def criar(cls, nome, cpf, oficina, papel="OUVINTE", **extra):
        """Cria a participação a partir do CPF em texto (nunca guarda o número)."""
        return cls.objects.create(
            nome=" ".join(nome.split()),
            cpf_hash=hash_cpf(cpf),
            cpf_meio=meio_cpf(cpf),
            oficina=oficina,
            papel=papel,
            **extra,
        )
