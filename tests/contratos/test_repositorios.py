"""El contrato de los puertos, escrito una vez.

Cada clase `Contrato*` describe lo que debe cumplir cualquier implementación del
puerto. Las clases `Test*` del final lo ejecutan contra los repositorios en
memoria; cuando exista el adaptador de Supabase, heredará de las mismas clases y
correrá exactamente estas pruebas. Así el repositorio en memoria no puede
divergir del real sin que la suite lo diga.

pytest no recoge las clases `Contrato*` porque no empiezan por `Test`: solo se
ejecutan a través de quien las hereda.
"""

from __future__ import annotations

import pytest

from itc_deporte.aplicacion.puertos import (
    RepositorioDeCompeticiones,
    RepositorioDeEnfrentamientos,
    RepositorioDeParticipantes,
    RepositorioDePlantillas,
)
from itc_deporte.domain.competicion import Competicion, Deporte, FaseDeGrupos
from itc_deporte.domain.enfrentamiento import Enfrentamiento, Marcador
from itc_deporte.domain.participante import Participante
from itc_deporte.domain.plantilla import PlantillaDeCompeticion
from itc_deporte.infraestructura.memoria import (
    CompeticionesEnMemoria,
    EnfrentamientosEnMemoria,
    ParticipantesEnMemoria,
    PlantillasEnMemoria,
)

FUTBOL = Deporte("microfutbol", "Microfútbol", "⚽")


def competicion(id_="c1", nombre="Intercursos") -> Competicion:
    return Competicion(id=id_, nombre=nombre, deporte=FUTBOL)


def participante(id_="p1", competicion_id="c1", nombre="Los Tigres") -> Participante:
    return Participante(id=id_, nombre=nombre, competicion_id=competicion_id)


def enfrentamiento(
    id_="e1", local="p1", visitante="p2", fase_id="f1"
) -> Enfrentamiento:
    return Enfrentamiento(id_, local, visitante, fase_id=fase_id)


# ── Competiciones ────────────────────────────────────────────────────────────


class ContratoDeCompeticiones:
    @pytest.fixture
    def repositorio(self) -> RepositorioDeCompeticiones:
        raise NotImplementedError

    def test_satisface_el_puerto(self, repositorio):
        assert isinstance(repositorio, RepositorioDeCompeticiones)

    def test_lo_guardado_se_recupera(self, repositorio):
        repositorio.guardar(competicion())
        assert repositorio.obtener("c1").nombre == "Intercursos"

    def test_lo_que_no_existe_es_none(self, repositorio):
        assert repositorio.obtener("fantasma") is None

    def test_empieza_vacio(self, repositorio):
        assert repositorio.listar() == ()

    def test_listar_devuelve_todo(self, repositorio):
        repositorio.guardar(competicion("c1"))
        repositorio.guardar(competicion("c2"))
        assert {c.id for c in repositorio.listar()} == {"c1", "c2"}

    def test_guardar_dos_veces_sobrescribe(self, repositorio):
        repositorio.guardar(competicion(nombre="Vieja"))
        repositorio.guardar(competicion(nombre="Nueva"))
        assert len(repositorio.listar()) == 1
        assert repositorio.obtener("c1").nombre == "Nueva"

    def test_conserva_las_fases(self, repositorio):
        repositorio.guardar(competicion().con_fase(FaseDeGrupos("f1", "Grupos", 0)))
        assert len(repositorio.obtener("c1").fases) == 1

    def test_conserva_las_reglas(self, repositorio):
        repositorio.guardar(competicion())
        recuperada = repositorio.obtener("c1")
        assert recuperada.reglas.puntuacion.puntos(Marcador(2, 1)) == (3, 0)

    def test_eliminar_la_quita(self, repositorio):
        repositorio.guardar(competicion())
        repositorio.eliminar("c1")
        assert repositorio.obtener("c1") is None

    def test_eliminar_lo_que_no_existe_no_revienta(self, repositorio):
        repositorio.eliminar("fantasma")


# ── Participantes ────────────────────────────────────────────────────────────


class ContratoDeParticipantes:
    @pytest.fixture
    def repositorio(self) -> RepositorioDeParticipantes:
        raise NotImplementedError

    def test_satisface_el_puerto(self, repositorio):
        assert isinstance(repositorio, RepositorioDeParticipantes)

    def test_lo_guardado_se_recupera(self, repositorio):
        repositorio.guardar(participante())
        assert repositorio.obtener("p1").nombre == "Los Tigres"

    def test_lo_que_no_existe_es_none(self, repositorio):
        assert repositorio.obtener("fantasma") is None

    def test_filtra_por_competicion(self, repositorio):
        repositorio.guardar(participante("p1", competicion_id="c1"))
        repositorio.guardar(participante("p2", competicion_id="c1"))
        repositorio.guardar(participante("p3", competicion_id="c2"))
        assert {p.id for p in repositorio.de_competicion("c1")} == {"p1", "p2"}

    def test_una_competicion_sin_inscritos_da_vacio(self, repositorio):
        assert repositorio.de_competicion("c9") == ()

    def test_los_no_inscritos_no_salen_en_ninguna(self, repositorio):
        repositorio.guardar(participante("p1", competicion_id=None))
        assert repositorio.de_competicion("c1") == ()

    def test_guardar_dos_veces_sobrescribe(self, repositorio):
        repositorio.guardar(participante(nombre="Los Tigres"))
        repositorio.guardar(participante(nombre="Las Panteras"))
        assert len(repositorio.de_competicion("c1")) == 1
        assert repositorio.obtener("p1").nombre == "Las Panteras"

    def test_conserva_los_miembros(self, repositorio):
        from itc_deporte.domain.participante import Miembro

        repositorio.guardar(participante().con_miembro(Miembro("m1", "Ana", 7)))
        recuperado = repositorio.obtener("p1")
        assert recuperado.miembros == (Miembro("m1", "Ana", 7),)

    def test_eliminar_lo_quita(self, repositorio):
        repositorio.guardar(participante())
        repositorio.eliminar("p1")
        assert repositorio.obtener("p1") is None

    def test_eliminar_lo_que_no_existe_no_revienta(self, repositorio):
        repositorio.eliminar("fantasma")


