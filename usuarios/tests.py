from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Usuario


# Comprueba el acceso al sistema y el registro de empleados
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AccesoTests(TestCase):
    # Un usuario nuevo inicia sesión sin asignarle roles adicionales
    def test_login_y_logout(self):
        Usuario.objects.create_user("E01", password="clave-prueba")
        respuesta = self.client.post(reverse("login"), {"id_empleado": "E01", "contrasenia": "clave-prueba"})
        self.assertRedirects(respuesta, reverse("dashboard"))
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    # Rechaza claves incorrectas y cuentas desactivadas
    def test_clave_incorrecta_e_inactivo(self):
        usuario = Usuario.objects.create_user("E01", password="clave-prueba")
        self.assertContains(self.client.post(reverse("login"), {"id_empleado": "E01", "contrasenia": "mal"}), "incorrectos")
        usuario.is_active = False
        usuario.save()
        self.assertContains(self.client.post(reverse("login"), {"id_empleado": "E01", "contrasenia": "clave-prueba"}), "incorrectos")

    # El superusuario crea empleados con una contraseña cifrada y cupo editable
    def test_crear_empleado_desde_admin(self):
        administrador = Usuario.objects.create_superuser("admin", "admin@example.com", "clave-prueba")
        self.client.force_login(administrador)
        respuesta = self.client.post(reverse("admin:usuarios_usuario_add"), {
            "username": "E09", "first_name": "Estrella", "last_name": "Mendoza",
            "email": "starmendozacamacho@gmail.com", "password1": "estrellabella9",
            "password2": "estrellabella9", "dias_vacaciones": 18,
        })
        self.assertEqual(respuesta.status_code, 302)
        empleado = Usuario.objects.get(username="E09")
        self.assertTrue(empleado.check_password("estrellabella9"))
        self.assertEqual(empleado.dias_vacaciones, 18)
        self.assertFalse(empleado.is_staff)

    # Todas las pantallas privadas redirigen al inicio de sesión
    def test_visitante_necesita_sesion(self):
        for nombre in ["dashboard", "solicitar_vacaciones", "ver_estatus_vacaciones", "revisar_solicitudes", "politicas"]:
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 302)
