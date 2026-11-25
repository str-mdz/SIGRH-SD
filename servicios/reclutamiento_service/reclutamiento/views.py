from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.

# Informa que el servicio de Reclutamiento está funcionando.
def estado_servicio(request):
    return JsonResponse({
        "servicio": "reclutamiento",
        "estado": "activo"
    })