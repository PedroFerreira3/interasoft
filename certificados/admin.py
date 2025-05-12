from django.contrib import admin
from .models import Certificado

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'curso', 'codigo', 'criado_em')
    search_fields = ('aluno__username', 'curso__nome', 'codigo')
    list_filter = ('curso', 'criado_em')
    readonly_fields = ('codigo', 'criado_em')
