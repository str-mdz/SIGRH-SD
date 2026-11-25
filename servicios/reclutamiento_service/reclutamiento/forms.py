from django import forms
from .models import Candidato, Vacante


# Permite registrar o editar los datos de una vacante
class VacanteForm(forms.ModelForm):
    # Define los campos editables y el espacio para describir el puesto
    class Meta:
        model = Vacante
        fields = ["titulo", "descripcion", "estado"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 4})}


# Recoge los datos del candidato y la vacante a la que postula
class CandidatoForm(forms.ModelForm):
    # Limita el registro a los datos personales y la vacante
    class Meta:
        model = Candidato
        fields = ["nombre", "correo", "vacante"]

    # Permite registrar postulaciones únicamente en vacantes abiertas
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vacante"].queryset = Vacante.objects.filter(estado="A")
        self.fields["vacante"].help_text = "Selecciona una vacante abierta"


# Permite modificar únicamente el estado de la postulación
class EstadoCandidatoForm(forms.ModelForm):
    # Limita la edición al estado del candidato
    class Meta:
        model = Candidato
        fields = ["estado"]
