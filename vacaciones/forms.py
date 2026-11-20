from django import forms
from .models import Solicitud


# Recoge las fechas y el motivo de una solicitud de vacaciones
class SolicitudForm(forms.ModelForm):
    # Define los campos y controles que usa el formulario de vacaciones
    class Meta:
        model = Solicitud
        fields = ["fecha_inicio", "fecha_fin", "motivo"]
        labels = {"fecha_inicio": "Desde", "fecha_fin": "Hasta", "motivo": "Motivo (opcional)"}
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "motivo": forms.Textarea(attrs={"rows": 3}),
        }


# Recoge la decisión del administrador y su comentario
class RevisionForm(forms.Form):
    decision = forms.ChoiceField(choices=[("A", "Aprobar"), ("R", "Rechazar")], label="Decisión")
    observaciones = forms.CharField(required=False, max_length=500, label="Comentario (opcional)", widget=forms.Textarea(attrs={"rows": 3}))
