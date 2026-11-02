from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("vacaciones/", include("vacaciones.urls")),
    path("", RedirectView.as_view(pattern_name="dashboard", permanent=False)),
    path("login/", RedirectView.as_view(pattern_name="login", permanent=False)),
]
