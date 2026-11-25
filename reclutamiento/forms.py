from django import forms


class VacanteForm(forms.Form):
    titulo = forms.CharField(max_length=150, label="Título")

    descripcion = forms.CharField(
        label="Descripción",
        widget=forms.Textarea(attrs={"rows": 4})
    )

    estado = forms.ChoiceField(
        choices=[("A", "Abierta"), ("C", "Cerrada")],
        initial="A"
    )


class CandidatoForm(forms.Form):
    nombre = forms.CharField(max_length=150)
    correo = forms.EmailField()
    vacante = forms.ChoiceField()

    # Recibe las vacantes disponibles desde la API.
    def __init__(self, *args, vacantes=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["vacante"].choices = [
            (str(v["id"]), v["titulo"])
            for v in (vacantes or [])
            if v["estado"] == "A"
        ]


class EstadoCandidatoForm(forms.Form):
    estado = forms.ChoiceField(
        choices=[
            ("P", "Pendiente"),
            ("A", "Aceptado"),
            ("R", "Rechazado"),
        ]
    )
