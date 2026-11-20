from django.urls import path
from . import views

app_name = "reclutamiento"
# Conecta las pantallas de vacantes y candidatos del módulo de reclutamiento
urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("vacantes/registrar/", views.guardar_vacante, name="registrar_vacante"),
    path("vacantes/<int:vacante_id>/editar/", views.guardar_vacante, name="editar_vacante"),
    path("candidatos/registrar/", views.registrar_candidato, name="registrar_candidato"),
    path("candidatos/<int:candidato_id>/estado/", views.cambiar_estado_candidato, name="estado_candidato"),
]
