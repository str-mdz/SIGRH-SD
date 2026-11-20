from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from vacaciones.models import Solicitud
from vacaciones.services import resumen_dias


# Inicia sesión con el identificador y la contraseña del empleado
def login_usuario(request):
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


# Muestra el saldo anual y las últimas solicitudes del usuario
@login_required
def dashboard(request):
    return render(request, "usuarios/dashboard.html", {
        "saldo": resumen_dias(request.user),
        "solicitudes": Solicitud.objects.filter(empleado=request.user)[:5],
    })


# Cierra la sesión mediante el botón Salir
@login_required
@require_POST
def logout_usuario(request):
    logout(request)
    return redirect("login")


# Explica las reglas que aplica esta versión del sistema
@login_required
def politicas_vacaciones(request):
    return render(request, "usuarios/politicas.html")
