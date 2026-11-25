from django.db import models
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

# Create your models here.

class Nomina(models.Model):
    # El empleado pertenece al microservicio Usuarios.
    # Guardamos solamente su identificador externo.
    empleado_id = models.PositiveBigIntegerField(db_index=True)

    periodo = models.CharField(
        max_length=80,
        verbose_name="Periodo",
        help_text="Ejemplo: 1 al 15 de noviembre de 2026",
    )

    sueldo_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    bono = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )

    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )

    total = models.DecimalField(
        max_digits=13,
        decimal_places=2,
        editable=False,
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Nómina"
        verbose_name_plural = "Nóminas"

    def __str__(self):
        return f"Empleado #{self.empleado_id} · {self.periodo}"

    def clean(self):
        super().clean()

        valores = (
            self.sueldo_base,
            self.bono,
            self.descuento,
        )

        if all(
            isinstance(valor, Decimal) and valor.is_finite()
            for valor in valores
        ):
            if self.descuento > self.sueldo_base + self.bono:
                raise ValidationError({
                    "descuento": (
                        "El descuento no puede superar "
                        "el sueldo base más el bono."
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean(exclude=["total"])

        self.total = (
            self.sueldo_base
            + self.bono
            - self.descuento
        )

        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = (
                set(kwargs["update_fields"])
                | {
                    "sueldo_base",
                    "bono",
                    "descuento",
                    "total",
                }
            )

        super().save(*args, **kwargs)
