from django.urls import path
from . import views

app_name = "nomina"
# Conecta el historial y el registro de nóminas
urlpatterns = [
    path("", views.historial, name="historial"),
    path("registrar/", views.registrar, name="registrar"),
]
