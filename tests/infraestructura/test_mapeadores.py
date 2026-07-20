"""Los mapeadores, con round-trip.

Esta es la parte de Supabase que **sí** se puede probar: es una función pura de
entidad a diccionario y vuelta. Un campo que se guarde y no se lea salta aquí,
sin necesidad de una base.

Lo que estos tests no dicen es si el diccionario resultante encaja con las
columnas reales de Supabase; eso lo comprueban los tests de contrato marcados
con `supabase`, que necesitan una instancia.
"""

from __future__ import annotations

import datetime as dt
import json

import pytest

from itc_deporte.domain.calendario import Calendario
from itc_deporte.domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    FaseDeGrupos,
    FaseEliminatoria,
    ReglasDeCompeticion,
)
from itc_deporte.domain.enfrentamiento import Enfrentamiento, Marcador, Parcial
from itc_deporte.domain.participante import Miembro, Participante
from itc_deporte.domain.reglas.desempate import PorEnfrentamientoDirecto, PorPuntos
from itc_deporte.domain.reglas.fixture import ConfigFixture
from itc_deporte.domain.reglas.puntuacion import PorSets, VictoriaDerrota
from itc_deporte.infraestructura.supabase import mapeadores as m

VOLEIBOL = Deporte("voleyball", "Voleyball", "🏐")


def es_serializable(dato) -> bool:
    """Lo que se manda a Supabase tiene que caber en JSON."""
    json.dumps(dato)
    return True


class TestReglas:
    def test_round_trip_por_defecto(self):
        original = ReglasDeCompeticion()
        assert m.reglas_desde_json(m.reglas_a_json(original)) == original

    def test_round_trip_por_sets(self):
        original = ReglasDeCompeticion(puntuacion=PorSets(umbral_ajustado=1))
        vuelta = m.reglas_desde_json(m.reglas_a_json(original))
        assert vuelta.puntuacion == PorSets(umbral_ajustado=1)

    def test_round_trip_del_desempate(self):
        original = ReglasDeCompeticion(
            desempate=(PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota()))
        )
        vuelta = m.reglas_desde_json(m.reglas_a_json(original))
        assert len(vuelta.desempate) == 2

    def test_el_enfrentamiento_directo_recibe_la_puntuacion_de_la_competicion(self):
        """No se guarda dos veces: se reconstruye desde la de la competición."""
        original = ReglasDeCompeticion(
            puntuacion=PorSets(),
            desempate=(PorPuntos(), PorEnfrentamientoDirecto(PorSets())),
        )
        vuelta = m.reglas_desde_json(m.reglas_a_json(original))
        assert vuelta.desempate[1].puntuacion == vuelta.puntuacion

    def test_es_serializable(self):
        assert es_serializable(m.reglas_a_json(ReglasDeCompeticion()))

    def test_sin_datos_devuelve_las_de_siempre(self):
        assert m.reglas_desde_json(None) == ReglasDeCompeticion()
        assert m.reglas_desde_json({}) == ReglasDeCompeticion()


class TestCalendario:
    def test_round_trip(self):
        original = Calendario(dia_de_la_semana=5, hora=dt.time(15, 0))
        assert m.calendario_desde_json(m.calendario_a_json(original)) == original

    def test_sin_dia_fijo(self):
        original = Calendario(hora=dt.time(9, 30), cadencia_dias=3)
        assert m.calendario_desde_json(m.calendario_a_json(original)) == original

    def test_es_serializable(self):
        assert es_serializable(m.calendario_a_json(Calendario(dia_de_la_semana=5)))

    def test_sin_datos_devuelve_el_de_siempre(self):
        assert m.calendario_desde_json(None) == Calendario()


