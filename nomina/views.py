from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from .forms import NominaForm
from .models import Nomina


# Muestra todas las nóminas a administradores y solo las propias a empleados
@login_required
def historial(request):
    nominas = Nomina.objects.select_related("empleado")
    if not request.user.is_staff:
        nominas = nominas.filter(empleado=request.user)
    return render(request, "nomina/historial.html", {"nominas": nominas})


# Permite registrar una nómina únicamente a administradores
@login_required
def registrar(request):
    if not request.user.is_staff:
        raise PermissionDenied
    form = NominaForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Nómina registrada.")
        return redirect("nomina:historial")
    return render(request, "nomina/registrar.html", {"form": form})
