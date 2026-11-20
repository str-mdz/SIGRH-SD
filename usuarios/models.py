from django.contrib.auth.models import AbstractUser
from django.db import models


# Usuario de Django con un cupo de vacaciones por año calendario
class Usuario(AbstractUser):

    dias_vacaciones = models.PositiveSmallIntegerField(
        default=12, verbose_name="Días de vacaciones por año"
    )

    # Muestra el nombre o el identificador del empleado
    def __str__(self):
        return self.get_full_name() or self.username
