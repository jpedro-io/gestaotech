from django import forms
from django.contrib import admin

from emissao.cpf import normalizar, valido

from .models import Oficina, Participacao, hash_cpf, meio_cpf


@admin.register(Oficina)
class OficinaAdmin(admin.ModelAdmin):
    list_display = ("nome", "equipe", "total_participacoes")
    search_fields = ("nome", "equipe")
    ordering = ("nome",)

    @admin.display(description="participações")
    def total_participacoes(self, obj):
        return obj.participacoes.count()


class ParticipacaoForm(forms.ModelForm):
    """Campo CPF só na entrada: vira hash, nunca é gravado."""

    cpf = forms.CharField(
        required=False, label="CPF",
        widget=forms.TextInput(attrs={"placeholder": "000.000.000-00", "size": 20}),
        help_text="Usado apenas para calcular o hash. O número não é guardado. "
                  "Em branco = mantém o CPF já cadastrado.",
    )

    class Meta:
        model = Participacao
        fields = ["nome", "oficina", "papel", "cpf", "revogado", "emitido_em"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.cpf_meio:
            self.fields["cpf"].help_text = (
                f"CPF atual: ***.{self.instance.cpf_meio[:3]}.{self.instance.cpf_meio[3:]}-** "
                f"— preencha só para corrigir."
            )

    def clean_cpf(self):
        cpf = normalizar(self.cleaned_data.get("cpf") or "")
        if cpf and not valido(cpf):
            raise forms.ValidationError("CPF inválido — confira os 11 dígitos.")
        return cpf

    def save(self, commit=True):
        obj = super().save(commit=False)
        cpf = self.cleaned_data.get("cpf")
        if cpf:                       # preenchido = calcula/recalcula o hash
            obj.cpf_hash = hash_cpf(cpf)
            obj.cpf_meio = meio_cpf(cpf)
        if commit:
            obj.save()
            self.save_m2m()
        return obj


@admin.register(Participacao)
class ParticipacaoAdmin(admin.ModelAdmin):
    form = ParticipacaoForm
    list_display = ("nome", "oficina", "papel", "codigo", "revogado", "emitido_em")
    list_filter = ("papel", "revogado", "oficina")
    list_select_related = ("oficina",)
    search_fields = ("nome", "codigo")
    readonly_fields = ("codigo", "cpf_atual", "criado_em")
    autocomplete_fields = ("oficina",)
    date_hierarchy = "criado_em"
    fieldsets = (
        ("Pessoa", {"fields": ("nome", "cpf", "cpf_atual")}),
        ("Certificado", {"fields": ("oficina", "papel", "codigo", "revogado", "emitido_em")}),
        ("Controle", {"fields": ("criado_em",), "classes": ("collapse",)}),
    )

    @admin.display(description="CPF no banco")
    def cpf_atual(self, obj):
        if not obj or not obj.papel:
            return "—"
        m = obj.cpf_meio or ""
        return f"***.{m[:3]}.{m[3:]}-**" if len(m) == 6 else "sem CPF"