class TestFases:
    def test_round_trip_de_grupos(self):
        original = FaseDeGrupos(
            "f1", "Liga", 0, config_fixture=ConfigFixture(jornadas_forzadas=7)
        )
        vuelta = m.fase_desde_fila(m.fase_a_fila(original, "c1"))
        assert isinstance(vuelta, FaseDeGrupos)
        assert vuelta.config_fixture.jornadas_forzadas == 7

    def test_round_trip_de_eliminatoria(self):
        original = FaseEliminatoria(
            "f2", "Copa", 1, fixture="eliminacion_directa", cupos=16
        )
        vuelta = m.fase_desde_fila(m.fase_a_fila(original, "c1"))
        assert isinstance(vuelta, FaseEliminatoria)
        assert vuelta.cupos == 16
        assert vuelta.fixture == "eliminacion_directa"

    def test_la_fila_lleva_la_competicion(self):
        fila = m.fase_a_fila(FaseDeGrupos("f1", "Liga", 0), "c1")
        assert fila["competicion_id"] == "c1"

    def test_admite_config_fixture_como_texto(self):
        """Algunos clientes devuelven jsonb ya decodificado y otros como texto."""
        fila = m.fase_a_fila(FaseDeGrupos("f1", "Liga", 0), "c1")
        fila["config_fixture"] = json.dumps(fila["config_fixture"])
        assert m.fase_desde_fila(fila).config_fixture == ConfigFixture()

    def test_es_serializable(self):
        assert es_serializable(m.fase_a_fila(FaseDeGrupos("f1", "Liga", 0), "c1"))


class TestCompeticion:
    @pytest.fixture
    def original(self):
        return Competicion(
            id="c1",
            nombre="Intercursos 2026",
            deporte=VOLEIBOL,
            temporada="2026",
            estado=EstadoCompeticion.EN_CURSO,
            fases=(FaseDeGrupos("f1", "Liga", 0),),
            reglas=ReglasDeCompeticion(puntuacion=PorSets()),
            calendario=Calendario(dia_de_la_semana=5),
        )

    def test_round_trip(self, original):
        fila = m.competicion_a_fila(original)
        vuelta = m.competicion_desde_fila(fila, VOLEIBOL, original.fases)
        assert vuelta.id == original.id
        assert vuelta.nombre == original.nombre
        assert vuelta.temporada == original.temporada
        assert vuelta.estado is original.estado

    def test_conserva_las_reglas(self, original):
        vuelta = m.competicion_desde_fila(m.competicion_a_fila(original), VOLEIBOL)
        assert vuelta.reglas.puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_conserva_el_calendario(self, original):
        vuelta = m.competicion_desde_fila(m.competicion_a_fila(original), VOLEIBOL)
        assert vuelta.calendario.dia_de_la_semana == 5

    def test_la_fila_referencia_el_deporte_por_id(self, original):
        assert m.competicion_a_fila(original)["deporte_id"] == "voleyball"

    def test_es_serializable(self, original):
        assert es_serializable(m.competicion_a_fila(original))

    def test_admite_reglas_como_texto(self, original):
        fila = m.competicion_a_fila(original)
        fila["reglas"] = json.dumps(fila["reglas"])
        assert m.competicion_desde_fila(fila, VOLEIBOL).calendario.dia_de_la_semana == 5


class TestDeporte:
    def test_round_trip(self):
        assert m.deporte_desde_fila(m.deporte_a_fila(VOLEIBOL)) == VOLEIBOL

    def test_sin_icono(self):
        ajedrez = Deporte("ajedrez", "Ajedrez")
        assert m.deporte_desde_fila(m.deporte_a_fila(ajedrez)) == ajedrez


