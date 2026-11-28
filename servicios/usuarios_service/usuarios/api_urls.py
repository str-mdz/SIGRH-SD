from django.urls import path

from .catalogo_api import catalogo_empleados
from . import api

urlpatterns = [
    path("estado/", api.estado_servicio),
    path("usuarios/<int:usuario_id>/", api.detalle_usuario),
    path("autenticar/", api.autenticar_usuario),
    path("sincronizar/", api.sincronizar_usuario),
    path(
        "catalogo-empleados/",
        catalogo_empleados,
        name="catalogo_empleados",
    ),
]
