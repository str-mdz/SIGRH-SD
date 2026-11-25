from decimal import Decimal
from django import forms


class NominaForm(forms.Form):
    empleado = forms.ChoiceField(
        label="Empleado",
        choices=[],
    )

    periodo = forms.CharField(
        max_length=80,
        label="Periodo",
        help_text="Ejemplo: 1 al 15 de noviembre de 2026",
    )

    sueldo_base = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        label="Sueldo base",
    )

    bono = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        label="Bono (opcional)",
    )

    descuento = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
        required=False,
        label="Descuento (opcional)",
    )

    def __init__(self, *args, empleados=None, **kwargs):
        super().__init__(*args, **kwargs)

        opciones = [("", "---------")]

        for usuario in empleados or []:
            nombre = " ".join(
                valor for valor in (
                    usuario.get("nombre", ""),
                    usuario.get("apellido", ""),
                )
                if valor
            )

            etiqueta = (
                f"{nombre} ({usuario['username']})"
                if nombre
                else usuario["username"]
            )

            opciones.append(
                (str(usuario["id"]), etiqueta)
            )

        self.fields["empleado"].choices = opciones

    def clean_bono(self):
        return (
            self.cleaned_data.get("bono")
            or Decimal("0")
        )

    def clean_descuento(self):
        return (
            self.cleaned_data.get("descuento")
            or Decimal("0")
        )

    def clean(self):
        datos = super().clean()

        sueldo = datos.get("sueldo_base")
        bono = datos.get("bono")
        descuento = datos.get("descuento")

        if None not in (sueldo, bono, descuento):
            if descuento > sueldo + bono:
                self.add_error(
                    "descuento",
                    "El descuento no puede superar "
                    "el sueldo base más el bono.",
                )

        return datos
