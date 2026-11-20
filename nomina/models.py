from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


# Guarda los importes de la nómina de un empleado por periodo
class Nomina(models.Model):
    empleado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="nominas")
    periodo = models.CharField(max_length=80, verbose_name="Periodo", help_text="Ejemplo: 1 al 15 de noviembre de 2026")
    sueldo_base = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    bono = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"), blank=True, validators=[MinValueValidator(Decimal("0"))])
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"), blank=True, validators=[MinValueValidator(Decimal("0"))])
    total = models.DecimalField(max_digits=13, decimal_places=2, editable=False)

    # Muestra primero las nóminas más recientes y define su nombre en el administrador
    class Meta:
        ordering = ["-id"]
        verbose_name = "Nómina"
        verbose_name_plural = "Nóminas"

    # Identifica la nómina por empleado y periodo
    def __str__(self):
        return f"{self.empleado} · {self.periodo}"

    # Evita descuentos mayores al sueldo más el bono
    def clean(self):
        super().clean()
        valores = (self.sueldo_base, self.bono, self.descuento)
        if all(isinstance(valor, Decimal) and valor.is_finite() for valor in valores):
            if self.descuento > self.sueldo_base + self.bono:
                raise ValidationError({"descuento": "El descuento no puede superar el sueldo base más el bono."})

    # Calcula y valida el total antes de guardar la nómina
    def save(self, *args, **kwargs):
        self.full_clean(exclude=["total"])
        self.total = self.sueldo_base + self.bono - self.descuento
        # Mantiene el total y sus importes juntos incluso al guardar solo algunos campos
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"sueldo_base", "bono", "descuento", "total"}
        super().save(*args, **kwargs)
