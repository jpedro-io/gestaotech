from django.contrib import admin

from .models import Oficina, Participacao


@admin.register(Oficina)
class OficinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "equipe", "total_participacoes")
    search_fields = ("nome", "equipe")
    ordering = ("nome",)

    @admin.display(description="participações")
    def total_participacoes(self, obj):
        return obj.participacoes.count()


@admin.register(Participacao)
class ParticipacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "oficina", "papel", "codigo", "revogado", "emitido_em")
    list_filter = ("papel", "revogado", "oficina")
    search_fields = ("nome", "codigo")
    readonly_fields = ("cpf_hash", "cpf_meio", "codigo", "criado_em")
    autocomplete_fields = ("oficina",)
    fieldsets = (
        ("Pessoa", {"fields": ("nome",)}),
        ("Certificado", {"fields": ("oficina", "papel", "codigo", "revogado", "emitido_em")}),
        ("CPF (não guardamos o número)", {
            "fields": ("cpf_hash", "cpf_meio"),
            "description": "O CPF completo nunca é gravado: só o hash e os 6 dígitos do meio, "
                           "usados para montar ***.123.456-** no certificado.",
        }),
    )
