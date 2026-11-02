from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Usuario


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccesoTests(TestCase):
    def test_login_y_logout(self):
        # Un usuario nuevo inicia sesión sin asignarle roles adicionales
        Usuario.objects.create_user("E01", password="clave-prueba")
        respuesta = self.client.post(reverse("login"), {"id_empleado": "E01", "contrasenia": "clave-prueba"})
        self.assertRedirects(respuesta, reverse("dashboard"))
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_clave_incorrecta_e_inactivo(self):
        # Rechaza claves incorrectas y cuentas desactivadas
        usuario = Usuario.objects.create_user("E01", password="clave-prueba")
        self.assertContains(self.client.post(reverse("login"), {"id_empleado": "E01", "contrasenia": "mal"}), "incorrectos")
        usuario.is_active = False
        usuario.save()
        self.assertContains(self.client.post(reverse("login"), {"id_empleado": "E01", "contrasenia": "clave-prueba"}), "incorrectos")

    def test_crear_empleado_desde_admin(self):
        # El superusuario crea empleados con una contraseña cifrada y cupo editable
        administrador = Usuario.objects.create_superuser("admin", "admin@example.com", "clave-prueba")
        self.client.force_login(administrador)
        respuesta = self.client.post(reverse("admin:usuarios_usuario_add"), {
            "username": "E03", "first_name": "Laura", "last_name": "Pérez",
            "email": "laura@example.com", "password1": "Prueba-larga-824!",
            "password2": "Prueba-larga-824!", "dias_vacaciones": 18,
        })
        self.assertEqual(respuesta.status_code, 302)
        empleado = Usuario.objects.get(username="E03")
        self.assertTrue(empleado.check_password("Prueba-larga-824!"))
        self.assertEqual(empleado.dias_vacaciones, 18)
        self.assertFalse(empleado.is_staff)

    def test_visitante_necesita_sesion(self):
        # Todas las pantallas privadas redirigen al inicio de sesión
        for nombre in ["dashboard", "solicitar_vacaciones", "ver_estatus_vacaciones", "revisar_solicitudes", "politicas"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 302)
