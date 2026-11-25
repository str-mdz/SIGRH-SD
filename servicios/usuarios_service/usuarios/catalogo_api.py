import os
import secrets

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def catalogo_empleados(request):
    esperado = os.getenv("USU_INTERNAL_TOKEN", "")
    recibido = request.headers.get("X-Internal-Token", "")

    if not (
        esperado
        and recibido
        and secrets.compare_digest(esperado, recibido)
    ):
        return JsonResponse(
            {"error": "Acceso no autorizado."},
            status=401,
        )

    Usuario = get_user_model()

    usuarios = Usuario.objects.filter(
        is_active=True
    ).order_by("username")

    return JsonResponse({
        "usuarios": [
            {
                "id": usuario.pk,
                "username": usuario.username,
                "nombre": usuario.first_name,
                "apellido": usuario.last_name,
                "administrador": usuario.is_staff,
            }
            for usuario in usuarios
        ]
    })
