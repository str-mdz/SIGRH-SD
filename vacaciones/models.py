from django.conf import settings
from django.db import models


class Solicitud(models.Model):
    # Guarda las fechas de vacaciones y una sola decisión del administrador

    ESTADOS = [("P", "Pendiente"), ("A", "Aprobada"), ("R", "Rechazada"), ("C", "Cancelada")]
    empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="solicitudes")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.PositiveSmallIntegerField()
    motivo = models.TextField(blank=True, max_length=500)
    estado = models.CharField(max_length=1, choices=ESTADOS, default="P")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    revisor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="revisadas")
    observaciones = models.CharField(max_length=500, blank=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_solicitud"]
        verbose_name = "Solicitud"
        verbose_name_plural = "Solicitudes"

    def __str__(self):
        # Identifica la solicitud en el panel de administración
        return f"{self.empleado} · {self.fecha_inicio} · {self.get_estado_display()}"
