from django.shortcuts import render
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# Create your views here.

# Comprueba que Django y PostgreSQL funcionan.
@require_GET
def estado_servicio(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

    except DatabaseError:
        return JsonResponse({
            "servicio": "vacaciones",
            "estado": "sin_base_de_datos"
        }, status=503)

    return JsonResponse({
        "servicio": "vacaciones",
        "estado": "activo"
    })

