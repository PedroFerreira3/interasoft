from rest_framework import serializers
from .models import Progresso

class NotaSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    capitulo_id = serializers.IntegerField()
    nota = serializers.FloatField()