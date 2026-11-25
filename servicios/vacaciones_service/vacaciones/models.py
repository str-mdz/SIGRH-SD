from django.db import models

# Create your models here.

# Almacena solicitudes sin claves foráneas hacia Usuarios.
class Solicitud(models.Model):

    ESTADOS = [
        ("P", "Pendiente"),
        ("A", "Aprobada"),
        ("R", "Rechazada"),
        ("C", "Cancelada"),
    ]

    # Identificadores pertenecientes al servicio Usuarios.
    empleado_id = models.PositiveBigIntegerField(db_index=True)
    revisor_id = models.PositiveBigIntegerField(
        null=True,
        blank=True
    )

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias = models.PositiveSmallIntegerField()

    motivo = models.TextField(blank=True, max_length=500)

    estado = models.CharField(
        max_length=1,
        choices=ESTADOS,
        default="P"
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    observaciones = models.CharField(
        max_length=500,
        blank=True
    )

    fecha_respuesta = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-fecha_solicitud"]
        verbose_name = "Solicitud"
        verbose_name_plural = "Solicitudes"

    def __str__(self):
        return (
            f"Empleado {self.empleado_id} - "
            f"{self.fecha_inicio} - "
            f"{self.get_estado_display()}"
        )
