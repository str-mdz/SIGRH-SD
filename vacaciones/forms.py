from django import forms
from .models import Solicitud


class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ["fecha_inicio", "fecha_fin", "motivo"]
        labels = {"fecha_inicio": "Desde", "fecha_fin": "Hasta", "motivo": "Motivo (opcional)"}
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "motivo": forms.Textarea(attrs={"rows": 3}),
        }


class RevisionForm(forms.Form):
    decision = forms.ChoiceField(choices=[("A", "Aprobar"), ("R", "Rechazar")], label="Decisión")
    observaciones = forms.CharField(required=False, max_length=500, label="Comentario (opcional)", widget=forms.Textarea(attrs={"rows": 3}))
