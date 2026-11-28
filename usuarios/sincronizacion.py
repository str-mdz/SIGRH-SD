import os

import requests


class ErrorSincronizacion(Exception):
    """Indica que no pudo sincronizarse un empleado."""
    pass


def sincronizar_usuario(usuario):
    """
    Envía la información de un usuario web al microservicio
    Usuarios, manteniendo el mismo ID en ambas bases.
    """

    base = os.getenv("USU_API_URL", "").rstrip("/")
    token = os.getenv("USU_INTERNAL_TOKEN", "")

    if not base or not token:
        raise ErrorSincronizacion(
            "El microservicio Usuarios no está configurado."
        )

    datos = {
        "id": usuario.pk,
        "username": usuario.username,
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "email": usuario.email,
        "dias_vacaciones": usuario.dias_vacaciones,
        "is_staff": usuario.is_staff,
        "is_active": usuario.is_active,
        "is_superuser": usuario.is_superuser,
    }

    try:
        respuesta = requests.post(
            f"{base}/sincronizar/",
            json=datos,
            headers={"X-Internal-Token": token},
            timeout=(2, 5),
        )

    except requests.RequestException as error:
        raise ErrorSincronizacion(
            "No fue posible contactar al microservicio Usuarios."
        ) from error

    if respuesta.status_code not in (200, 201):
        try:
            mensaje = respuesta.json().get(
                "error", "Error desconocido"
            )
        except (ValueError, AttributeError):
            mensaje = "Respuesta inválida del microservicio"

        raise ErrorSincronizacion(
            f"Usuarios rechazó la sincronización: {mensaje}"
        )

    try:
        resultado = respuesta.json()
    except ValueError as error:
        raise ErrorSincronizacion(
            "El microservicio devolvió un JSON inválido."
        ) from error

    if (
        resultado.get("sincronizado") is not True
        or resultado.get("usuario", {}).get("id") != usuario.pk
    ):
        raise ErrorSincronizacion(
            "No se confirmó correctamente la identidad."
        )

    return resultado
