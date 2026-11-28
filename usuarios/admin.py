
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from .models import Usuario
from .sincronizacion import (
    ErrorSincronizacion,
    sincronizar_usuario,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):

    fieldsets = (
        (
            None,
            {"fields": ("username", "password")},
        ),
        (
            "Empleado",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "dias_vacaciones",
                )
            },
        ),
        (
            "Acceso",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "password1",
                    "password2",
                    "dias_vacaciones",
                    "is_staff",
                )
            },
        ),
    )

    list_display = (
        "username",
        "first_name",
        "last_name",
        "dias_vacaciones",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "is_staff",
        "is_active",
    )

    actions = ["resincronizar_usuarios"]

    # Se ejecuta cuando se crea o modifica un empleado.
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        try:
            sincronizar_usuario(obj)

        except ErrorSincronizacion as error:
            self.message_user(
                request,
                "El empleado se guardó en la aplicación web, "
                "pero NO se sincronizó con PostgreSQL. "
                f"Detalle: {error}. "
                "Puedes reintentar desde la lista de usuarios.",
                level=messages.WARNING,
            )

    # Permite reparar usuarios anteriores o reintentar.
    @admin.action(
        description="Sincronizar seleccionados con PostgreSQL"
    )
    def resincronizar_usuarios(self, request, queryset):
        correctos = 0
        errores = []

        for usuario in queryset:
            try:
                sincronizar_usuario(usuario)
                correctos += 1

            except ErrorSincronizacion as error:
                errores.append(
                    f"{usuario.username}: {error}"
                )

        if correctos:
            self.message_user(
                request,
                f"Usuarios sincronizados correctamente: {correctos}",
                level=messages.SUCCESS,
            )

        if errores:
            self.message_user(
                request,
                "Errores de sincronización: "
                + "; ".join(errores[:5]),
                level=messages.WARNING,
            )


admin.site.site_header = "Administración de SIGRH"
admin.site.site_title = "SIGRH"
admin.site.index_title = "Usuarios y solicitudes"
