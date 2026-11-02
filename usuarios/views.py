from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from vacaciones.models import Solicitud
from vacaciones.services import resumen_dias


def login_usuario(request):
    # Inicia sesión con el identificador y la contraseña del empleado
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        usuario = authenticate(
            request,
            username=request.POST.get("id_empleado", "").strip(),
            password=request.POST.get("contrasenia", ""),
        )
        if usuario is not None:
            login(request, usuario)
            return redirect("dashboard")
        messages.error(request, "Identificador o contraseña incorrectos.")
    return render(request, "usuarios/login.html")


@login_required
def dashboard(request):
    # Muestra el saldo anual y las últimas solicitudes del usuario
    return render(request, "usuarios/dashboard.html", {
        "saldo": resumen_dias(request.user),
        "solicitudes": Solicitud.objects.filter(empleado=request.user)[:5],
    })


@login_required
@require_POST
def logout_usuario(request):
    # Cierra la sesión mediante el botón Salir
    logout(request)
    return redirect("login")


@login_required
def politicas_vacaciones(request):
    # Explica las reglas que aplica esta versión del sistema
    return render(request, "usuarios/politicas.html")
