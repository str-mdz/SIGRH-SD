import os
import requests

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render

from .forms import (
    VacanteForm,
    CandidatoForm,
    EstadoCandidatoForm,
)


# Envía una petición HTTP a Reclutamiento.
def llamar_api(metodo, ruta, datos=None):
    base = os.getenv("RECL_API_URL", "").rstrip("/")
    token = os.getenv("RECL_INTERNAL_TOKEN", "")

    if not base or not token:
        raise requests.RequestException(
            "Falta configurar la API de Reclutamiento"
        )

    respuesta = requests.request(
        metodo,
        f"{base}/{ruta.lstrip('/')}",
        json=datos,
        headers={"X-Internal-Token": token},
        timeout=(2, 5)
    )

    if respuesta.status_code == 404:
        raise Http404("Registro no encontrado")

    respuesta.raise_for_status()
    return respuesta.json()


# Conserva los permisos del monolito.
def comprobar_admin(request):
    if not request.user.is_staff:
        raise PermissionDenied


@login_required
def inicio(request):
    comprobar_admin(request)

    vacantes = []
    candidatos = []

    try:
        vacantes = llamar_api("GET", "vacantes/")["vacantes"]
        candidatos = llamar_api("GET", "candidatos/")["candidatos"]

    except (requests.RequestException, ValueError, KeyError):
        messages.error(
            request,
            "No se pudo conectar con Reclutamiento."
        )

    return render(request, "reclutamiento/inicio.html", {
        "vacantes": vacantes,
        "candidatos": candidatos,
    })


@login_required
def guardar_vacante(request, vacante_id=None):
    comprobar_admin(request)

    vacante = None

    if vacante_id is not None:
        try:
            vacante = llamar_api(
                "GET", f"vacantes/{vacante_id}/"
            )
        except requests.RequestException:
            messages.error(
                request, "No se pudo consultar la vacante."
            )
            return redirect("reclutamiento:inicio")

    form = VacanteForm(
        request.POST if request.method == "POST" else None,
        initial=vacante
    )

    if request.method == "POST" and form.is_valid():
        try:
            if vacante_id is None:
                llamar_api(
                    "POST", "vacantes/", form.cleaned_data
                )
            else:
                llamar_api(
                    "PATCH",
                    f"vacantes/{vacante_id}/",
                    form.cleaned_data
                )

            messages.success(request, "Vacante guardada.")
            return redirect("reclutamiento:inicio")

        except requests.RequestException:
            messages.error(
                request, "No se pudo guardar la vacante."
            )

    return render(
        request,
        "reclutamiento/formulario.html",
        {
            "form": form,
            "titulo": (
                "Registrar vacante"
                if vacante_id is None
                else "Editar vacante"
            ),
        }
    )


@login_required
def registrar_candidato(request):
    comprobar_admin(request)

    vacantes = []

    try:
        vacantes = llamar_api("GET", "vacantes/")["vacantes"]

    except (requests.RequestException, ValueError, KeyError):
        messages.error(
            request, "No se pudieron obtener las vacantes."
        )

    form = CandidatoForm(
        request.POST if request.method == "POST" else None,
        vacantes=vacantes
    )

    if request.method == "POST" and form.is_valid():
        try:
            llamar_api(
                "POST", "candidatos/", form.cleaned_data
            )

            messages.success(
                request, "Candidato registrado."
            )
            return redirect("reclutamiento:inicio")

        except requests.RequestException:
            messages.error(
                request, "No se pudo registrar el candidato."
            )

    return render(
        request,
        "reclutamiento/formulario.html",
        {
            "form": form,
            "titulo": "Registrar candidato",
        }
    )


@login_required
def cambiar_estado_candidato(request, candidato_id):
    comprobar_admin(request)

    try:
        candidato = llamar_api(
            "GET", f"candidatos/{candidato_id}/"
        )

    except requests.RequestException:
        messages.error(
            request, "No se pudo consultar el candidato."
        )
        return redirect("reclutamiento:inicio")

    form = EstadoCandidatoForm(
        request.POST if request.method == "POST" else None,
        initial={"estado": candidato["estado"]}
    )

    if request.method == "POST" and form.is_valid():
        try:
            llamar_api(
                "PATCH",
                f"candidatos/{candidato_id}/",
                form.cleaned_data
            )

            messages.success(
                request, "Estado actualizado."
            )
            return redirect("reclutamiento:inicio")

        except requests.RequestException:
            messages.error(
                request, "No se pudo actualizar el candidato."
            )

    return render(
        request,
        "reclutamiento/formulario.html",
        {
            "form": form,
            "titulo": "Cambiar estado del candidato",
            "candidato": candidato,
        }
    )
