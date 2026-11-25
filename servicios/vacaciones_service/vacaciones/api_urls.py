from django.urls import path
from . import api

urlpatterns = [
    path("saldo/", api.saldo),
    path("solicitudes/", api.solicitudes),
    path(
        "solicitudes/<int:solicitud_id>/",
        api.detalle_solicitud
    ),
    path(
        "solicitudes/<int:solicitud_id>/cancelar/",
        api.cancelar
    ),
    path(
        "solicitudes/<int:solicitud_id>/revision/",
        api.revision
    ),
]
