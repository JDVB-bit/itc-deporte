from __future__ import annotations

import pytest

from itc_deporte.domain.enfrentamiento import Marcador, Parcial
from itc_deporte.domain.errores import ReglaInvalida
from itc_deporte.domain.reglas.puntuacion import (
    PorSets,
    SistemaDePuntuacion,
    VictoriaDerrota,
)


class TestVictoriaDerrota:
    def test_por_defecto_reparte_3_1_0(self):
        """El comportamiento que el sistema aplicaba a todos los deportes."""
        regla = VictoriaDerrota()
        assert regla.puntos(Marcador(2, 1)) == (3, 0)
        assert regla.puntos(Marcador(1, 2)) == (0, 3)
        assert regla.puntos(Marcador(1, 1)) == (1, 1)

    def test_admite_otro_reparto(self):
        """Ligas con 2 puntos por victoria, sin tocar el código del motor."""
        regla = VictoriaDerrota(victoria=2, empate=1, derrota=0)
        assert regla.puntos(Marcador(3, 0)) == (2, 0)
        assert regla.puntos(Marcador(0, 0)) == (1, 1)

    def test_un_cero_a_cero_es_empate(self):
        assert VictoriaDerrota().puntos(Marcador(0, 0)) == (1, 1)

    def test_rechaza_que_empatar_pague_mas_que_ganar(self):
        with pytest.raises(ReglaInvalida):
            VictoriaDerrota(victoria=1, empate=3)

    def test_rechaza_que_perder_pague_mas_que_empatar(self):
        with pytest.raises(ReglaInvalida):
            VictoriaDerrota(victoria=3, empate=0, derrota=1)

    def test_admite_una_liga_sin_premio_al_empate(self):
        regla = VictoriaDerrota(victoria=1, empate=0, derrota=0)
        assert regla.puntos(Marcador(1, 1)) == (0, 0)


class TestPorSets:
    """La regla que el sistema anterior no podía expresar."""

    def test_una_victoria_holgada_da_3_0(self):
        assert PorSets().puntos(Marcador(3, 0)) == (3, 0)
        assert PorSets().puntos(Marcador(3, 1)) == (3, 0)

    def test_una_victoria_ajustada_da_2_1(self):
        """El 3-2 reparte: cinco sets no son un paseo."""
        assert PorSets().puntos(Marcador(3, 2)) == (2, 1)

    def test_respeta_el_lado_ganador(self):
        assert PorSets().puntos(Marcador(2, 3)) == (1, 2)
        assert PorSets().puntos(Marcador(0, 3)) == (0, 3)

    def test_un_empate_en_sets_es_un_dato_invalido(self):
        """Un partido de voleibol no puede terminar 2-2: bajo la regla vieja sí."""
        with pytest.raises(ReglaInvalida):
            PorSets().puntos(Marcador(2, 2))

    def test_el_umbral_de_ajustado_es_configurable(self):
        """En un formato a 3 sets, perder 1 ya cuenta como ajustado."""
        regla = PorSets(umbral_ajustado=1)
        assert regla.puntos(Marcador(2, 1)) == (2, 1)
        assert regla.puntos(Marcador(2, 0)) == (3, 0)

    def test_rechaza_que_la_victoria_ajustada_pague_mas_que_la_holgada(self):
        with pytest.raises(ReglaInvalida):
            PorSets(victoria=2, victoria_ajustada=3)

    def test_rechaza_que_la_derrota_holgada_pague_mas_que_la_ajustada(self):
        with pytest.raises(ReglaInvalida):
            PorSets(derrota_ajustada=0, derrota=1)

    def test_rechaza_un_umbral_de_cero(self):
        with pytest.raises(ReglaInvalida):
            PorSets(umbral_ajustado=0)


class TestPuntuacionSobreParciales:
    """El caso de punta a punta: sets reales convertidos en puntos de tabla."""

    def test_un_3_2_en_sets_reparte_2_1(self):
        parciales = (
            Parcial(25, 20),
            Parcial(23, 25),
            Parcial(25, 18),
            Parcial(20, 25),
            Parcial(15, 12),
        )
        marcador = Marcador.por_sets(parciales)
        assert (marcador.local, marcador.visitante) == (3, 2)
        assert PorSets().puntos(marcador) == (2, 1)

    def test_la_misma_regla_vieja_lo_habria_dado_por_3_0(self):
        """Contraste explícito con el comportamiento que se está sustituyendo."""
        marcador = Marcador(3, 2)
        assert VictoriaDerrota().puntos(marcador) == (3, 0)
        assert PorSets().puntos(marcador) == (2, 1)


class TestElProtocoloEsElSeam:
    @pytest.mark.parametrize("regla", [VictoriaDerrota(), PorSets()])
    def test_ambas_reglas_satisfacen_el_protocolo(self, regla):
        assert isinstance(regla, SistemaDePuntuacion)

    def test_el_motor_puede_usar_cualquier_regla_sin_conocerla(self):
        """OCP: una regla nueva no obliga a editar nada de lo anterior."""

        class SoloGanar:
            def puntos(self, marcador):
                return (1, 0) if marcador.gana_local else (0, 1)

        def total(regla, marcadores):
            return sum(regla.puntos(m)[0] for m in marcadores)

        marcadores = [Marcador(3, 0), Marcador(0, 3), Marcador(3, 2)]
        assert total(VictoriaDerrota(), marcadores) == 6
        assert total(PorSets(), marcadores) == 5
        assert total(SoloGanar(), marcadores) == 2
