import os
import requests


class UsuarioAPIError(Exception):
    def __init__(self, mensaje, estado=503):
        super().__init__(mensaje)
        self.estado = estado


# Consulta al propietario de los datos de empleados.
def obtener_usuario(usuario_id):
    base = os.getenv("USU_API_URL", "").rstrip("/")
    token = os.getenv("USU_INTERNAL_TOKEN", "")

    if not base or not token:
        raise UsuarioAPIError("Usuarios no está configurado.")

    try:
        respuesta = requests.get(
            f"{base}/usuarios/{usuario_id}/",
            headers={"X-Internal-Token": token},
            timeout=(2, 5)
        )
    except requests.RequestException:
        raise UsuarioAPIError(
            "No se pudo conectar con Usuarios."
        )

    if respuesta.status_code == 404:
        raise UsuarioAPIError(
            "Empleado no encontrado.",
            estado=404
        )

    if respuesta.status_code != 200:
        raise UsuarioAPIError(
            "Usuarios no está disponible."
        )

    try:
        usuario = respuesta.json()
    except ValueError:
        raise UsuarioAPIError(
            "Usuarios devolvió una respuesta inválida."
        )

    if (
        not isinstance(usuario, dict)
        or usuario.get("id") != usuario_id
        or type(usuario.get("dias_vacaciones")) is not int
        or type(usuario.get("activo")) is not bool
        or type(usuario.get("administrador")) is not bool
    ):
        raise UsuarioAPIError(
            "Usuarios devolvió datos incompletos."
        )

    if not usuario["activo"]:
        raise UsuarioAPIError(
            "El empleado no está activo.",
            estado=403
        )

    return usuario
