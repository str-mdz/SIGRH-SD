from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Conecta las rutas de los cuatro módulos de SIGRH
    path("usuarios/", include("usuarios.urls")),
    path("vacaciones/", include("vacaciones.urls")),
    path("reclutamiento/", include("reclutamiento.urls")),
    path("nomina/", include("nomina.urls")),
    # Lleva la entrada principal al panel y mantiene el acceso por /login/
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path("login/", RedirectView.as_view(pattern_name="login", permanent=False)),
]
