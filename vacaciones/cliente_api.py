import os
from datetime import date
from types import SimpleNamespace

import requests


class FalloAPI(Exception):
    def __init__(self, mensaje, estado=503):
        super().__init__(mensaje)
        self.estado = estado


# Envía una petición protegida a un microservicio.
def peticion(base_variable, token_variable, metodo, ruta,
             datos=None, parametros=None):
    base = os.getenv(base_variable, "").rstrip("/")
    token = os.getenv(token_variable, "")

    if not base or not token:
        raise FalloAPI("Servicio no configurado.")

    try:
        respuesta = requests.request(
            metodo,
            f"{base}/{ruta.lstrip('/')}",
            headers={"X-Internal-Token": token},
            json=datos,
            params=parametros,
            timeout=(2, 5)
        )
    except requests.RequestException as error:
        raise FalloAPI(
            "No se pudo conectar con el servicio."
        ) from error

    try:
        contenido = respuesta.json()
    except ValueError as error:
        raise FalloAPI(
            "El servicio devolvió una respuesta inválida.",
            502
        ) from error

    if not respuesta.ok:
        mensaje = "No se pudo completar la operación."

        if isinstance(contenido, dict):
            detalle = contenido.get(
                "errores", contenido.get("error", mensaje)
            )

            if isinstance(detalle, list):
                mensaje = " ".join(str(x) for x in detalle)
            else:
                mensaje = str(detalle)

        raise FalloAPI(mensaje, respuesta.status_code)

    return contenido


# Consulta la API de Vacaciones.
def vacaciones_api(metodo, ruta, datos=None, parametros=None):
    return peticion(
        "VAC_API_URL",
        "VAC_INTERNAL_TOKEN",
        metodo,
        ruta,
        datos,
        parametros
    )


# Consulta al propietario de los empleados.
def usuarios_api(usuario_id):
    return peticion(
        "USU_API_URL",
        "USU_INTERNAL_TOKEN",
        "GET",
        f"usuarios/{usuario_id}/"
    )


# Adapta las respuestas JSON para las plantillas existentes.
def adaptar_solicitud(datos, incluir_nombre=False):
    solicitud = SimpleNamespace(**datos)

    # Los HTML originales utilizan solicitud.pk.
    solicitud.pk = datos["id"]

    # Los HTML originales esperan objetos date de Python.
    solicitud.fecha_inicio = date.fromisoformat(
        datos["fecha_inicio"]
    )
    solicitud.fecha_fin = date.fromisoformat(
        datos["fecha_fin"]
    )

    # La plantilla utiliza get_estado_display.
    solicitud.get_estado_display = datos["estado_texto"]

    solicitud.empleado = (
        f"Empleado #{datos['empleado_id']}"
    )

    if incluir_nombre:
        try:
            usuario = usuarios_api(datos["empleado_id"])

            nombre = " ".join(
                x for x in [
                    usuario.get("nombre", ""),
                    usuario.get("apellido", "")
                ] if x
            )

            solicitud.empleado = (
                nombre
                or usuario.get("identificador")
                or solicitud.empleado
            )

        except FalloAPI:
            # Conserva el identificador si Usuarios no responde.
            pass

    return solicitud
