from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


# Organiza el alta y la edición de empleados en el administrador
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Empleado", {"fields": ("first_name", "last_name", "email", "dias_vacaciones")}),
        ("Acceso", {"fields": ("is_active", "is_staff")}),
    )
    add_fieldsets = (
        (None, {"fields": (
            "username", "first_name", "last_name", "email",
            "password1", "password2", "dias_vacaciones", "is_staff",
        )}),
    )
    list_display = ("username", "first_name", "last_name", "dias_vacaciones", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")


admin.site.site_header = "Administración de SIGRH"
admin.site.site_title = "SIGRH"
admin.site.index_title = "Usuarios y solicitudes"
