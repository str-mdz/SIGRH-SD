import json
import os
import secrets

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import CandidatoForm, EstadoCandidatoForm, VacanteForm
from .models import Candidato, Vacante


# Comprueba la clave enviada por otro servicio.
def autorizado(request):
    esperado = os.getenv("RECL_INTERNAL_TOKEN", "")
    recibido = request.headers.get("X-Internal-Token", "")
    return bool(esperado) and secrets.compare_digest(recibido, esperado)


# Lee los datos JSON enviados en la petición.
def leer_json(request):
    try:
        datos = json.loads(request.body.decode("utf-8"))
        return datos if isinstance(datos, dict) else None
    except (ValueError, UnicodeDecodeError):
        return None


# Convierte una vacante en datos que pueden viajar por HTTP.
def datos_vacante(vacante):
    return {
        "id": vacante.pk,
        "pk": vacante.pk,
        "titulo": vacante.titulo,
        "descripcion": vacante.descripcion,
        "estado": vacante.estado,
        "get_estado_display": vacante.get_estado_display(),
    }


# Convierte un candidato en datos JSON.
def datos_candidato(candidato):
    return {
        "id": candidato.pk,
        "pk": candidato.pk,
        "nombre": candidato.nombre,
        "correo": candidato.correo,
        "vacante_id": candidato.vacante_id,
        "vacante": {
            "id": candidato.vacante_id,
            "titulo": candidato.vacante.titulo,
        },
        "estado": candidato.estado,
        "get_estado_display": candidato.get_estado_display(),
    }


# Lista las vacantes o registra una nueva.
@csrf_exempt
@require_http_methods(["GET", "POST"])
def vacantes(request):
    if not autorizado(request):
        return JsonResponse({"error": "No autorizado"}, status=401)

    if request.method == "GET":
        return JsonResponse({
            "vacantes": [datos_vacante(v) for v in Vacante.objects.all()]
        })

    datos = leer_json(request)
    if datos is None:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    form = VacanteForm(datos)
    if not form.is_valid():
        return JsonResponse({"errores": form.errors}, status=400)

    vacante = form.save()
    return JsonResponse(datos_vacante(vacante), status=201)


# Consulta o actualiza una vacante existente.
@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def detalle_vacante(request, vacante_id):
    if not autorizado(request):
        return JsonResponse({"error": "No autorizado"}, status=401)

    vacante = get_object_or_404(Vacante, pk=vacante_id)

    if request.method == "GET":
        return JsonResponse(datos_vacante(vacante))

    datos = leer_json(request)
    if datos is None:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    form = VacanteForm(datos, instance=vacante)
    if not form.is_valid():
        return JsonResponse({"errores": form.errors}, status=400)

    return JsonResponse(datos_vacante(form.save()))


# Lista candidatos o registra una postulación.
@csrf_exempt
@require_http_methods(["GET", "POST"])
def candidatos(request):
    if not autorizado(request):
        return JsonResponse({"error": "No autorizado"}, status=401)

    if request.method == "GET":
        registros = Candidato.objects.select_related("vacante")
        return JsonResponse({
            "candidatos": [datos_candidato(c) for c in registros]
        })

    datos = leer_json(request)
    if datos is None:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    form = CandidatoForm(datos)
    if not form.is_valid():
        return JsonResponse({"errores": form.errors}, status=400)

    candidato = form.save()
    return JsonResponse(datos_candidato(candidato), status=201)


# Consulta un candidato o cambia su estado.
@csrf_exempt
@require_http_methods(["GET", "PATCH"])
def detalle_candidato(request, candidato_id):
    if not autorizado(request):
        return JsonResponse({"error": "No autorizado"}, status=401)

    candidato = get_object_or_404(
        Candidato.objects.select_related("vacante"),
        pk=candidato_id
    )

    if request.method == "GET":
        return JsonResponse(datos_candidato(candidato))

    datos = leer_json(request)
    if datos is None:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    form = EstadoCandidatoForm(datos, instance=candidato)
    if not form.is_valid():
        return JsonResponse({"errores": form.errors}, status=400)

    return JsonResponse(datos_candidato(form.save()))
