from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from usuarios.models import Usuario
from .models import Nomina


# Comprueba los cálculos de nómina y la privacidad de cada empleado
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class NominaTests(TestCase):
    # Prepara dos empleados y un administrador que no es superusuario
    def setUp(self):
        self.admin = Usuario.objects.create_user("rrhh", password="prueba", is_staff=True)
        self.empleado = Usuario.objects.create_user("E01", password="prueba")
        self.otro = Usuario.objects.create_user("E02", password="prueba")
        self.client.force_login(self.admin)
        self.datos = {
            "empleado": self.empleado.pk, "periodo": "Primera quincena de noviembre de 2026",
            "sueldo_base": "10000.50", "bono": "500.25", "descuento": "100.10",
        }

    # Calcula con decimales e ignora un total manipulado desde el formulario
    def test_registro_y_total_automatico(self):
        respuesta = self.client.post(reverse("nomina:registrar"), self.datos | {"total": "1.00"})
        self.assertRedirects(respuesta, reverse("nomina:historial"))
        nomina = Nomina.objects.get()
        self.assertEqual(nomina.total, Decimal("10400.65"))
        self.assertEqual(nomina.empleado, self.empleado)
        self.assertEqual(nomina.periodo, self.datos["periodo"])

    # Los importes opcionales vacíos se guardan como cero
    def test_bono_y_descuento_opcionales(self):
        respuesta = self.client.post(reverse("nomina:registrar"), self.datos | {"bono": "", "descuento": ""})
        self.assertEqual(respuesta.status_code, 302)
        nomina = Nomina.objects.get()
        self.assertEqual(nomina.bono, Decimal("0.00"))
        self.assertEqual(nomina.descuento, Decimal("0.00"))
        self.assertEqual(nomina.total, Decimal("10000.50"))

    # Rechaza negativos, exceso de decimales, descuentos excesivos y empleados inexistentes
    def test_importes_y_datos_invalidos(self):
        casos = [
            {"sueldo_base": "-1"}, {"bono": "-1"}, {"descuento": "-1"},
            {"descuento": "20000"}, {"sueldo_base": "1.001"},
            {"sueldo_base": "texto"}, {"sueldo_base": "9999999999999"},
            {"periodo": ""}, {"empleado": 999999},
        ]
        for cambios in casos:
            with self.subTest(cambios=cambios):
                respuesta = self.client.post(reverse("nomina:registrar"), self.datos | cambios)
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(respuesta.context["form"].errors)
        self.assertFalse(Nomina.objects.exists())

    # Guardar directamente también calcula el total y valida los importes
    def test_modelo_recalcula_y_valida(self):
        nomina = Nomina.objects.create(empleado=self.empleado, periodo="Noviembre", sueldo_base="100.10", bono="0.20")
        self.assertEqual(nomina.total, Decimal("100.30"))
        nomina.bono = Decimal("1.20")
        nomina.save(update_fields=["bono"])
        nomina.refresh_from_db()
        self.assertEqual(nomina.total, Decimal("101.30"))
        nomina.descuento = Decimal("999")
        with self.assertRaises(ValidationError):
            nomina.save()

    # Los parámetros enviados por el empleado no permiten consultar registros ajenos
    def test_empleado_solo_consulta_nominas_propias(self):
        propia = Nomina.objects.create(empleado=self.empleado, periodo="Periodo propio", sueldo_base=Decimal("100"))
        Nomina.objects.create(empleado=self.otro, periodo="Periodo privado de E02", sueldo_base=Decimal("900"))
        self.client.force_login(self.empleado)
        respuesta = self.client.get(reverse("nomina:historial"), {"empleado": self.otro.pk})
        self.assertQuerySetEqual(respuesta.context["nominas"], [propia])
        self.assertContains(respuesta, "Periodo propio")
        self.assertNotContains(respuesta, "Periodo privado de E02")
        self.assertNotContains(respuesta, reverse("nomina:registrar"))

    # Un usuario staff puede consultar las nóminas de todos los empleados
    def test_administrador_consulta_todas(self):
        for empleado in [self.empleado, self.otro]:
            Nomina.objects.create(empleado=empleado, periodo="Noviembre", sueldo_base=Decimal("100"))
        respuesta = self.client.get(reverse("nomina:historial"))
        self.assertEqual(len(respuesta.context["nominas"]), 2)
        self.assertContains(respuesta, reverse("nomina:registrar"))

    # Rechaza el formulario y el envío directo de un empleado
    def test_empleado_no_registra_nominas(self):
        self.client.force_login(self.empleado)
        self.assertEqual(self.client.get(reverse("nomina:registrar")).status_code, 403)
        self.assertEqual(self.client.post(reverse("nomina:registrar"), self.datos).status_code, 403)
        self.assertFalse(Nomina.objects.exists())

    # Protege las dos rutas frente a visitantes sin sesión
    def test_visitante_necesita_sesion(self):
        self.client.logout()
        for nombre in ["nomina:historial", "nomina:registrar"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 302)
            self.assertEqual(self.client.post(reverse(nombre), self.datos).status_code, 302)

    # Reutiliza el panel y muestra las opciones del menú según los permisos
    def test_plantillas_menu_y_get_sin_cambios(self):
        for nombre in ["nomina:historial", "nomina:registrar"]:
            respuesta = self.client.get(reverse(nombre))
            self.assertEqual(respuesta.status_code, 200)
            self.assertTemplateUsed(respuesta, "base.html")
            self.assertContains(respuesta, 'class="sidebar"')
        self.assertFalse(Nomina.objects.exists())
        respuesta = self.client.get(reverse("dashboard"))
        self.assertContains(respuesta, reverse("reclutamiento:inicio"))
        self.assertContains(respuesta, reverse("nomina:historial"))
        self.client.force_login(self.empleado)
        respuesta = self.client.get(reverse("dashboard"))
        self.assertNotContains(respuesta, reverse("reclutamiento:inicio"))
        self.assertContains(respuesta, reverse("nomina:historial"))

    # El alta de nóminas exige el token del formulario
    def test_csrf_obligatorio(self):
        navegador = Client(enforce_csrf_checks=True)
        navegador.force_login(self.admin)
        self.assertEqual(navegador.post(reverse("nomina:registrar"), self.datos).status_code, 403)
        self.assertFalse(Nomina.objects.exists())
