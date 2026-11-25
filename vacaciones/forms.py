from django import forms

# Recibe las fechas sin guardar directamente en SQLite.
class SolicitudForm(forms.Form):
    fecha_inicio = forms.DateField(
        label="Desde",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d"
        )
    )

    fecha_fin = forms.DateField(
        label="Hasta",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d"
        )
    )

    motivo = forms.CharField(
        required=False,
        max_length=500,
        label="Motivo (opcional)",
        widget=forms.Textarea(attrs={"rows": 3})
    )


# Recibe la decisión de un administrador.
class RevisionForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[("A", "Aprobar"), ("R", "Rechazar")],
        label="Decisión"
    )

    observaciones = forms.CharField(
        required=False,
        max_length=500,
        label="Comentario (opcional)",
        widget=forms.Textarea(attrs={"rows": 3})
    )
