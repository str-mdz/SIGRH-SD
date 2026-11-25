from django.test import TestCase

import json
import os

from datetime import date
from unittest.mock import patch
from .models import Solicitud


# Comprueba las reglas principales del servicio.
class VacacionesAPITests(TestCase):

    def setUp(self):
        self.headers = {
            "HTTP_X_INTERNAL_TOKEN": "token-pruebas"
        }

        entorno = patch.dict(
            os.environ,
            {"VAC_INTERNAL_TOKEN": "token-pruebas"}
        )
        entorno.start()
        self.addCleanup(entorno.stop)

        reloj = patch(
            "django.utils.timezone.localdate",
            return_value=date(2026, 6, 1)
        )
        reloj.start()
        self.addCleanup(reloj.stop)

        cliente = patch(
            "vacaciones.api.obtener_usuario",
            side_effect=self.usuario_falso
        )
        cliente.start()
        self.addCleanup(cliente.stop)

    # Simula Usuarios sin conectarse a otra base.
    def usuario_falso(self, usuario_id):
        return {
            "id": usuario_id,
            "activo": True,
            "administrador": usuario_id == 3,
            "dias_vacaciones": 12,
        }

    def enviar(self, ruta, datos):
        return self.client.post(
            ruta,
            data=json.dumps(datos),
            content_type="application/json",
            **self.headers
        )

    def solicitar(self, actor_id=1, inicio="2026-06-08",
                  fin="2026-06-12"):
        return self.enviar("/api/solicitudes/", {
            "actor_id": actor_id,
            "fecha_inicio": inicio,
            "fecha_fin": fin,
            "motivo": "Descanso",
        })

    # No acepta peticiones sin clave interna.
    def test_autorizacion(self):
        respuesta = self.client.get(
            "/api/solicitudes/?actor_id=1"
        )
        self.assertEqual(respuesta.status_code, 401)

    # Reserva cinco días y consulta el saldo.
    def test_solicitud_y_saldo(self):
        respuesta = self.solicitar()
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["dias"], 5)

        saldo = self.client.get(
            "/api/saldo/?actor_id=1",
            **self.headers
        ).json()

        self.assertEqual(saldo["total"], 12)
        self.assertEqual(saldo["pendientes"], 5)
        self.assertEqual(saldo["disponibles"], 7)

    # Rechaza fechas cruzadas o sin saldo.
    def test_validaciones(self):
        self.assertEqual(
            self.solicitar(
                inicio="2026-05-29"
            ).status_code,
            400
        )

        self.assertEqual(
            self.solicitar(
                inicio="2026-06-06",
                fin="2026-06-07"
            ).status_code,
            400
        )

        self.assertEqual(self.solicitar().status_code, 201)

        self.assertEqual(
            self.solicitar().status_code,
            400
        )

        self.assertEqual(
            self.solicitar(
                inicio="2026-06-15",
                fin="2026-06-30"
            ).status_code,
            400
        )

    # Rechazar libera saldo y no permite revisar dos veces.
    def test_rechazo_y_revision_unica(self):
        solicitud = self.solicitar().json()

        ruta = (
            f"/api/solicitudes/{solicitud['id']}/revision/"
        )

        respuesta = self.enviar(ruta, {
            "actor_id": 3,
            "decision": "R",
            "observaciones": "No autorizado",
        })

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["estado"], "R")

        self.assertEqual(
            self.enviar(ruta, {
                "actor_id": 3,
                "decision": "A"
            }).status_code,
            409
        )

        saldo = self.client.get(
            "/api/saldo/?actor_id=1",
            **self.headers
        ).json()

        self.assertEqual(saldo["disponibles"], 12)

    # Solo el propietario puede cancelar una pendiente.
    def test_cancelacion_y_privacidad(self):
        solicitud = self.solicitar().json()

        ruta = (
            f"/api/solicitudes/{solicitud['id']}/cancelar/"
        )

        self.assertEqual(
            self.enviar(ruta, {
                "actor_id": 2
            }).status_code,
            404
        )

        self.assertEqual(
            self.enviar(ruta, {
                "actor_id": 1
            }).status_code,
            200
        )

        self.assertEqual(
            self.enviar(ruta, {
                "actor_id": 1
            }).status_code,
            409
        )

        self.assertEqual(
            Solicitud.objects.get().estado,
            "C"
        )

    # Impide revisar solicitudes propias o sin permiso.
    def test_permisos_revision(self):
        solicitud = self.solicitar(actor_id=3).json()

        ruta = (
            f"/api/solicitudes/{solicitud['id']}/revision/"
        )

        self.assertEqual(
            self.enviar(ruta, {
                "actor_id": 3,
                "decision": "A"
            }).status_code,
            403
        )

        self.assertEqual(
            self.enviar(ruta, {
                "actor_id": 2,
                "decision": "A"
            }).status_code,
            403
        )
