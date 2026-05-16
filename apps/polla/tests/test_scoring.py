from django.test import TestCase
from unittest.mock import MagicMock
from apps.polla.scoring import calcular_puntos


def _config(pts_res_g=1, pts_marc_g=2, pts_res_e=2, pts_marc_e=4):
    c = MagicMock()
    c.pts_resultado_grupos = pts_res_g
    c.pts_marcador_grupos = pts_marc_g
    c.pts_resultado_eliminatoria = pts_res_e
    c.pts_marcador_eliminatoria = pts_marc_e
    return c


def _partido(fase='GRUPOS', gl=2, gv=1, finalizado=True):
    p = MagicMock()
    p.fase = fase
    p.goles_local = gl
    p.goles_visitante = gv
    p.finalizado = finalizado
    if gl is not None and gv is not None:
        p.resultado_texto = 'LOCAL' if gl > gv else ('VISITANTE' if gv > gl else 'EMPATE')
    else:
        p.resultado_texto = None
    p.es_eliminatoria = fase in ['TREINTA_DOS', 'OCTAVOS', 'CUARTOS', 'SEMIS', 'TERCERO', 'FINAL']
    return p


def _pronostico(gl, gv):
    p = MagicMock()
    p.goles_local = gl
    p.goles_visitante = gv
    p.resultado_pronosticado = 'LOCAL' if gl > gv else ('VISITANTE' if gv > gl else 'EMPATE')
    return p


class ScoringGruposTest(TestCase):
    def setUp(self):
        self.config = _config()
        self.partido = _partido('GRUPOS', 2, 1)

    def test_marcador_exacto_grupos(self):
        pron = _pronostico(2, 1)
        r = calcular_puntos(pron, self.partido, self.config)
        self.assertEqual(r['puntos'], 3)  # 1 resultado + 2 marcador
        self.assertTrue(r['acerto_resultado'])
        self.assertTrue(r['acerto_marcador'])

    def test_solo_resultado_grupos(self):
        pron = _pronostico(1, 0)  # gana local, marcador distinto
        r = calcular_puntos(pron, self.partido, self.config)
        self.assertEqual(r['puntos'], 1)
        self.assertTrue(r['acerto_resultado'])
        self.assertFalse(r['acerto_marcador'])

    def test_fallo_total_grupos(self):
        pron = _pronostico(0, 2)  # gana visitante
        r = calcular_puntos(pron, self.partido, self.config)
        self.assertEqual(r['puntos'], 0)
        self.assertFalse(r['acerto_resultado'])
        self.assertFalse(r['acerto_marcador'])

    def test_empate_acertado(self):
        partido_empate = _partido('GRUPOS', 1, 1)
        pron = _pronostico(1, 1)
        r = calcular_puntos(pron, partido_empate, self.config)
        self.assertEqual(r['puntos'], 3)
        self.assertTrue(r['acerto_marcador'])

    def test_partido_no_finalizado(self):
        partido = _partido('GRUPOS', None, None, finalizado=False)
        partido.goles_local = None
        pron = _pronostico(1, 0)
        r = calcular_puntos(pron, partido, self.config)
        self.assertEqual(r['puntos'], 0)

    def test_marcador_exacto_eliminatoria(self):
        partido = _partido('FINAL', 2, 1)
        pron = _pronostico(2, 1)
        r = calcular_puntos(pron, partido, self.config)
        self.assertEqual(r['puntos'], 6)  # 2 resultado + 4 marcador

    def test_solo_resultado_eliminatoria(self):
        partido = _partido('OCTAVOS', 2, 1)
        pron = _pronostico(1, 0)
        r = calcular_puntos(pron, partido, self.config)
        self.assertEqual(r['puntos'], 2)
        self.assertFalse(r['acerto_marcador'])