# ── Enfrentamientos ──────────────────────────────────────────────────────────


class ContratoDeEnfrentamientos:
    @pytest.fixture
    def repositorio(self) -> RepositorioDeEnfrentamientos:
        raise NotImplementedError

    def test_satisface_el_puerto(self, repositorio):
        assert isinstance(repositorio, RepositorioDeEnfrentamientos)

    def test_lo_guardado_se_recupera_por_fase(self, repositorio):
        repositorio.guardar(enfrentamiento())
        assert len(repositorio.de_fase("f1")) == 1

    def test_se_recupera_por_id(self, repositorio):
        repositorio.guardar(enfrentamiento())
        assert repositorio.obtener("e1").local == "p1"

    def test_lo_que_no_existe_es_none(self, repositorio):
        assert repositorio.obtener("fantasma") is None

    def test_una_fase_sin_partidos_da_vacio(self, repositorio):
        assert repositorio.de_fase("f9") == ()

    def test_las_fases_no_se_mezclan(self, repositorio):
        repositorio.guardar(enfrentamiento("e1"))
        repositorio.guardar(enfrentamiento("e2", fase_id="f2"))
        assert {e.id for e in repositorio.de_fase("f1")} == {"e1"}

    def test_guardar_muchos_los_guarda_todos(self, repositorio):
        partidos = [enfrentamiento(f"e{i}", "p1", f"p{i + 2}") for i in range(5)]
        repositorio.guardar_muchos(partidos)
        assert len(repositorio.de_fase("f1")) == 5

    def test_guardar_muchos_sobre_lo_ya_guardado_actualiza(self, repositorio):
        repositorio.guardar(enfrentamiento("e1"))
        cerrado = enfrentamiento("e1").finalizar(Marcador(2, 0))
        repositorio.guardar_muchos([cerrado])
        assert len(repositorio.de_fase("f1")) == 1
        assert repositorio.obtener("e1").esta_finalizado

    def test_guardar_muchos_con_lista_vacia_no_hace_nada(self, repositorio):
        repositorio.guardar_muchos([])
        assert repositorio.de_fase("f1") == ()

    def test_conserva_el_marcador(self, repositorio):
        repositorio.guardar(enfrentamiento().finalizar(Marcador(3, 1)))
        assert repositorio.obtener("e1").marcador == Marcador(3, 1)

    def test_eliminar_de_fase_vacia_solo_esa_fase(self, repositorio):
        repositorio.guardar(enfrentamiento("e1"))
        repositorio.guardar(enfrentamiento("e2", fase_id="f2"))
        repositorio.eliminar_de_fase("f1")
        assert repositorio.de_fase("f1") == ()
        assert len(repositorio.de_fase("f2")) == 1

    def test_eliminar_una_fase_inexistente_no_revienta(self, repositorio):
        repositorio.eliminar_de_fase("fantasma")


# ── Plantillas ───────────────────────────────────────────────────────────────


class ContratoDePlantillas:
    @pytest.fixture
    def repositorio(self) -> RepositorioDePlantillas:
        raise NotImplementedError

    def test_satisface_el_puerto(self, repositorio):
        assert isinstance(repositorio, RepositorioDePlantillas)

    def test_lista_las_plantillas(self, repositorio):
        assert len(repositorio.listar()) >= 1

    def test_se_recupera_por_id(self, repositorio):
        alguna = repositorio.listar()[0]
        assert repositorio.obtener(alguna.id) == alguna

    def test_lo_que_no_existe_es_none(self, repositorio):
        assert repositorio.obtener("fantasma") is None


# ── Implementaciones ─────────────────────────────────────────────────────────


class TestCompeticionesEnMemoria(ContratoDeCompeticiones):
    @pytest.fixture
    def repositorio(self):
        return CompeticionesEnMemoria()


class TestParticipantesEnMemoria(ContratoDeParticipantes):
    @pytest.fixture
    def repositorio(self):
        return ParticipantesEnMemoria()


class TestEnfrentamientosEnMemoria(ContratoDeEnfrentamientos):
    @pytest.fixture
    def repositorio(self):
        return EnfrentamientosEnMemoria()


class TestPlantillasEnMemoria(ContratoDePlantillas):
    @pytest.fixture
    def repositorio(self):
        return PlantillasEnMemoria(
            [PlantillaDeCompeticion(id="basica", nombre="Liga", deporte=FUTBOL)]
        )


class TestConstruccionConDatosIniciales:
    """Los repositorios en memoria aceptan un estado de partida, que es lo que
    hace legibles los tests de casos de uso."""

    def test_competiciones(self):
        repo = CompeticionesEnMemoria([competicion("c1"), competicion("c2")])
        assert len(repo.listar()) == 2

    def test_participantes(self):
        repo = ParticipantesEnMemoria([participante("p1"), participante("p2")])
        assert len(repo.de_competicion("c1")) == 2

    def test_plantillas_desde_las_semillas(self):
        from itc_deporte.infraestructura.plantillas import cargar_semillas

        repo = PlantillasEnMemoria(cargar_semillas())
        assert repo.obtener("itc-voleyball") is not None
