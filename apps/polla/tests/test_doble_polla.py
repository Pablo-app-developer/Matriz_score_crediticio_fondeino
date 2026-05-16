from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.polla.models import Afiliado, InscripcionPolla

User = get_user_model()


class DoblePollaModeTest(TestCase):
    def _make_afiliado(self, cedula, pollas=1, motivo=None):
        afl = Afiliado.objects.create(
            cedula=cedula,
            nombre_completo=f'Afiliado {cedula}',
            cantidad_pollas=pollas,
            motivo_doble_polla=motivo,
        )
        InscripcionPolla.objects.create(afiliado=afl, numero_polla=1)
        if pollas == 2:
            InscripcionPolla.objects.create(afiliado=afl, numero_polla=2)
        return afl

    def test_afiliado_simple_tiene_una_inscripcion(self):
        afl = self._make_afiliado('1001', pollas=1)
        self.assertEqual(afl.inscripciones.count(), 1)

    def test_afiliado_doble_tiene_dos_inscripciones(self):
        afl = self._make_afiliado('1002', pollas=2, motivo='NUEVO')
        self.assertEqual(afl.inscripciones.count(), 2)

    def test_no_se_puede_crear_tercera_inscripcion(self):
        afl = self._make_afiliado('1003', pollas=2)
        with self.assertRaises(Exception):
            InscripcionPolla.objects.create(afiliado=afl, numero_polla=1)

    def test_ranking_contiene_dos_entradas_doble_polla(self):
        afl = self._make_afiliado('1004', pollas=2, motivo='AUMENTO')
        ranking_ids = list(
            InscripcionPolla.objects.filter(afiliado=afl).values_list('pk', flat=True)
        )
        self.assertEqual(len(ranking_ids), 2)

    def test_unique_together_impide_duplicado(self):
        afl = self._make_afiliado('1005', pollas=1)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            InscripcionPolla.objects.create(afiliado=afl, numero_polla=1)

    def test_motivo_doble_none_para_polla_simple(self):
        afl = self._make_afiliado('1006', pollas=1)
        self.assertIsNone(afl.motivo_doble_polla)

    def test_tiene_doble_polla_property(self):
        afl1 = self._make_afiliado('1007', pollas=1)
        afl2 = self._make_afiliado('1008', pollas=2, motivo='NUEVO')
        self.assertFalse(afl1.tiene_doble_polla)
        self.assertTrue(afl2.tiene_doble_polla)
