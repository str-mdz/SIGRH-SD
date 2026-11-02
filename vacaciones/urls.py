from django.urls import path
from . import views

urlpatterns = [
    path("solicitar/", views.solicitar_vacaciones, name="solicitar_vacaciones"),
    path("estatus/", views.ver_estatus, name="ver_estatus_vacaciones"),
    path("cancelar/<int:solicitud_id>/", views.cancelar_solicitud, name="cancelar_solicitud"),
    path("revisiones/", views.revisar_solicitudes, name="revisar_solicitudes"),
    path("revisiones/<int:solicitud_id>/", views.detalle_revision, name="detalle_revision"),
]
