from django.test import TestCase
import json
import os
from unittest.mock import patch

# Create your tests here.

# Comprueba el funcionamiento de la API de Usuarios.
class UsuariosAPITests(TestCase):

    def setUp(self):
        self.token = "token-de-prueba"
        self.headers = {
            "HTTP_X_INTERNAL_TOKEN": self.token
        }

        parche = patch.dict(
            os.environ,
            {"USU_INTERNAL_TOKEN": self.token}
        )

        parche.start()
        self.addCleanup(parche.stop)

    # El estado del servicio debe responder correctamente.
    def test_estado(self):
        respuesta = self.client.get("/api/estado/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.json()["servicio"],
            "usuarios"
        )

    # No se permite consultar usuarios sin autorización.
    def test_sin_token(self):
        respuesta = self.client.get("/api/usuarios/1/")

        self.assertEqual(respuesta.status_code, 401)

    # Un identificador inexistente debe responder 404.
    def test_usuario_no_encontrado(self):
        respuesta = self.client.get(
            "/api/usuarios/999999/",
            **self.headers
        )

        self.assertEqual(respuesta.status_code, 404)

    # Una contraseña incorrecta no autentica.
    def test_credenciales_incorrectas(self):
        respuesta = self.client.post(
            "/api/autenticar/",
            data=json.dumps({
                "identificador": "usuario-inexistente",
                "password": "clave-de-prueba",
            }),
            content_type="application/json",
            **self.headers
        )

        self.assertEqual(respuesta.status_code, 401)