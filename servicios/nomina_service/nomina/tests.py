from django.test import TestCase
import json
import os
from decimal import Decimal
from unittest.mock import patch
from django.core.exceptions import ValidationError
from .models import Nomina
from .usuarios_cliente import UsuarioAPIError

# Create your tests here.

def usuario_falso(usuario_id):
    usuarios = {
        1: {"id": 1, "activo": True, "administrador": True},
        2: {"id": 2, "activo": True, "administrador": False},
        3: {"id": 3, "activo": True, "administrador": False},
    }

    if usuario_id not in usuarios:
        raise UsuarioAPIError("Empleado no encontrado.", 404)

    return usuarios[usuario_id]


class NominaTests(TestCase):
    def setUp(self):
        self.token = os.environ["NOM_INTERNAL_TOKEN"]
        self.ruta = "/api/nominas/"

        self.datos = {
            "actor_id": 1,
            "empleado_id": 2,
            "periodo": "Prueba noviembre 2026",
            "sueldo_base": "10000.50",
            "bono": "500.25",
            "descuento": "100.10",
        }

    def publicar(self, datos, con_token=True):
        extras = {}

        if con_token:
            extras["HTTP_X_INTERNAL_TOKEN"] = self.token

        return self.client.post(
            self.ruta,
            data=json.dumps(datos),
            content_type="application/json",
            **extras,
        )

    def consultar(self, actor_id):
        return self.client.get(
            self.ruta,
            {"actor_id": actor_id},
            HTTP_X_INTERNAL_TOKEN=self.token,
        )

    def test_modelo_calcula_total(self):
        nomina = Nomina.objects.create(
            empleado_id=2,
            periodo="Noviembre",
            sueldo_base=Decimal("10000.50"),
            bono=Decimal("500.25"),
            descuento=Decimal("100.10"),
        )

        self.assertEqual(
            nomina.total,
            Decimal("10400.65")
        )

    def test_modelo_rechaza_descuento_excesivo(self):
        nomina = Nomina(
            empleado_id=2,
            periodo="Noviembre",
            sueldo_base=Decimal("100"),
            descuento=Decimal("101"),
        )

        with self.assertRaises(ValidationError):
            nomina.save()

    def test_sin_token_no_hay_acceso(self):
        respuesta = self.publicar(
            self.datos,
            con_token=False,
        )

        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(Nomina.objects.count(), 0)

    @patch(
        "nomina.api.obtener_usuario",
        side_effect=usuario_falso,
    )
    def test_administrador_registra(self, _mock):
        respuesta = self.publicar(self.datos)

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(
            respuesta.json()["total"],
            "10400.65"
        )
        self.assertEqual(Nomina.objects.count(), 1)

    @patch(
        "nomina.api.obtener_usuario",
        side_effect=usuario_falso,
    )
    def test_empleado_no_registra(self, _mock):
        datos = self.datos | {"actor_id": 2}
        respuesta = self.publicar(datos)

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Nomina.objects.exists())

    @patch(
        "nomina.api.obtener_usuario",
        side_effect=usuario_falso,
    )
    def test_empleado_solo_ve_sus_nominas(self, _mock):
        Nomina.objects.create(
            empleado_id=2,
            periodo="Propia",
            sueldo_base=Decimal("100"),
        )
        Nomina.objects.create(
            empleado_id=3,
            periodo="Privada",
            sueldo_base=Decimal("900"),
        )

        respuesta = self.consultar(2)

        self.assertEqual(respuesta.status_code, 200)
        registros = respuesta.json()["nominas"]

        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["periodo"], "Propia")

    @patch(
        "nomina.api.obtener_usuario",
        side_effect=usuario_falso,
    )
    def test_administrador_ve_todas(self, _mock):
        for empleado_id in (2, 3):
            Nomina.objects.create(
                empleado_id=empleado_id,
                periodo="Noviembre",
                sueldo_base=Decimal("100"),
            )

        respuesta = self.consultar(1)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            len(respuesta.json()["nominas"]),
            2,
        )

    @patch(
        "nomina.api.obtener_usuario",
        side_effect=usuario_falso,
    )
    def test_no_registra_empleado_inexistente(self, _mock):
        datos = self.datos | {"empleado_id": 999}
        respuesta = self.publicar(datos)

        self.assertEqual(respuesta.status_code, 404)
        self.assertFalse(Nomina.objects.exists())

    @patch(
        "nomina.api.obtener_usuario",
        side_effect=usuario_falso,
    )
    def test_importes_invalidos(self, _mock):
        casos = [
            {"sueldo_base": "-1"},
            {"sueldo_base": "texto"},
            {"sueldo_base": "1.001"},
            {"descuento": "999999"},
            {"bono": "-1"},
            {"descuento": "-1"},
            {"periodo": ""},
        ]

        for cambios in casos:
            with self.subTest(cambios=cambios):
                datos = self.datos | cambios
                respuesta = self.publicar(datos)
                self.assertEqual(
                    respuesta.status_code,
                    400,
                )

        self.assertFalse(Nomina.objects.exists())

    @patch(
        "nomina.api.obtener_usuario",
        side_effect=UsuarioAPIError(
            "Usuarios no disponible.", 503
        ),
    )
    def test_caida_de_usuarios(self, _mock):
        respuesta = self.publicar(self.datos)

        self.assertEqual(respuesta.status_code, 503)
        self.assertFalse(Nomina.objects.exists())
