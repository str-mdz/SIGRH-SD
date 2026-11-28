from django.urls import path
from . import views, recibos

app_name = "nomina"

urlpatterns = [
    path("", views.historial, name="historial"),
    path("registrar/", views.registrar, name="registrar"),
    path(
        "recibo/<int:nomina_id>/",
        recibos.descargar,
        name="recibo",
    ),
]

