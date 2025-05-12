from django.shortcuts import render, get_object_or_404
from .models import Certificado

def visualizar_certificado(request, certificado_id):
    certificado = get_object_or_404(Certificado, id=certificado_id)
    return render(request, 'certificados/certificado.html', {'certificado': certificado})
