from datetime import date

from django.conf import settings
from django.core import signing
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from certificados.models import Participacao

from . import dados
from .certificado import gerar_pdf
from .cpf import normalizar, valido

ERRO = ("Não encontramos um certificado com esses dados. "
        "Confira se o nome, o CPF e a oficina estão corretos.")


def _form(request, erro=None, status=200, digitado=None, oficina=None):
    return render(request, "emitir.html", {
        "oficinas": dados.listar_oficinas(),
        "erro": erro,
        "digitado": digitado or {},
        "oficina_sel": oficina or "",
    }, status=status)


def emitir(request):
    return _form(request, None)


@require_POST
@ratelimit(key="ip", rate="10/m", method="POST", block=False)
def buscar(request):
    digitado = {"nome": request.POST.get("nome", ""),
                "cpf": request.POST.get("cpf", "")}
    oficina = request.POST.get("oficina", "").strip()

    if getattr(request, "limited", False):
        return _form(request, "Muitas tentativas. Aguarde 1 minuto.", 429, digitado, oficina)
    if date.today() < settings.DATA_LIBERACAO:
        return _form(request, "Os certificados ainda não foram liberados.", 200, digitado, oficina)

    cpf = normalizar(request.POST.get("cpf", ""))
    if not valido(cpf):
        return _form(request, "CPF inválido. Confira os números digitados.", 200, digitado, oficina)

    # compara o nome de forma tolerante (só como filtro, sem revelar qual campo falhou)
    nome = " ".join(digitado["nome"].split()).lower()
    achados_qs = [p for p in dados.participacoes_do_cpf(cpf)
                  if not p.revogado and (not oficina or p.oficina.nome == oficina)]
    if nome:
        def combina(p):
            alvo = p.nome.lower()
            return nome in alvo or alvo.startswith(nome.split()[0])
        por_nome = [p for p in achados_qs if combina(p)]
        achados_qs = por_nome or achados_qs
    if not achados_qs:
        return _form(request, ERRO, 200, digitado, oficina)

    achados = [dados.publico(p) for p in achados_qs]

    itens = [{
        "nome": p["nome"], "oficina": p["oficina"], "papel": p["papel"],
        "codigo": p["codigo"],
        "token": signing.dumps(p["codigo"], salt="download"),
    } for p in achados]
    return render(request, "resultado.html", {"participacoes": itens,
                                              "digitado": digitado})


def baixar(request, token):
    try:
        codigo = signing.loads(token, salt="download", max_age=600)  # 10 min
    except signing.BadSignature:
        return _form(request, "Link expirado. Faça a busca novamente.", 400)

    p = dados.buscar_por_codigo(codigo)
    if not p or p["revogado"]:
        return _form(request, ERRO, 404)

    # grava a data de emissão no primeiro download (o certificado não muda depois)
    if not p["emitido_em"]:
        Participacao.objects.filter(codigo=codigo, emitido_em__isnull=True).update(
            emitido_em=date.today())
        p["emitido_em"] = date.today()

    resp = HttpResponse(gerar_pdf(p), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="certificado-{codigo}.pdf"'
    return resp


@ratelimit(key="ip", rate="30/m", block=False)
def validar(request, codigo=None):
    codigo = (codigo or request.GET.get("codigo", "")).strip().upper()
    if not codigo:
        return render(request, "validar.html", {"codigo": ""})
    if getattr(request, "limited", False):
        return render(request, "validar.html", {"estado": "limite", "codigo": codigo}, status=429)

    p = dados.buscar_por_codigo(codigo)
    if not p:
        estado = "invalido"
    elif p["revogado"]:
        estado = "revogado"
    else:
        estado = "valido"
    ctx = {"estado": estado, "codigo": codigo}
    if estado == "valido":
        ctx.update(nome=p["nome"], oficina=p["oficina"], papel=p["papel"],
                   cpf_parcial=p["cpf_parcial"])
    return render(request, "validar.html", ctx)
