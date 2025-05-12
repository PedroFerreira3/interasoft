# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('username', 'email', 'tipo', 'escola', 'is_active')
    list_filter = ('tipo', 'escola', 'is_active', 'is_staff')
    list_editable = ('is_active',)
    search_fields = ('username', 'email', 'first_name', 'last_name', 'cpf')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {
            'fields': ('first_name', 'last_name', 'email', 'cpf', 'telefone', 'endereco')
        }),
        ('Tipo e Escola', {
            'fields': ('tipo', 'escola')
        }),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'tipo', 'escola', 'is_active', 'is_staff'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.tipo == 'escola':
            return qs.filter(escola=request.user)
        return qs