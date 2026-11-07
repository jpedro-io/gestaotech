"""CPF: normalização, validação dos dígitos e máscara parcial."""
import re


def normalizar(cpf: str) -> str:
    return re.sub(r"\D", "", cpf or "")


def valido(c: str) -> bool:
    if len(c) != 11 or c == c[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(c[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10 % 11) % 10 != int(c[n]):
            return False
    return True


def mascarar(c: str) -> str:
    return f"***.{c[3:6]}.{c[6:9]}-**"
