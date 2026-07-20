from __future__ import annotations

import datetime as dt

import pytest

from itc_deporte.domain.enfrentamiento import (
    Enfrentamiento,
    EstadoEnfrentamiento,
    Marcador,
    Parcial,
)
from itc_deporte.domain.errores import ErrorDeDominio


def enf(**cambios) -> Enfrentamiento:
    base = dict(id="e1", local="p1", visitante="p2")
    return Enfrentamiento(**{**base, **cambios})


class TestMarcador:
    def test_gana_local(self):
        m = Marcador(3, 1)
        assert m.gana_local and not m.gana_visitante and not m.es_empate

    def test_gana_visitante(self):
        m = Marcador(0, 2)
        assert m.gana_visitante and not m.gana_local and not m.es_empate

    def test_empate(self):
        m = Marcador(2, 2)
        assert m.es_empate and not m.gana_local and not m.gana_visitante

    def test_diferencia_es_positiva_si_gana_el_local(self):
        assert Marcador(4, 1).diferencia == 3
        assert Marcador(1, 4).diferencia == -3

    @pytest.mark.parametrize("local,visitante", [(-1, 0), (0, -1)])
    def test_rechaza_totales_negativos(self, local, visitante):
        with pytest.raises(ErrorDeDominio):
            Marcador(local, visitante)

    def test_los_parciales_son_opcionales(self):
        """Fútbol: el total basta, no hay detalle que registrar."""
        assert Marcador(2, 1).parciales == ()

    def test_invertido_intercambia_los_lados(self):
        m = Marcador(3, 1, (Parcial(25, 20), Parcial(18, 25)))
        invertido = m.invertido()
        assert (invertido.local, invertido.visitante) == (1, 3)
        assert invertido.parciales == (Parcial(20, 25), Parcial(25, 18))

    def test_invertir_dos_veces_devuelve_el_original(self):
        m = Marcador(3, 1, (Parcial(25, 20),))
        assert m.invertido().invertido() == m

    def test_es_inmutable(self):
        with pytest.raises(AttributeError):
            Marcador(1, 0).local = 5


class TestMarcadorPorSets:
    """El caso que el sistema anterior no podía representar."""

    def test_cuenta_sets_ganados_no_puntos(self):
        parciales = (Parcial(25, 20), Parcial(23, 25), Parcial(25, 18), Parcial(25, 22))
        m = Marcador.por_sets(parciales)
        assert (m.local, m.visitante) == (3, 1)

    def test_conserva_el_detalle_de_los_parciales(self):
        parciales = (Parcial(25, 20), Parcial(25, 18), Parcial(25, 22))
        assert Marcador.por_sets(parciales).parciales == parciales

    def test_el_total_no_es_la_suma_de_los_puntos(self):
        """Un 3-0 en sets con muchos puntos sigue siendo 3-0."""
        parciales = (Parcial(25, 23), Parcial(25, 23), Parcial(25, 23))
        m = Marcador.por_sets(parciales)
        assert (m.local, m.visitante) == (3, 0)

    def test_un_set_empatado_no_cuenta_para_nadie(self):
        m = Marcador.por_sets((Parcial(25, 25), Parcial(25, 20)))
        assert (m.local, m.visitante) == (1, 0)

    def test_sin_parciales_es_cero_a_cero(self):
        assert Marcador.por_sets(()) == Marcador(0, 0)


class TestMarcadorPorSuma:
    def test_suma_los_parciales(self):
        m = Marcador.por_suma((Parcial(1, 0), Parcial(2, 3)))
        assert (m.local, m.visitante) == (3, 3)

    def test_conserva_el_detalle(self):
        parciales = (Parcial(1, 0), Parcial(2, 3))
        assert Marcador.por_suma(parciales).parciales == parciales


class TestParcial:
    @pytest.mark.parametrize("local,visitante", [(-1, 0), (0, -5)])
    def test_rechaza_valores_negativos(self, local, visitante):
        with pytest.raises(ErrorDeDominio):
            Parcial(local, visitante)


class TestInvariantesDelEnfrentamiento:
    def test_rechaza_un_participante_contra_si_mismo(self):
        with pytest.raises(ErrorDeDominio):
            enf(local="p1", visitante="p1")

    def test_rechaza_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            enf(id="")

    def test_rechaza_finalizado_sin_marcador(self):
        """Un partido no puede estar cerrado y no tener resultado."""
        with pytest.raises(ErrorDeDominio):
            enf(estado=EstadoEnfrentamiento.FINALIZADO)

    def test_pendiente_admite_marcador_parcial(self):
        """Se puede ir cargando el resultado antes de cerrar el partido."""
        e = enf(marcador=Marcador(1, 0))
        assert not e.esta_finalizado

    def test_la_identidad_es_el_id(self):
        assert enf(local="p1", visitante="p2") == enf(local="p3", visitante="p4")
        assert enf(id="e1") != enf(id="e2")

    def test_no_se_compara_con_otros_tipos(self):
        assert enf() != "e1"


class TestResultado:
    def test_gana_el_local(self):
        e = enf().finalizar(Marcador(2, 1))
        assert e.ganador() == "p1"
        assert e.perdedor() == "p2"

    def test_gana_el_visitante(self):
        e = enf().finalizar(Marcador(0, 3))
        assert e.ganador() == "p2"
        assert e.perdedor() == "p1"

    def test_un_empate_no_tiene_ganador_ni_perdedor(self):
        e = enf().finalizar(Marcador(2, 2))
        assert e.ganador() is None
        assert e.perdedor() is None

    def test_un_partido_pendiente_no_tiene_ganador(self):
        """Aunque lleve un marcador cargado a favor de alguien."""
        assert enf(marcador=Marcador(3, 0)).ganador() is None

    def test_finalizar_devuelve_una_instancia_nueva(self):
        original = enf()
        cerrado = original.finalizar(Marcador(1, 0))
        assert original.estado is EstadoEnfrentamiento.PENDIENTE
        assert cerrado.esta_finalizado
        assert cerrado.marcador == Marcador(1, 0)

    def test_finalizar_conserva_el_resto_de_los_datos(self):
        fecha = dt.datetime(2026, 7, 25, 15, 0)
        cerrado = enf(fecha=fecha, jornada=3).finalizar(Marcador(1, 0))
        assert cerrado.fecha == fecha
        assert cerrado.jornada == 3
        assert cerrado.id == "e1"


class TestConsultas:
    def test_participa(self):
        e = enf()
        assert e.participa("p1") and e.participa("p2")
        assert not e.participa("p9")

    def test_rival_de(self):
        e = enf()
        assert e.rival_de("p1") == "p2"
        assert e.rival_de("p2") == "p1"

    def test_rival_de_un_ajeno_es_none(self):
        assert enf().rival_de("p9") is None

    def test_marcador_de_orienta_el_resultado(self):
        e = enf().finalizar(Marcador(3, 1))
        assert e.marcador_de("p1") == Marcador(3, 1)
        assert e.marcador_de("p2") == Marcador(1, 3)

    def test_marcador_de_un_ajeno_es_none(self):
        assert enf().finalizar(Marcador(1, 0)).marcador_de("p9") is None

    def test_marcador_de_sin_marcador_es_none(self):
        assert enf().marcador_de("p1") is None
