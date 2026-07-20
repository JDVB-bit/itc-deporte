"""El calendario de una competición.

Estos casos vivían en los tests de plantilla. Al retirarse las plantillas se
quedaron sin cubrir, y `Calendario` es código de dominio: no se queda sin tests.
"""

from __future__ import annotations

import datetime as dt

import pytest

from itc_deporte.domain.calendario import Calendario
from itc_deporte.domain.errores import ErrorDeDominio

LUNES = dt.date(2026, 7, 20)
SABADO = dt.date(2026, 7, 25)


class TestSinDiaFijo:
    def test_arranca_en_la_fecha_dada(self):
        cal = Calendario(hora=dt.time(9, 0))
        assert cal.fechas(LUNES, 2)[0] == dt.datetime(2026, 7, 20, 9, 0)

    def test_por_defecto_juega_a_las_tres(self):
        assert Calendario().fechas(LUNES, 1)[0].hour == 15


class TestConDiaFijo:
    def test_busca_el_siguiente_que_corresponda(self):
        """El 20/07/2026 es lunes; el sábado siguiente es el 25."""
        cal = Calendario(dia_de_la_semana=5)
        assert cal.fechas(LUNES, 1)[0].date() == SABADO

    def test_estando_en_el_dia_programa_para_el_siguiente(self):
        """Es lo que hacía el sorteo anterior con su `or 7`."""
        cal = Calendario(dia_de_la_semana=5)
        assert cal.fechas(SABADO, 1)[0].date() == dt.date(2026, 8, 1)

    def test_reproduce_el_calendario_con_el_que_opera_el_itc(self):
        cal = Calendario(dia_de_la_semana=5, hora=dt.time(15, 0))
        assert cal.fechas(LUNES, 3) == (
            dt.datetime(2026, 7, 25, 15, 0),
            dt.datetime(2026, 8, 1, 15, 0),
            dt.datetime(2026, 8, 8, 15, 0),
        )

    @pytest.mark.parametrize("dia", range(7))
    def test_cualquier_dia_de_la_semana_vale(self, dia):
        assert Calendario(dia_de_la_semana=dia).fechas(LUNES, 1)[0].weekday() == dia


class TestCadencia:
    def test_por_defecto_es_semanal(self):
        fechas = Calendario().fechas(LUNES, 2)
        assert (fechas[1] - fechas[0]).days == 7

    def test_es_configurable(self):
        fechas = Calendario(cadencia_dias=3).fechas(LUNES, 2)
        assert (fechas[1] - fechas[0]).days == 3

    def test_se_aplica_desde_la_primera_jornada(self):
        fechas = Calendario(dia_de_la_semana=5, cadencia_dias=14).fechas(LUNES, 2)
        assert fechas[0].date() == SABADO
        assert fechas[1].date() == dt.date(2026, 8, 8)


class TestInvariantes:
    def test_cero_fechas_es_vacio(self):
        assert Calendario().fechas(LUNES, 0) == ()

    def test_rechaza_una_cantidad_negativa(self):
        with pytest.raises(ErrorDeDominio):
            Calendario().fechas(LUNES, -1)

    @pytest.mark.parametrize("dia", [-1, 7, 99])
    def test_rechaza_un_dia_fuera_de_rango(self, dia):
        with pytest.raises(ErrorDeDominio):
            Calendario(dia_de_la_semana=dia)

    def test_rechaza_cadencia_de_cero_dias(self):
        with pytest.raises(ErrorDeDominio):
            Calendario(cadencia_dias=0)

    def test_es_inmutable(self):
        with pytest.raises(AttributeError):
            Calendario().cadencia_dias = 3
