from django.test import TestCase

from .consumidor import guardar_evento
from .models import VacacionAprobada


class PruebaIdempotencia(TestCase):

    def test_evento_repetido_no_duplica(self):
        mensaje = {
            "id": (
                "d580bcaa-34b4-4ec3-8bee-"
                "0025b79e52e1"
            ),
            "tipo": "vacaciones.aprobadas",
            "datos": {
                "solicitud_id": 7,
                "empleado_id": 2,
                "dias": 3,
                "fecha_inicio": "2026-12-01",
                "fecha_fin": "2026-12-03",
            },
        }

        # Primera recepción: crea un registro.
        self.assertTrue(
            guardar_evento(mensaje)
        )

        # Segunda recepción: ignora el duplicado.
        self.assertFalse(
            guardar_evento(mensaje)
        )

        self.assertEqual(
            VacacionAprobada.objects.count(),
            1,
        )