class TestParticipante:
    def test_round_trip(self):
        original = Participante("p1", "Los Tigres", "c1", "601")
        assert m.participante_desde_fila(m.participante_a_fila(original)) == original

    def test_conserva_los_miembros(self):
        original = Participante(
            "p1", "Los Tigres", "c1", "601",
            miembros=(Miembro("m1", "Ana", 7), Miembro("m2", "Luis")),
        )
        vuelta = m.participante_desde_fila(
            m.participante_a_fila(original), tuple(m.miembros_a_filas(original))
        )
        assert vuelta.miembros == original.miembros

    def test_los_miembros_referencian_al_participante(self):
        original = Participante("p1", "X", "c1", miembros=(Miembro("m1", "Ana"),))
        assert m.miembros_a_filas(original)[0]["participante_id"] == "p1"

    def test_sin_miembros_no_produce_filas(self):
        assert m.miembros_a_filas(Participante("p1", "X", "c1")) == []

    def test_es_serializable(self):
        original = Participante("p1", "X", "c1", miembros=(Miembro("m1", "Ana", 7),))
        assert es_serializable(m.participante_a_fila(original))
        assert es_serializable(m.miembros_a_filas(original))


class TestEnfrentamiento:
    def test_round_trip_pendiente(self):
        original = Enfrentamiento(
            "e1", "p1", "p2", competicion_id="c1", fase_id="f1", jornada=3,
            fecha=dt.datetime(2026, 7, 25, 15, 0),
        )
        vuelta = m.enfrentamiento_desde_fila(m.enfrentamiento_a_fila(original))
        assert vuelta.id == original.id
        assert vuelta.local == "p1" and vuelta.visitante == "p2"
        assert vuelta.jornada == 3
        assert vuelta.fecha == original.fecha
        assert not vuelta.esta_finalizado

    def test_round_trip_finalizado(self):
        original = Enfrentamiento("e1", "p1", "p2", fase_id="f1").finalizar(
            Marcador(3, 1)
        )
        vuelta = m.enfrentamiento_desde_fila(
            m.enfrentamiento_a_fila(original), m.marcador_a_fila(original)
        )
        assert vuelta.esta_finalizado
        assert vuelta.marcador == Marcador(3, 1)

    def test_conserva_los_parciales(self):
        """Lo que hace expresable el voleibol tiene que sobrevivir al guardado."""
        marcador = Marcador.por_sets((Parcial(25, 20), Parcial(23, 25), Parcial(25, 18)))
        original = Enfrentamiento("e1", "p1", "p2").finalizar(marcador)
        vuelta = m.enfrentamiento_desde_fila(
            m.enfrentamiento_a_fila(original), m.marcador_a_fila(original)
        )
        assert vuelta.marcador == marcador
        assert vuelta.marcador.parciales == marcador.parciales

    def test_una_casilla_de_cuadro_conserva_ronda_y_slot(self):
        original = Enfrentamiento(
            "e1", None, None, competicion_id="c1", fase_id="f2", ronda=1, slot=0
        )
        vuelta = m.enfrentamiento_desde_fila(m.enfrentamiento_a_fila(original))
        assert (vuelta.ronda, vuelta.slot) == (1, 0)
        assert vuelta.local is None and vuelta.visitante is None

    def test_sin_marcador_no_produce_fila_de_marcador(self):
        assert m.marcador_a_fila(Enfrentamiento("e1", "p1", "p2")) is None

    def test_es_serializable(self):
        original = Enfrentamiento("e1", "p1", "p2", fase_id="f1").finalizar(
            Marcador(3, 1, (Parcial(25, 20),))
        )
        assert es_serializable(m.enfrentamiento_a_fila(original))
        assert es_serializable(m.marcador_a_fila(original))

    def test_admite_la_fecha_con_zona_horaria_de_postgres(self):
        fila = m.enfrentamiento_a_fila(Enfrentamiento("e1", "p1", "p2"))
        fila["fecha"] = "2026-07-25T15:00:00Z"
        assert m.enfrentamiento_desde_fila(fila).fecha is not None

    def test_admite_parciales_como_texto(self):
        original = Enfrentamiento("e1", "p1", "p2").finalizar(
            Marcador(1, 0, (Parcial(25, 20),))
        )
        fila = m.marcador_a_fila(original)
        fila["parciales"] = json.dumps(fila["parciales"])
        vuelta = m.enfrentamiento_desde_fila(m.enfrentamiento_a_fila(original), fila)
        assert vuelta.marcador.parciales == (Parcial(25, 20),)
