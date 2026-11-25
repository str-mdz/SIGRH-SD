import json
import os
import secrets

from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST


# Comprueba que la petición procede de un servicio autorizado.
def autorizado(request):
    esperado = os.getenv("USU_INTERNAL_TOKEN", "")
    recibido = request.headers.get("X-Internal-Token", "")

    return bool(esperado) and secrets.compare_digest(
        esperado, recibido
    )


# Devuelve información básica sin exponer contraseñas.
def datos_usuario(usuario):
    return {
        "id": usuario.pk,
        "identificador": usuario.get_username(),
        "nombre": getattr(usuario, "first_name", ""),
        "apellido": getattr(usuario, "last_name", ""),
        "activo": bool(getattr(usuario, "is_active", True)),
        "administrador": bool(usuario.is_staff),
        "dias_vacaciones": usuario.dias_vacaciones,
    }

# Permite saber si la aplicación está ejecutándose.
@require_GET
def estado_servicio(request):
    return JsonResponse({
        "servicio": "usuarios",
        "estado": "activo",
    })


# Consulta un usuario por su identificador.
@require_GET
def detalle_usuario(request, usuario_id):
    if not autorizado(request):
        return JsonResponse(
            {"error": "No autorizado"},
            status=401
        )

    Usuario = get_user_model()

    try:
        usuario = Usuario.objects.get(pk=usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse(
            {"error": "Usuario no encontrado"},
            status=404
        )

    return JsonResponse(datos_usuario(usuario))


# Verifica credenciales mediante el sistema de Django.
@csrf_exempt
@require_POST
def autenticar_usuario(request):
    if not autorizado(request):
        return JsonResponse(
            {"error": "No autorizado"},
            status=401
        )

    try:
        datos = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse(
            {"error": "JSON inválido"},
            status=400
        )

    if not isinstance(datos, dict):
        return JsonResponse(
            {"error": "Datos inválidos"},
            status=400
        )

    identificador = datos.get("identificador")
    contrasena = datos.get("password")

    if not isinstance(identificador, str) or not isinstance(
        contrasena, str
    ):
        return JsonResponse(
            {"error": "Credenciales inválidas"},
            status=400
        )

    Usuario = get_user_model()

    usuario = authenticate(
        request,
        **{
            Usuario.USERNAME_FIELD: identificador,
            "password": contrasena,
        }
    )

    if usuario is None or not getattr(usuario, "is_active", True):
        return JsonResponse(
            {"error": "Credenciales inválidas"},
            status=401
        )

    return JsonResponse({
        "autenticado": True,
        "usuario": datos_usuario(usuario),
    })
