"""Editar un cuadro: quitar un resultado e intercambiar a dos participantes."""

from __future__ import annotations

import pytest

from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.errores import ErrorDeDominio
from itc_deporte.domain.motor.bracket import Bracket


def equipos(n: int) -> list[str]:
    return [f"p{i}" for i in range(1, n + 1)]


def gana_local(bracket, ronda, posicion):
    return bracket.con_resultado(ronda, posicion, Marcador(1, 0))


class TestSinResultado:
    def test_deja_la_casilla_pendiente(self):
        bracket = gana_local(Bracket.desde_clasificados(equipos(4)), 0, 0)
        assert bracket.sin_resultado(0, 0).slot(0, 0).marcador is None

    def test_el_ganador_sale_de_la_ronda_siguiente(self):
        bracket = gana_local(Bracket.desde_clasificados(equipos(4)), 0, 0)
        assert bracket.slot(1, 0).local == "p1"
        assert bracket.sin_resultado(0, 0).slot(1, 0).local is None

    def test_arrastra_lo_jugado_despues(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        bracket = gana_local(gana_local(bracket, 0, 0), 0, 1)
        bracket = gana_local(bracket, 1, 0)
        assert bracket.campeon() == "p1"
        limpio = bracket.sin_resultado(0, 0)
        assert limpio.campeon() is None
        assert limpio.slot(1, 0).marcador is None

    def test_no_toca_lo_que_no_depende_de_el(self):
        bracket = gana_local(gana_local(Bracket.desde_clasificados(equipos(4)), 0, 0), 0, 1)
        limpio = bracket.sin_resultado(0, 0)
        assert limpio.slot(0, 1).marcador == Marcador(1, 0)
        assert limpio.slot(1, 0).visitante == "p2"

    def test_devuelve_un_cuadro_nuevo(self):
        original = gana_local(Bracket.desde_clasificados(equipos(4)), 0, 0)
        original.sin_resultado(0, 0)
        assert original.slot(0, 0).marcador == Marcador(1, 0)

    def test_rechaza_una_casilla_sin_resultado(self):
        with pytest.raises(ErrorDeDominio, match="no tiene resultado"):
            Bracket.desde_clasificados(equipos(4)).sin_resultado(0, 0)

    def test_rechaza_una_casilla_inexistente(self):
        with pytest.raises(ErrorDeDominio):
            Bracket.desde_clasificados(equipos(4)).sin_resultado(9, 0)


class TestIntercambiar:
    def test_cambia_de_sitio_a_los_dos(self):
        bracket = Bracket.desde_clasificados(equipos(4)).intercambiar("p1", "p2")
        assert (bracket.slot(0, 0).local, bracket.slot(0, 1).local) == ("p2", "p1")

    def test_el_resto_queda_igual(self):
        bracket = Bracket.desde_clasificados(equipos(4)).intercambiar("p1", "p2")
        assert (bracket.slot(0, 0).visitante, bracket.slot(0, 1).visitante) == ("p4", "p3")

    def test_es_simetrico(self):
        original = Bracket.desde_clasificados(equipos(8))
        assert original.intercambiar("p1", "p8").intercambiar("p1", "p8") == original

    def test_un_participante_con_bye_se_puede_cambiar_por_otro(self):
        bracket = Bracket.desde_clasificados(equipos(3)).intercambiar("p1", "p3")
        assert bracket.slot(1, 0).local == "p3"  # el bye lo disfruta ahora p3

    def test_vuelve_a_propagar_los_byes(self):
        bracket = Bracket.desde_clasificados(equipos(5)).intercambiar("p1", "p5")
        assert {c.ganador() for c in bracket.rondas[0] if c.es_bye} == {"p5", "p2", "p3"}

    def test_nadie_se_pierde_ni_se_duplica(self):
        bracket = Bracket.desde_clasificados(equipos(6)).intercambiar("p2", "p6")
        presentes = [
            p for c in bracket.rondas[0] for p in (c.local, c.visitante) if p
        ]
        assert sorted(presentes) == equipos(6)

    def test_rechaza_intercambiar_a_alguien_consigo_mismo(self):
        with pytest.raises(ErrorDeDominio, match="distintos"):
            Bracket.desde_clasificados(equipos(4)).intercambiar("p1", "p1")

    def test_rechaza_a_un_ajeno(self):
        with pytest.raises(ErrorDeDominio, match="no está"):
            Bracket.desde_clasificados(equipos(4)).intercambiar("p1", "p9")

    def test_rechaza_si_ya_hay_resultados(self):
        bracket = gana_local(Bracket.desde_clasificados(equipos(4)), 0, 0)
        with pytest.raises(ErrorDeDominio, match="bórralos"):
            bracket.intercambiar("p1", "p2")

    def test_tras_borrar_los_resultados_ya_se_puede(self):
        bracket = gana_local(Bracket.desde_clasificados(equipos(4)), 0, 0)
        assert bracket.sin_resultado(0, 0).intercambiar("p1", "p2")
