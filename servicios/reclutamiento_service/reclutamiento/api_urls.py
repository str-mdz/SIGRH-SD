from django.urls import path
from . import api

urlpatterns = [
    path("vacantes/", api.vacantes),
    path("vacantes/<int:vacante_id>/", api.detalle_vacante),
    path("candidatos/", api.candidatos),
    path("candidatos/<int:candidato_id>/", api.detalle_candidato),
]
