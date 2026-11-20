from django.contrib import admin
from .models import Solicitud


# Permite consultar las solicitudes sin alterar su historial desde el administrador
@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ("empleado", "fecha_inicio", "fecha_fin", "dias", "estado", "revisor")
    list_filter = ("estado",)
    search_fields = ("empleado__username", "empleado__first_name", "empleado__last_name")
    readonly_fields = ("empleado", "fecha_inicio", "fecha_fin", "dias", "motivo", "estado", "fecha_solicitud", "revisor", "observaciones", "fecha_respuesta")

    # Las solicitudes se crean desde el formulario para validar el saldo
    def has_add_permission(self, request):
        return False

    # Las decisiones se guardan desde Revisar solicitudes
    def has_change_permission(self, request, obj=None):
        return False

    # Conserva el historial de vacaciones
    def has_delete_permission(self, request, obj=None):
        return False
