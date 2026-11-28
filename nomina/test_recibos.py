from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase

from .recibos import descargar


class RecibosPDFTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/nomina/recibo/9/")
        self.request.user = SimpleNamespace(
            is_authenticated=True,
            pk=2,
            get_username=lambda: "ana",
        )
        self.empleados = [
            {"id": 2, "username": "ana", "nombre": "Ana", "apellido": "Prueba"},
        ]
        self.nominas = {
            "nominas": [
                {"id": 9, "empleado_id": 2, "periodo": "2026-11", "sueldo_base": "1000.00", "bono": "100.00", "descuento": "20.00", "total": "1080.00"},
            ]
        }

    @patch("nomina.recibos.nomina_api")
    @patch("nomina.recibos.catalogo_empleados")
    def test_crea_pdf_valido(self, catalogo, nominas):
        catalogo.return_value = self.empleados
        nominas.return_value = self.nominas
        respuesta = descargar(self.request, 9)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/pdf")
        self.assertTrue(respuesta.content.startswith(b"%PDF-"))
        nominas.assert_called_once_with(
            "GET", "nominas/", parametros={"actor_id": 2}
        )

    @patch("nomina.recibos.catalogo_empleados")
    def test_rechaza_identidad_no_coincidente(self, catalogo):
        catalogo.return_value = [
            {"id": 2, "username": "otra_persona"},
        ]
        with self.assertRaises(PermissionDenied):
            descargar(self.request, 9)

    @patch("nomina.recibos.nomina_api")
    @patch("nomina.recibos.catalogo_empleados")
    def test_no_revela_nomina_ajena(self, catalogo, nominas):
        catalogo.return_value = self.empleados
        nominas.return_value = {"nominas": []}
        with self.assertRaises(Http404):
            descargar(self.request, 42)
