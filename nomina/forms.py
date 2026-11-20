from decimal import Decimal
from django import forms
from .models import Nomina


# Recoge los importes de la nómina sin permitir capturar el total
class NominaForm(forms.ModelForm):
    # Define los campos de captura y señala los importes opcionales
    class Meta:
        model = Nomina
        fields = ["empleado", "periodo", "sueldo_base", "bono", "descuento"]
        labels = {"bono": "Bono (opcional)", "descuento": "Descuento (opcional)"}

    # Usa cero cuando no se captura un bono
    def clean_bono(self):
        return self.cleaned_data.get("bono") or Decimal("0")

    # Usa cero cuando no se captura un descuento
    def clean_descuento(self):
        return self.cleaned_data.get("descuento") or Decimal("0")
