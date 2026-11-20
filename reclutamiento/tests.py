from django.test import Client, TestCase, override_settings
from django.urls import reverse
from usuarios.models import Usuario
from .models import Candidato, Vacante


# Comprueba el registro de vacantes, candidatos y los permisos de acceso
@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ReclutamientoTests(TestCase):
    # Prepara un administrador sin permisos de superusuario y un empleado
    def setUp(self):
        self.admin = Usuario.objects.create_user("rrhh", password="prueba", is_staff=True)
        self.empleado = Usuario.objects.create_user("empleado", password="prueba")
        self.vacante = Vacante.objects.create(titulo="Auxiliar", descripcion="Apoyo administrativo")
        self.candidato = Candidato.objects.create(nombre="Ana", correo="ana@example.com", vacante=self.vacante)
        self.client.force_login(self.admin)
        self.rutas = [
            reverse("reclutamiento:inicio"),
            reverse("reclutamiento:registrar_vacante"),
            reverse("reclutamiento:editar_vacante", args=[self.vacante.pk]),
            reverse("reclutamiento:registrar_candidato"),
            reverse("reclutamiento:estado_candidato", args=[self.candidato.pk]),
        ]

    # Un administrador registra una vacante y una postulación pendiente
    def test_registrar_vacante_y_candidato(self):
        respuesta = self.client.post(reverse("reclutamiento:registrar_vacante"), {
            "titulo": "Recepción", "descripcion": "Atención a visitantes", "estado": "A",
        })
        self.assertRedirects(respuesta, reverse("reclutamiento:inicio"))
        vacante = Vacante.objects.get(titulo="Recepción")
        respuesta = self.client.post(reverse("reclutamiento:registrar_candidato"), {
            "nombre": "Luis", "correo": "luis@example.com", "vacante": vacante.pk, "estado": "A",
        })
        self.assertRedirects(respuesta, reverse("reclutamiento:inicio"))
        candidato = Candidato.objects.get(nombre="Luis")
        self.assertEqual(candidato.estado, "P")
        self.assertEqual(candidato.vacante, vacante)
        self.assertContains(self.client.get(reverse("reclutamiento:inicio")), "luis@example.com")

    # El cambio de estado conserva la vacante y sus candidatos
    def test_cerrar_y_reabrir_vacante(self):
        url = reverse("reclutamiento:editar_vacante", args=[self.vacante.pk])
        for estado in ["C", "A"]:
            respuesta = self.client.post(url, {"titulo": "Auxiliar", "descripcion": "Actualizada", "estado": estado})
            self.assertEqual(respuesta.status_code, 302)
            self.vacante.refresh_from_db()
            self.assertEqual(self.vacante.estado, estado)
            self.assertTrue(Candidato.objects.filter(pk=self.candidato.pk).exists())

    # Permite los tres estados y rechaza valores desconocidos
    def test_cambiar_estado_candidato(self):
        url = reverse("reclutamiento:estado_candidato", args=[self.candidato.pk])
        for estado in ["A", "R", "P"]:
            self.assertEqual(self.client.post(url, {"estado": estado}).status_code, 302)
            self.candidato.refresh_from_db()
            self.assertEqual(self.candidato.estado, estado)
        respuesta = self.client.post(url, {"estado": "X"})
        self.assertTrue(respuesta.context["form"].errors)
        self.candidato.refresh_from_db()
        self.assertEqual(self.candidato.estado, "P")

    # No guarda registros incompletos, correos inválidos ni vacantes inexistentes
    def test_formularios_invalidos(self):
        self.assertTrue(self.client.post(reverse("reclutamiento:registrar_vacante"), {}).context["form"].errors)
        datos = {"nombre": "Pedro", "correo": "correo-invalido", "vacante": self.vacante.pk}
        self.assertTrue(self.client.post(reverse("reclutamiento:registrar_candidato"), datos).context["form"].errors)
        datos.update(correo="pedro@example.com", vacante=999999)
        self.assertTrue(self.client.post(reverse("reclutamiento:registrar_candidato"), datos).context["form"].errors)
        self.assertEqual(Vacante.objects.count(), 1)
        self.assertEqual(Candidato.objects.count(), 1)

    # Una vacante cerrada conserva su historial pero no recibe nuevos candidatos
    def test_no_postular_a_vacante_cerrada(self):
        self.vacante.estado = "C"
        self.vacante.save()
        respuesta = self.client.post(reverse("reclutamiento:registrar_candidato"), {
            "nombre": "Luis", "correo": "luis@example.com", "vacante": self.vacante.pk,
        })
        self.assertTrue(respuesta.context["form"].errors)
        self.assertEqual(Candidato.objects.count(), 1)

    # Bloquea lectura y escritura aunque se conozcan las rutas
    def test_empleado_no_accede_a_ninguna_vista(self):
        self.client.force_login(self.empleado)
        for url in self.rutas:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, {"estado": "A"}).status_code, 403)
        self.candidato.refresh_from_db()
        self.assertEqual(self.candidato.estado, "P")

    # Las rutas de reclutamiento exigen autenticación
    def test_visitante_necesita_sesion(self):
        self.client.logout()
        for url in self.rutas:
            self.assertEqual(self.client.get(url).status_code, 302)
            self.assertEqual(self.client.post(url).status_code, 302)

    # Las pantallas usan el panel existente y abrirlas no cambia registros
    def test_plantillas_y_get_sin_cambios(self):
        for url in self.rutas:
            respuesta = self.client.get(url)
            self.assertEqual(respuesta.status_code, 200)
            self.assertTemplateUsed(respuesta, "base.html")
            self.assertContains(respuesta, 'class="sidebar"')
        self.candidato.refresh_from_db()
        self.assertEqual(self.candidato.estado, "P")
        self.assertEqual(Vacante.objects.count(), 1)
        self.assertEqual(Candidato.objects.count(), 1)

    # Protege los formularios y devuelve 404 para identificadores desconocidos
    def test_csrf_y_registros_inexistentes(self):
        navegador = Client(enforce_csrf_checks=True)
        navegador.force_login(self.admin)
        self.assertEqual(navegador.post(reverse("reclutamiento:registrar_vacante"), {}).status_code, 403)
        self.assertEqual(self.client.get(reverse("reclutamiento:editar_vacante", args=[999999])).status_code, 404)
        self.assertEqual(self.client.get(reverse("reclutamiento:estado_candidato", args=[999999])).status_code, 404)
