from django.urls import path
from . import views

# Agrupa las pantallas de acceso, inicio y reglas de vacaciones
urlpatterns = [
    path("login/", views.login_usuario, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_usuario, name="logout"),
    path("politicas/", views.politicas_vacaciones, name="politicas"),
]
