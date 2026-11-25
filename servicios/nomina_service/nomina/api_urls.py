from django.urls import path
from . import api

urlpatterns = [
    path("estado/", api.estado_servicio, name="estado"),
    path("nominas/", api.nominas, name="nominas"),
]