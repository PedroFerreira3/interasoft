# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Usuario

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email',
    }))
    password = forms.CharField(label="Senha", widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Senha',
    }))

class EscolaForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo = 'escola'
        if commit:
            user.save()
        return user

class ProfessorForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'cpf', 'telefone', 'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        self.escola = kwargs.pop('escola', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo = 'professor'
        user.escola = self.escola
        if commit:
            user.save()
        return user

class AlunoForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'cpf', 'telefone', 'endereco', 'username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        self.escola = kwargs.pop('escola', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo = 'aluno'
        user.escola = self.escola
        if commit:
            user.save()
        return user