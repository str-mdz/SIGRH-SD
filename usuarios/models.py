from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    # Usuario de Django con un cupo de vacaciones por año calendario

    dias_vacaciones = models.PositiveSmallIntegerField(
        default=12, verbose_name="Días de vacaciones por año"
    )

    def __str__(self):
        # Muestra el nombre o el identificador del empleado
        return self.get_full_name() or self.username
