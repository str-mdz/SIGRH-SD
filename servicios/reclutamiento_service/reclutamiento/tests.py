import json
import os
from unittest.mock import patch
from django.test import TestCase

from .models import Candidato, Vacante


# Comprueba la seguridad y las operaciones de Reclutamiento.
class APITests(TestCase):

    def setUp(self):
        self.token = "token-de-prueba"
        self.headers = {"HTTP_X_INTERNAL_TOKEN": self.token}

        parche = patch.dict(
            os.environ,
            {"RECL_INTERNAL_TOKEN": self.token}
        )
        parche.start()
        self.addCleanup(parche.stop)

    # Rechaza peticiones que no tengan la clave interna.
    def test_sin_autorizacion(self):
        respuesta = self.client.get("/api/vacantes/")
        self.assertEqual(respuesta.status_code, 401)

    # Registra una vacante y un candidato pendiente.
    def test_registrar_vacante_y_candidato(self):
        respuesta = self.client.post(
            "/api/vacantes/",
            data=json.dumps({
                "titulo": "Analista",
                "descripcion": "Análisis de datos",
                "estado": "A"
            }),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(respuesta.status_code, 201)
        vacante_id = respuesta.json()["id"]

        respuesta = self.client.post(
            "/api/candidatos/",
            data=json.dumps({
                "nombre": "Ana",
                "correo": "ana@example.com",
                "vacante": vacante_id
            }),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["estado"], "P")

    # Impide postular a una vacante cerrada.
    def test_vacante_cerrada(self):
        vacante = Vacante.objects.create(
            titulo="Soporte",
            descripcion="Atención técnica",
            estado="C"
        )

        respuesta = self.client.post(
            "/api/candidatos/",
            data=json.dumps({
                "nombre": "Luis",
                "correo": "luis@example.com",
                "vacante": vacante.pk
            }),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Candidato.objects.count(), 0)
