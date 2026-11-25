from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import SolicitudForm, RevisionForm
from .cliente_api import (
    vacaciones_api,
    adaptar_solicitud,
    FalloAPI,
)


# Convierte errores de permisos en respuestas HTTP adecuadas.
def verificar_error(error):
    if error.estado == 403:
        raise PermissionDenied
    if error.estado == 404:
        raise Http404(str(error))


# Solicita vacaciones utilizando la API.
@login_required
def solicitar_vacaciones(request):
    form = SolicitudForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        datos = {
            "actor_id": request.user.pk,
            "fecha_inicio": (
                form.cleaned_data["fecha_inicio"].isoformat()
            ),
            "fecha_fin": (
                form.cleaned_data["fecha_fin"].isoformat()
            ),
            "motivo": form.cleaned_data["motivo"],
        }

        try:
            vacaciones_api("POST", "solicitudes/", datos)

            messages.success(request, "Solicitud enviada.")
            return redirect("ver_estatus_vacaciones")

        except FalloAPI as error:
            if error.estado == 400:
                form.add_error(None, str(error))
            else:
                verificar_error(error)
                messages.error(request, str(error))

    # El saldo se obtiene desde Vacaciones.
    saldo = {"disponibles": "No disponible"}

    try:
        saldo = vacaciones_api(
            "GET",
            "saldo/",
            parametros={"actor_id": request.user.pk}
        )
    except FalloAPI as error:
        verificar_error(error)
        messages.error(request, str(error))

    return render(
        request,
        "vacaciones/solicitar.html",
        {"form": form, "saldo": saldo}
    )


# Consulta únicamente las solicitudes del empleado.
@login_required
def ver_estatus(request):
    solicitudes = []

    try:
        respuesta = vacaciones_api(
            "GET",
            "solicitudes/",
            parametros={"actor_id": request.user.pk}
        )

        solicitudes = [
            adaptar_solicitud(item)
            for item in respuesta["solicitudes"]
        ]

    except (FalloAPI, ValueError, KeyError) as error:
        messages.error(
            request,
            f"No se pudo consultar el historial: {error}"
        )

    return render(
        request,
        "vacaciones/estatus.html",
        {"solicitudes": solicitudes}
    )


# Cancela una solicitud propia mediante HTTP.
@login_required
@require_POST
def cancelar_solicitud(request, solicitud_id):
    try:
        vacaciones_api(
            "POST",
            f"solicitudes/{solicitud_id}/cancelar/",
            {"actor_id": request.user.pk}
        )

        messages.success(
            request,
            "Solicitud cancelada. Tus días vuelven "
            "a estar disponibles."
        )

    except FalloAPI as error:
        verificar_error(error)
        messages.error(request, str(error))

    return redirect("ver_estatus_vacaciones")


# Muestra las solicitudes pendientes de otras personas.
@login_required
def revisar_solicitudes(request):
    if not request.user.is_staff:
        raise PermissionDenied

    solicitudes = []

    try:
        respuesta = vacaciones_api(
            "GET",
            "solicitudes/",
            parametros={
                "actor_id": request.user.pk,
                "pendientes": "1"
            }
        )

        solicitudes = [
            adaptar_solicitud(item, incluir_nombre=True)
            for item in respuesta["solicitudes"]
        ]

    except FalloAPI as error:
        verificar_error(error)
        messages.error(request, str(error))

    return render(
        request,
        "vacaciones/lista_revisiones.html",
        {"solicitudes": solicitudes}
    )


# Aprueba o rechaza solicitudes desde la API.
@login_required
def detalle_revision(request, solicitud_id):
    if not request.user.is_staff:
        raise PermissionDenied

    try:
        datos = vacaciones_api(
            "GET",
            f"solicitudes/{solicitud_id}/",
            parametros={"actor_id": request.user.pk}
        )
    except FalloAPI as error:
        verificar_error(error)
        messages.error(request, str(error))
        return redirect("revisar_solicitudes")

    if datos["empleado_id"] == request.user.pk:
        raise PermissionDenied

    solicitud = adaptar_solicitud(
        datos,
        incluir_nombre=True
    )

    form = RevisionForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            vacaciones_api(
                "POST",
                f"solicitudes/{solicitud_id}/revision/",
                {
                    "actor_id": request.user.pk,
                    "decision": form.cleaned_data["decision"],
                    "observaciones": (
                        form.cleaned_data["observaciones"]
                    )
                }
            )

            messages.success(request, "Decisión guardada.")
            return redirect("revisar_solicitudes")

        except FalloAPI as error:
            verificar_error(error)

            if error.estado in (400, 409):
                form.add_error(None, str(error))
            else:
                messages.error(request, str(error))

    return render(
        request,
        "vacaciones/revisar.html",
        {"solicitud": solicitud, "form": form}
    )
