import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

# Credenciais fixas para testes
USERNAME = 'admin'
EMAIL = 'admin@test.com'
PASSWORD = 'senha&123'  # Senha simples para testes

if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD
    )
    print(f"Superuser criado: {USERNAME}/{PASSWORD}")
else:
    print(f"Superuser já existe: {USERNAME}/{PASSWORD}")