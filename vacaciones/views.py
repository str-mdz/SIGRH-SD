from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import RevisionForm, SolicitudForm
from .models import Solicitud
from .services import crear_solicitud, resumen_dias


@login_required
def solicitar_vacaciones(request):
    # Recibe las fechas y muestra los errores sin borrar el formulario
    form = SolicitudForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            crear_solicitud(request.user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, "Solicitud enviada.")
            return redirect("ver_estatus_vacaciones")
    return render(request, "vacaciones/solicitar.html", {"form": form, "saldo": resumen_dias(request.user)})


@login_required
def ver_estatus(request):
    # Lista únicamente las solicitudes del usuario que inició sesión
    return render(request, "vacaciones/estatus.html", {
        "solicitudes": Solicitud.objects.filter(empleado=request.user).select_related("revisor"),
    })


@login_required
@require_POST
def cancelar_solicitud(request, solicitud_id):
    # Cancela una solicitud propia solo mientras esté pendiente
    solicitud = get_object_or_404(Solicitud, pk=solicitud_id, empleado=request.user)
    cambio = Solicitud.objects.filter(pk=solicitud.pk, estado="P").update(estado="C", fecha_respuesta=timezone.now())
    if cambio:
        messages.success(request, "Solicitud cancelada. Tus días vuelven a estar disponibles.")
    else:
        messages.error(request, "Solo puedes cancelar solicitudes pendientes.")
    return redirect("ver_estatus_vacaciones")


@login_required
def revisar_solicitudes(request):
    # Muestra al administrador las solicitudes pendientes de otras personas
    if not request.user.is_staff:
        raise PermissionDenied
    return render(request, "vacaciones/lista_revisiones.html", {
        "solicitudes": Solicitud.objects.filter(estado="P").exclude(empleado=request.user).select_related("empleado"),
    })


@login_required
def detalle_revision(request, solicitud_id):
    # Aprueba o rechaza una sola vez; nadie revisa su propia solicitud
    if not request.user.is_staff:
        raise PermissionDenied
    solicitud = get_object_or_404(Solicitud.objects.select_related("empleado"), pk=solicitud_id)
    if solicitud.empleado_id == request.user.pk:
        raise PermissionDenied
    form = RevisionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cambio = Solicitud.objects.filter(pk=solicitud.pk, estado="P").update(
            estado=form.cleaned_data["decision"],
            observaciones=form.cleaned_data["observaciones"],
            revisor=request.user, fecha_respuesta=timezone.now(),
        )
        if cambio:
            messages.success(request, "Decisión guardada.")
        else:
            messages.error(request, "Esta solicitud ya no está pendiente.")
        return redirect("revisar_solicitudes")
    return render(request, "vacaciones/revisar.html", {"solicitud": solicitud, "form": form})
