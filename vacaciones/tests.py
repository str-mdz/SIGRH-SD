from datetime import date
from unittest.mock import patch
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from usuarios.models import Usuario
from .models import Solicitud
from .services import resumen_dias


# Comprueba las solicitudes, el saldo y los permisos de vacaciones
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class FlujoVacacionesTests(TestCase):
    # Prepara dos empleados, un administrador y una fecha fija
    def setUp(self):
        reloj = patch("django.utils.timezone.localdate", return_value=date(2026, 6, 1))
        reloj.start()
        self.addCleanup(reloj.stop)
        self.empleado = Usuario.objects.create_user("E01", password="clave-prueba", first_name="Ana")
        self.otro = Usuario.objects.create_user("E02", password="clave-prueba")
        self.admin = Usuario.objects.create_superuser("ADMIN", "admin@example.com", "clave-prueba")
        self.client.force_login(self.empleado)
        self.datos = {"fecha_inicio": "2026-06-08", "fecha_fin": "2026-06-12", "motivo": "Descanso"}

    # Envía el formulario con fechas válidas salvo las indicadas
    def solicitar(self, **cambios):
        return self.client.post(reverse("solicitar_vacaciones"), self.datos | cambios)

    # Comprueba el recorrido completo y la reserva correcta de cinco días
    def test_solicitar_aprobar_y_consultar(self):
        self.assertRedirects(self.solicitar(), reverse("ver_estatus_vacaciones"))
        solicitud = Solicitud.objects.get()
        self.assertEqual(solicitud.dias, 5)
        self.assertEqual(resumen_dias(self.empleado)["disponibles"], 7)
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("detalle_revision", args=[solicitud.pk]), {"decision": "A", "observaciones": "Autorizado"})
        self.assertRedirects(respuesta, reverse("revisar_solicitudes"))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "A")
        self.assertEqual(solicitud.revisor, self.admin)
        self.assertIsNotNone(solicitud.fecha_respuesta)
        self.assertEqual(resumen_dias(self.empleado), {"total": 12, "usados": 5, "pendientes": 0, "disponibles": 7})
        self.client.force_login(self.empleado)
        self.assertContains(self.client.get(reverse("ver_estatus_vacaciones")), "Autorizado")

    # El rechazo devuelve los días reservados al empleado
    def test_rechazar_libera_saldo(self):
        self.solicitar()
        solicitud = Solicitud.objects.get()
        self.client.force_login(self.admin)
        self.client.post(reverse("detalle_revision", args=[solicitud.pk]), {"decision": "R"})
        self.assertEqual(resumen_dias(self.empleado)["disponibles"], 12)

    # Cancelar una pendiente libera el saldo y registra su fecha final
    def test_cancelar_libera_saldo(self):
        self.solicitar()
        solicitud = Solicitud.objects.get()
        self.assertRedirects(self.client.post(reverse("cancelar_solicitud", args=[solicitud.pk])), reverse("ver_estatus_vacaciones"))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "C")
        self.assertIsNotNone(solicitud.fecha_respuesta)
        self.assertEqual(resumen_dias(self.empleado)["disponibles"], 12)

    # Rechaza fechas pasadas, invertidas, incompletas, futuras y sin días hábiles
    def test_fechas_invalidas(self):
        casos = [
            ("2026-05-29", "2026-06-01"), ("2026-06-12", "2026-06-08"),
            ("2027-01-04", "2027-01-05"), ("2026-12-31", "2027-01-01"),
            ("2026-06-06", "2026-06-07"), ("incorrecta", "2026-06-12"),
            ("", "2026-06-12"),
        ]
        for inicio, fin in casos:
            with self.subTest(inicio=inicio, fin=fin):
                respuesta = self.solicitar(fecha_inicio=inicio, fecha_fin=fin)
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(respuesta.context["form"].errors)
        self.assertFalse(Solicitud.objects.exists())

    # Una solicitud que supera el cupo no se guarda
    def test_no_exceder_cupo(self):
        respuesta = self.solicitar(fecha_fin="2026-06-30")
        self.assertContains(respuesta, "No tienes suficientes días")
        self.assertFalse(Solicitud.objects.exists())

    # Las pendientes también impiden reservar más días que el cupo
    def test_reservas_cuentan_para_solicitudes_nuevas(self):
        self.solicitar()
        respuesta = self.solicitar(fecha_inicio="2026-06-15", fecha_fin="2026-06-24")
        self.assertContains(respuesta, "No tienes suficientes días")
        self.assertEqual(Solicitud.objects.count(), 1)

    # Impide solapar tanto solicitudes pendientes como aprobadas
    def test_no_cruzar_solicitudes(self):
        self.solicitar()
        for estado in ["P", "A"]:
            Solicitud.objects.update(estado=estado)
            self.assertContains(self.solicitar(), "Las fechas coinciden")
        self.assertEqual(Solicitud.objects.count(), 1)

    # Permite volver a pedir un periodo rechazado
    def test_solicitar_despues_de_rechazo(self):
        self.solicitar()
        Solicitud.objects.update(estado="R")
        self.assertEqual(self.solicitar().status_code, 302)
        self.assertEqual(Solicitud.objects.count(), 2)

    # Un empleado no ve ni cancela solicitudes ajenas ni puede aprobarlas
    def test_privacidad_y_permisos(self):
        self.solicitar()
        solicitud = Solicitud.objects.get()
        self.client.force_login(self.otro)
        self.assertContains(self.client.get(reverse("ver_estatus_vacaciones")), "Todavía no tienes solicitudes")
        self.assertEqual(self.client.post(reverse("cancelar_solicitud", args=[solicitud.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("revisar_solicitudes")).status_code, 403)
        self.assertEqual(self.client.post(reverse("detalle_revision", args=[solicitud.pk]), {"decision": "A"}).status_code, 403)

    # El administrador necesita que otra persona revise sus vacaciones
    def test_admin_no_aprueba_solicitud_propia(self):
        self.client.force_login(self.admin)
        self.solicitar()
        solicitud = Solicitud.objects.get()
        self.assertEqual(self.client.post(reverse("detalle_revision", args=[solicitud.pk]), {"decision": "A"}).status_code, 403)

    # Una segunda decisión o una cancelación tardía no cambia el resultado
    def test_no_repetir_decision_ni_cancelar_aprobada(self):
        self.solicitar()
        solicitud = Solicitud.objects.get()
        self.client.force_login(self.admin)
        url = reverse("detalle_revision", args=[solicitud.pk])
        self.client.post(url, {"decision": "A"})
        self.client.post(url, {"decision": "R"})
        self.client.force_login(self.empleado)
        self.client.post(reverse("cancelar_solicitud", args=[solicitud.pk]))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "A")

    # Solo se aceptan aprobar y rechazar en el formulario de revisión
    def test_decision_invalida(self):
        self.solicitar()
        solicitud = Solicitud.objects.get()
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("detalle_revision", args=[solicitud.pk]), {"decision": "C"})
        self.assertTrue(respuesta.context["form"].errors)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "P")

    # Abrir una URL no cancela vacaciones ni cierra sesiones
    def test_get_no_modifica_datos(self):
        self.solicitar()
        solicitud = Solicitud.objects.get()
        self.assertEqual(self.client.get(reverse("cancelar_solicitud", args=[solicitud.pk])).status_code, 405)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("detalle_revision", args=[solicitud.pk])).status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "P")

    # Las solicitudes de escritura requieren el token del formulario
    def test_csrf_obligatorio(self):
        navegador = Client(enforce_csrf_checks=True)
        navegador.force_login(self.empleado)
        self.assertEqual(navegador.post(reverse("solicitar_vacaciones"), self.datos).status_code, 403)

    # El historial anterior no consume el cupo del nuevo año
    def test_saldo_nuevo_anio(self):
        self.solicitar()
        with patch("django.utils.timezone.localdate", return_value=date(2027, 1, 1)):
            self.assertEqual(resumen_dias(self.empleado)["disponibles"], 12)

    # Las pantallas principales se renderizan sin errores de plantilla
    def test_paginas_principales(self):
        for nombre in ["dashboard", "solicitar_vacaciones", "ver_estatus_vacaciones", "politicas"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("revisar_solicitudes")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:usuarios_usuario_add")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:usuarios_usuario_change", args=[self.empleado.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:vacaciones_solicitud_changelist")).status_code, 200)
