import os
from types import SimpleNamespace

import requests


class ErrorServicio(Exception):
    def __init__(self, mensaje, estado=503):
        super().__init__(mensaje)
        self.estado = estado


def peticion(base_var, token_var, metodo, ruta,
             datos=None, parametros=None):

    base = os.getenv(base_var, "").rstrip("/")
    token = os.getenv(token_var, "")

    if not base or not token:
        raise ErrorServicio("Servicio no configurado.")

    try:
        respuesta = requests.request(
            metodo,
            f"{base}/{ruta.lstrip('/')}",
            headers={"X-Internal-Token": token},
            json=datos,
            params=parametros,
            timeout=(2, 5),
        )
    except requests.RequestException as error:
        raise ErrorServicio(
            "No se pudo conectar con el microservicio."
        ) from error

    try:
        contenido = respuesta.json()
    except ValueError as error:
        raise ErrorServicio(
            "Respuesta inválida del servicio.", 502
        ) from error

    if not respuesta.ok:
        mensaje = "No fue posible completar la operación."

        if isinstance(contenido, dict):
            if "error" in contenido:
                mensaje = str(contenido["error"])
            elif "errores" in contenido:
                mensaje = str(contenido["errores"])

        raise ErrorServicio(mensaje, respuesta.status_code)

    return contenido


def nomina_api(metodo, ruta, datos=None, parametros=None):
    return peticion(
        "NOM_API_URL",
        "NOM_INTERNAL_TOKEN",
        metodo,
        ruta,
        datos,
        parametros,
    )


def catalogo_empleados():
    respuesta = peticion(
        "USU_API_URL",
        "USU_INTERNAL_TOKEN",
        "GET",
        "catalogo-empleados/",
    )

    if (
        not isinstance(respuesta, dict)
        or not isinstance(respuesta.get("usuarios"), list)
    ):
        raise ErrorServicio(
            "Catálogo de empleados inválido.", 502
        )

    return respuesta["usuarios"]


class EmpleadoVista:
    def __init__(self, datos):
        self.id = datos["id"]
        self.username = datos.get(
            "username", f"ID {self.id}"
        )
        self.nombre = datos.get("nombre", "")
        self.apellido = datos.get("apellido", "")

    def __str__(self):
        nombre = " ".join(
            valor for valor in (
                self.nombre,
                self.apellido,
            )
            if valor
        )

        return nombre or self.username


def adaptar_nomina(datos, empleados_por_id):
    nomina = SimpleNamespace(**datos)

    empleado_id = int(datos["empleado_id"])

    empleado = empleados_por_id.get(
        empleado_id,
        {
            "id": empleado_id,
            "username": f"ID {empleado_id}",
        },
    )

    nomina.empleado = EmpleadoVista(empleado)

    return nomina
