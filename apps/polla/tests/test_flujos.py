"""Tests de integración para flujos críticos de usuario."""
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import Usuario
from apps.polla.models import Afiliado, InscripcionPolla, ConfiguracionPolla


def _crear_usuario(username, rol, es_admin_polla=False):
    u = Usuario.objects.create_user(username=username, password='pass1234!', rol=rol)
    u.es_admin_polla = es_admin_polla
    u.save()
    return u


def _crear_afiliado(user=None, cedula='11111111', nombre='Test Afiliado', cantidad=1):
    afl = Afiliado.objects.create(
        cedula=cedula,
        nombre_completo=nombre,
        cantidad_pollas=cantidad,
        user=user,
    )
    InscripcionPolla.objects.create(afiliado=afl, numero_polla=1)
    if cantidad == 2:
        InscripcionPolla.objects.create(afiliado=afl, numero_polla=2)
    return afl


class AccesoModulosTest(TestCase):
    """ROL_POLLA no puede acceder a credito/nómina."""

    def setUp(self):
        ConfiguracionPolla.objects.get_or_create(pk=1)
        self.admin = _crear_usuario('admin1', Usuario.ROL_ADMIN)
        self.comite = _crear_usuario('comite1', Usuario.ROL_COMITE)
        self.polla_user = _crear_usuario('polla1', Usuario.ROL_POLLA)
        self.client = Client()

    def test_admin_accede_credito(self):
        self.client.login(username='admin1', password='pass1234!')
        r = self.client.get(reverse('credito:dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_comite_accede_credito(self):
        self.client.login(username='comite1', password='pass1234!')
        r = self.client.get(reverse('credito:dashboard'))
        self.assertEqual(r.status_code, 200)

    def test_polla_bloqueado_en_credito(self):
        self.client.login(username='polla1', password='pass1234!')
        r = self.client.get(reverse('credito:dashboard'))
        self.assertRedirects(r, reverse('polla:index'), fetch_redirect_response=False)

    def test_polla_bloqueado_en_nomina(self):
        self.client.login(username='polla1', password='pass1234!')
        r = self.client.get('/nomina/')
        self.assertRedirects(r, reverse('polla:index'), fetch_redirect_response=False)

    def test_no_autenticado_redirige_al_login(self):
        r = self.client.get(reverse('credito:dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])


class AdminPollaPermisoTest(TestCase):
    """es_admin_polla permite acceso a vistas de admin polla."""

    def setUp(self):
        ConfiguracionPolla.objects.get_or_create(pk=1)
        self.comite_sin_polla = _crear_usuario('comite2', Usuario.ROL_COMITE)
        self.comite_con_polla = _crear_usuario('comite3', Usuario.ROL_COMITE, es_admin_polla=True)
        self.client = Client()

    def test_comite_sin_permiso_bloqueado_en_admin_polla(self):
        self.client.login(username='comite2', password='pass1234!')
        r = self.client.get(reverse('polla:admin_afiliados'))
        self.assertRedirects(r, reverse('polla:index'), fetch_redirect_response=False)

    def test_comite_con_permiso_accede_admin_polla(self):
        self.client.login(username='comite3', password='pass1234!')
        r = self.client.get(reverse('polla:admin_afiliados'))
        self.assertEqual(r.status_code, 200)


class PanelSelectorTest(TestCase):
    """panel_selector redirige correctamente según rol."""

    def setUp(self):
        ConfiguracionPolla.objects.get_or_create(pk=1)
        self.admin = _crear_usuario('adm', Usuario.ROL_ADMIN)
        self.polla = _crear_usuario('pol', Usuario.ROL_POLLA)
        self.client = Client()

    def test_admin_ve_selector(self):
        self.client.login(username='adm', password='pass1234!')
        r = self.client.get(reverse('accounts:panel_selector'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'accounts/panel_selector.html')

    def test_polla_redirigido_al_index(self):
        self.client.login(username='pol', password='pass1234!')
        r = self.client.get(reverse('accounts:panel_selector'))
        self.assertRedirects(r, reverse('polla:index'), fetch_redirect_response=False)

    def test_no_autenticado_redirige_a_login(self):
        r = self.client.get(reverse('accounts:panel_selector'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])


class RegistroPollaTest(TestCase):
    """Flujo de auto-registro para participantes."""

    def setUp(self):
        ConfiguracionPolla.objects.get_or_create(pk=1)
        Afiliado.objects.create(cedula='99999999', nombre_completo='Juan Perez', activo=True)
        self.client = Client()

    def test_registro_exitoso_crea_usuario_y_vincula(self):
        r = self.client.post(reverse('polla:registro'), {
            'cedula': '99999999',
            'password1': 'ClaveSegura123!',
            'password2': 'ClaveSegura123!',
        })
        self.assertRedirects(r, reverse('polla:index'), fetch_redirect_response=False)
        u = Usuario.objects.get(username='99999999')
        self.assertEqual(u.rol, Usuario.ROL_POLLA)
        afl = Afiliado.objects.get(cedula='99999999')
        self.assertEqual(afl.user, u)

    def test_cedula_inexistente_rechazada(self):
        r = self.client.post(reverse('polla:registro'), {
            'cedula': '00000000',
            'password1': 'ClaveSegura123!',
            'password2': 'ClaveSegura123!',
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Usuario.objects.filter(username='00000000').exists())

    def test_usuario_ya_autenticado_redirige(self):
        u = _crear_usuario('ya_existe', Usuario.ROL_POLLA)
        self.client.login(username='ya_existe', password='pass1234!')
        r = self.client.get(reverse('polla:registro'))
        self.assertRedirects(r, reverse('polla:index'), fetch_redirect_response=False)


class EliminarAfiliadoTest(TestCase):
    """Admin puede eliminar afiliado e inscripcion individual."""

    def setUp(self):
        ConfiguracionPolla.objects.get_or_create(pk=1)
        self.admin = _crear_usuario('adm2', Usuario.ROL_ADMIN)
        self.client = Client()
        self.client.login(username='adm2', password='pass1234!')

    def test_eliminar_afiliado_sin_cuenta(self):
        afl = _crear_afiliado(cedula='55555555', nombre='Sin Cuenta')
        r = self.client.post(reverse('polla:admin_afiliado_eliminar', args=[afl.pk]))
        self.assertRedirects(r, reverse('polla:admin_afiliados'), fetch_redirect_response=False)
        self.assertFalse(Afiliado.objects.filter(pk=afl.pk).exists())

    def test_eliminar_afiliado_elimina_su_usuario(self):
        u = _crear_usuario('participante1', Usuario.ROL_POLLA)
        afl = _crear_afiliado(user=u, cedula='44444444', nombre='Con Cuenta')
        r = self.client.post(reverse('polla:admin_afiliado_eliminar', args=[afl.pk]))
        self.assertFalse(Afiliado.objects.filter(pk=afl.pk).exists())
        self.assertFalse(Usuario.objects.filter(pk=u.pk).exists())

    def test_eliminar_inscripcion_sin_pronosticos(self):
        afl = _crear_afiliado(cedula='33333333', nombre='Doble', cantidad=2)
        insc_b = InscripcionPolla.objects.get(afiliado=afl, numero_polla=2)
        r = self.client.post(reverse('polla:admin_inscripcion_eliminar', args=[insc_b.pk]))
        self.assertFalse(InscripcionPolla.objects.filter(pk=insc_b.pk).exists())
        afl.refresh_from_db()
        self.assertEqual(afl.cantidad_pollas, 1)

    def test_no_admin_bloqueado(self):
        comite = _crear_usuario('comite99', Usuario.ROL_COMITE)
        afl = _crear_afiliado(cedula='22222222', nombre='Test')
        c = Client()
        c.login(username='comite99', password='pass1234!')
        r = c.post(reverse('polla:admin_afiliado_eliminar', args=[afl.pk]))
        self.assertRedirects(r, reverse('polla:index'), fetch_redirect_response=False)
        self.assertTrue(Afiliado.objects.filter(pk=afl.pk).exists())
