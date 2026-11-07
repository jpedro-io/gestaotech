"""Camada de dados — agora no banco (Neon / Postgres).

Nunca devolve o CPF: só `cpf_parcial`, montado a partir dos 6 dígitos do meio.
Tudo o que as views precisam está aqui, então trocar de fonte não mexe em mais nada.
"""
from certificados.models import Oficina, Participacao, hash_cpf

__all__ = ["listar_oficinas", "buscar_por_cpf", "buscar_por_codigo",
           "participacoes_do_cpf", "publico"]


def publico(p: Participacao) -> dict:
    return {
        "nome": p.nome,
        "oficina": p.oficina.nome,
        "papel": p.papel,
        "codigo": p.codigo,
        "revogado": p.revogado,
        "cpf_parcial": p.cpf_parcial,
        "emitido_em": p.emitido_em,
    }


def listar_oficinas():
    """Nomes das 7 oficinas do projeto, para a caixa de seleção.

    Lista todas as oficinas cadastradas (não só as que já têm participações),
    porque o catálogo é fixo e as equipes ainda vão enviar os dados.
    """
    return list(Oficina.objects.order_by("nome").values_list("nome", flat=True))


def participacoes_do_cpf(cpf: str):
    """Todas as participações de um CPF (inclui revogadas — a view filtra)."""
    return (
        Participacao.objects.select_related("oficina")
        .filter(cpf_hash=hash_cpf(cpf))
        .order_by("oficina__nome")
    )


def buscar_por_cpf(cpf: str):
    return [publico(p) for p in participacoes_do_cpf(cpf)]


def buscar_por_codigo(codigo: str):
    p = (
        Participacao.objects.select_related("oficina")
        .filter(codigo=(codigo or "").strip().upper())
        .first()
    )
    return publico(p) if p else None
