import os
import requests


class UsuarioAPIError(Exception):
    def __init__(self, mensaje, estado=503):
        super().__init__(mensaje)
        self.estado = estado


def obtener_usuario(usuario_id):
    base = os.getenv("USU_API_URL", "").rstrip("/")
    token = os.getenv("USU_INTERNAL_TOKEN", "")

    if not base or not token:
        raise UsuarioAPIError("Usuarios no está configurado.")

    try:
        respuesta = requests.get(
            f"{base}/usuarios/{usuario_id}/",
            headers={"X-Internal-Token": token},
            timeout=(2, 5),
        )
    except requests.RequestException as error:
        raise UsuarioAPIError(
            "No se pudo comunicar con Usuarios."
        ) from error

    if respuesta.status_code == 404:
        raise UsuarioAPIError("Empleado no encontrado.", 404)

    if not respuesta.ok:
        raise UsuarioAPIError(
            "Usuarios no pudo validar la identidad."
        )

    try:
        usuario = respuesta.json()
    except ValueError as error:
        raise UsuarioAPIError(
            "Usuarios devolvió una respuesta inválida.", 502
        ) from error

    if not isinstance(usuario, dict):
        raise UsuarioAPIError("Respuesta inválida de Usuarios.", 502)

    if usuario.get("id") != usuario_id:
        raise UsuarioAPIError("Identidad inconsistente.", 502)

    if not isinstance(usuario.get("activo"), bool):
        raise UsuarioAPIError("Falta el estado del empleado.", 502)

    if not isinstance(usuario.get("administrador"), bool):
        raise UsuarioAPIError("Faltan los permisos del empleado.", 502)

    if not usuario["activo"]:
        raise UsuarioAPIError("El empleado está inactivo.", 403)

    return usuario
