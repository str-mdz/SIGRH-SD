from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import NominaForm
from .cliente_api import (
    ErrorServicio,
    nomina_api,
    catalogo_empleados,
    adaptar_nomina,
)


# Muestra el historial desde PostgreSQL mediante la API.
@login_required
def historial(request):
    nominas = []

    try:
        respuesta = nomina_api(
            "GET",
            "nominas/",
            parametros={"actor_id": request.user.pk},
        )

        if not isinstance(respuesta.get("nominas"), list):
            raise ErrorServicio(
                "Historial de nóminas inválido.", 502
            )

        try:
            empleados = catalogo_empleados()
        except ErrorServicio:
            empleados = []

        empleados_por_id = {
            int(usuario["id"]): usuario
            for usuario in empleados
        }

        nominas = [
            adaptar_nomina(item, empleados_por_id)
            for item in respuesta["nominas"]
        ]

    except (
        ErrorServicio,
        KeyError,
        ValueError,
        TypeError,
    ):
        messages.error(
            request,
            "No fue posible consultar las nóminas "
            "en este momento.",
        )

    return render(
        request,
        "nomina/historial.html",
        {"nominas": nominas},
    )


# Solo los administradores pueden registrar nóminas.
@login_required
def registrar(request):
    if not request.user.is_staff:
        raise PermissionDenied

    empleados = []

    try:
        empleados = catalogo_empleados()
    except ErrorServicio:
        messages.error(
            request,
            "No se pudo consultar el catálogo "
            "de empleados.",
        )

    form = NominaForm(
        request.POST if request.method == "POST" else None,
        empleados=empleados,
    )

    if request.method == "POST" and form.is_valid():
        datos = {
            "actor_id": request.user.pk,
            "empleado_id": int(
                form.cleaned_data["empleado"]
            ),
            "periodo": form.cleaned_data["periodo"],
            "sueldo_base": str(
                form.cleaned_data["sueldo_base"]
            ),
            "bono": str(form.cleaned_data["bono"]),
            "descuento": str(
                form.cleaned_data["descuento"]
            ),
        }

        try:
            nomina_api(
                "POST",
                "nominas/",
                datos=datos,
            )

            messages.success(
                request,
                "Nómina registrada.",
            )

            return redirect("nomina:historial")

        except ErrorServicio as error:
            if error.estado == 403:
                raise PermissionDenied

            form.add_error(None, str(error))

    return render(
        request,
        "nomina/registrar.html",
        {"form": form},
    )
