from django.db import models


# Guarda los datos del puesto y si admite postulaciones
class Vacante(models.Model):
    ESTADOS = [("A", "Abierta"), ("C", "Cerrada")]
    titulo = models.CharField(max_length=150, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    estado = models.CharField(max_length=1, choices=ESTADOS, default="A")

    # Muestra primero las vacantes registradas más recientemente
    class Meta:
        ordering = ["-id"]

    # Identifica la vacante en los formularios
    def __str__(self):
        return self.titulo


# Relaciona a cada candidato con su vacante y el estado de su postulación
class Candidato(models.Model):
    ESTADOS = [("P", "Pendiente"), ("A", "Aceptado"), ("R", "Rechazado")]
    nombre = models.CharField(max_length=150)
    correo = models.EmailField()
    vacante = models.ForeignKey(Vacante, on_delete=models.PROTECT, related_name="candidatos")
    estado = models.CharField(max_length=1, choices=ESTADOS, default="P")

    # Muestra primero las postulaciones registradas más recientemente
    class Meta:
        ordering = ["-id"]

    # Muestra el nombre del candidato
    def __str__(self):
        return self.nombre
