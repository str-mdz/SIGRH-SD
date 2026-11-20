from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CandidatoForm, EstadoCandidatoForm, VacanteForm
from .models import Candidato, Vacante


# Lista vacantes y candidatos para los administradores
@login_required
def inicio(request):
    if not request.user.is_staff:
        raise PermissionDenied
    return render(request, "reclutamiento/inicio.html", {
        "vacantes": Vacante.objects.all(),
        "candidatos": Candidato.objects.select_related("vacante"),
    })


# Registra una vacante o modifica sus datos y su estado
@login_required
def guardar_vacante(request, vacante_id=None):
    if not request.user.is_staff:
        raise PermissionDenied
    vacante = get_object_or_404(Vacante, pk=vacante_id) if vacante_id else None
    form = VacanteForm(request.POST if request.method == "POST" else None, instance=vacante)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vacante guardada.")
        return redirect("reclutamiento:inicio")
    return render(request, "reclutamiento/formulario.html", {
        "form": form, "titulo": "Editar vacante" if vacante else "Registrar vacante",
    })


# Registra un candidato con estado pendiente
@login_required
def registrar_candidato(request):
    if not request.user.is_staff:
        raise PermissionDenied
    form = CandidatoForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Candidato registrado.")
        return redirect("reclutamiento:inicio")
    return render(request, "reclutamiento/formulario.html", {"form": form, "titulo": "Registrar candidato"})


# Actualiza el estado del candidato al enviar el formulario
@login_required
def cambiar_estado_candidato(request, candidato_id):
    if not request.user.is_staff:
        raise PermissionDenied
    candidato = get_object_or_404(Candidato.objects.select_related("vacante"), pk=candidato_id)
    form = EstadoCandidatoForm(request.POST if request.method == "POST" else None, instance=candidato)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Estado del candidato actualizado.")
        return redirect("reclutamiento:inicio")
    return render(request, "reclutamiento/formulario.html", {
        "form": form, "titulo": "Cambiar estado del candidato", "candidato": candidato,
    })
