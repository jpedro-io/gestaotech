"""Contexto disponível em todos os templates."""
from datetime import date

from django.conf import settings


def site(request):
    return {
        "site_url": settings.SITE_URL,
        "ano": date.today().year,
        "liberado": date.today() >= settings.DATA_LIBERACAO,
        "data_liberacao": settings.DATA_LIBERACAO,
    }
