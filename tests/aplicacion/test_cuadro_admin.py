"""Borrar y editar el cuadro final: solo el Admin, y sin dejar nada a medias."""

from __future__ import annotations

import datetime as dt
import random

import pytest

from itc_deporte.aplicacion.errores import NoEncontrado
from itc_deporte.aplicacion.permisos import (
    ANONIMO, Concesion, Identidad, PermisoDenegado, Rol,
)
from itc_deporte.aplicacion.servicios import ServicioDeSorteo
from itc_deporte.domain.calendario import Calendario
from itc_deporte.domain.competicion import (
    Competicion, Deporte, FaseDeGrupos, FaseEliminatoria,
)
from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.errores import ErrorDeDominio
from itc_deporte.domain.reglas.fixture import ConfigFixture
from itc_deporte.infraestructura.autenticacion import (
    AutenticadorEnMemoria, ConcesionesEnMemoria,
)
from itc_deporte.infraestructura.memoria import (
    CompeticionesEnMemoria, EnfrentamientosEnMemoria, ParticipantesEnMemoria,
)
from itc_deporte.ui.composicion import ensamblar

ADMIN = Identidad("admin", "admin@itc.edu.co")
PROFE = Identidad("profe", "profe@itc.edu.co")
CURIOSO = Identidad("curioso", "curioso@itc.edu.co")
LUNES = dt.date(2026, 7, 20)


@pytest.fixture
def mundo():
    repos = (
        CompeticionesEnMemoria(), ParticipantesEnMemoria(), EnfrentamientosEnMemoria(),
        ConcesionesEnMemoria(
            [Concesion("admin", Rol.ADMIN), Concesion("profe", Rol.REGISTRADOR, "c1")]
        ),
    )
    servicios = ensamblar(repos, AutenticadorEnMemoria([ADMIN, PROFE, CURIOSO]))
    servicios.competiciones.crear(
        ADMIN,
        Competicion(
            id="c1", nombre="Prueba", deporte=Deporte("micro", "Micro", "⚽"),
            fases=(
                FaseDeGrupos("c1:0", "Grupos", 0, config_fixture=ConfigFixture()),
                FaseEliminatoria("c1:1", "Cuadro", 1, fixture="eliminacion_directa", cupos=8),
            ),
            calendario=Calendario(dia_de_la_semana=5, hora=dt.time(15, 0)),
        ),
    )
    for i in range(1, 5):
        servicios.inscripciones.inscribir(ADMIN, "c1", f"p{i}", f"Equipo {i}", "601")
    ServicioDeSorteo(
        repos[0], repos[1], repos[2], servicios.politica, azar=random.Random(1)
    ).sortear(ADMIN, "c1", "c1:0", desde=LUNES)
    servicios.cuadro.generar(ADMIN, "c1", "c1:1", desde_fase="c1:0")
    return servicios, repos[2]


def _equipos_de_la_primera(servicios):
    primera = servicios.cuadro.actual("c1", "c1:1").rondas[0]
    return [p for c in primera for p in (c.local, c.visitante)]


class TestEliminar:
    def test_borra_el_cuadro(self, mundo):
        servicios, repo = mundo
        servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")
        assert repo.de_fase("c1:1") == ()

    def test_despues_ya_no_hay_cuadro(self, mundo):
        servicios, _ = mundo
        servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")
        with pytest.raises(NoEncontrado, match="todavía no tiene cuadro"):
            servicios.cuadro.actual("c1", "c1:1")

    def test_se_puede_generar_otro(self, mundo):
        servicios, _ = mundo
        servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")
        assert servicios.cuadro.generar(ADMIN, "c1", "c1:1", desde_fase="c1:0")

    def test_no_toca_el_calendario_de_la_liga(self, mundo):
        servicios, repo = mundo
        antes = len(repo.de_fase("c1:0"))
        servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")
        assert len(repo.de_fase("c1:0")) == antes

    def test_borra_tambien_los_resultados(self, mundo):
        servicios, repo = mundo
        servicios.cuadro.registrar(ADMIN, "c1", "c1:1", 0, 0, Marcador(2, 1))
        servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")
        assert repo.de_fase("c1:1") == ()

    def test_sin_cuadro_falla_claro(self, mundo):
        servicios, _ = mundo
        servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")
        with pytest.raises(NoEncontrado):
            servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")

    def test_rechaza_una_fase_que_no_es_eliminatoria(self, mundo):
        servicios, _ = mundo
        with pytest.raises(Exception, match="no es una eliminatoria"):
            servicios.cuadro.eliminar(ADMIN, "c1", "c1:0")


class TestBorrarResultado:
    def test_quita_el_resultado(self, mundo):
        servicios, _ = mundo
        servicios.cuadro.registrar(ADMIN, "c1", "c1:1", 0, 0, Marcador(2, 1))
        servicios.cuadro.borrar_resultado(ADMIN, "c1", "c1:1", 0, 0)
        assert servicios.cuadro.actual("c1", "c1:1").slot(0, 0).marcador is None

    def test_queda_guardado_y_el_ganador_sale_de_la_final(self, mundo):
        servicios, _ = mundo
        servicios.cuadro.registrar(ADMIN, "c1", "c1:1", 0, 0, Marcador(2, 1))
        assert servicios.cuadro.actual("c1", "c1:1").slot(1, 0).local is not None
        servicios.cuadro.borrar_resultado(ADMIN, "c1", "c1:1", 0, 0)
        assert servicios.cuadro.actual("c1", "c1:1").slot(1, 0).local is None

    def test_el_partido_vuelve_a_pendiente_en_el_repositorio(self, mundo):
        servicios, repo = mundo
        servicios.cuadro.registrar(ADMIN, "c1", "c1:1", 0, 0, Marcador(2, 1))
        servicios.cuadro.borrar_resultado(ADMIN, "c1", "c1:1", 0, 0)
        assert not repo.obtener("c1:1:r0:0").esta_finalizado

    def test_una_casilla_sin_resultado_se_rechaza(self, mundo):
        servicios, _ = mundo
        with pytest.raises(ErrorDeDominio, match="no tiene resultado"):
            servicios.cuadro.borrar_resultado(ADMIN, "c1", "c1:1", 0, 0)

    def test_sin_cuadro_falla_claro(self, mundo):
        servicios, _ = mundo
        servicios.cuadro.eliminar(ADMIN, "c1", "c1:1")
        with pytest.raises(NoEncontrado):
            servicios.cuadro.borrar_resultado(ADMIN, "c1", "c1:1", 0, 0)


class TestIntercambiar:
    def test_cambia_a_los_dos_de_sitio(self, mundo):
        servicios, _ = mundo
        antes = _equipos_de_la_primera(servicios)
        servicios.cuadro.intercambiar(ADMIN, "c1", "c1:1", antes[0], antes[1])
        despues = _equipos_de_la_primera(servicios)
        assert (despues[0], despues[1]) == (antes[1], antes[0])
        assert despues[2:] == antes[2:]

    def test_queda_guardado(self, mundo):
        servicios, _ = mundo
        antes = _equipos_de_la_primera(servicios)
        servicios.cuadro.intercambiar(ADMIN, "c1", "c1:1", antes[0], antes[3])
        assert _equipos_de_la_primera(servicios)[0] == antes[3]

    def test_con_resultados_se_rechaza_y_no_cambia_nada(self, mundo):
        servicios, _ = mundo
        servicios.cuadro.registrar(ADMIN, "c1", "c1:1", 0, 0, Marcador(2, 1))
        antes = _equipos_de_la_primera(servicios)
        with pytest.raises(ErrorDeDominio, match="bórralos"):
            servicios.cuadro.intercambiar(ADMIN, "c1", "c1:1", antes[0], antes[3])
        assert _equipos_de_la_primera(servicios) == antes

    def test_un_ajeno_se_rechaza(self, mundo):
        servicios, _ = mundo
        with pytest.raises(ErrorDeDominio, match="no está"):
            servicios.cuadro.intercambiar(ADMIN, "c1", "c1:1", "p1", "fantasma")


class TestSoloElAdmin:
    @pytest.mark.parametrize("quien", [PROFE, CURIOSO, ANONIMO], ids=["registrador", "visitante", "anonimo"])
    def test_no_pueden_borrar_el_cuadro(self, mundo, quien):
        servicios, repo = mundo
        with pytest.raises(PermisoDenegado):
            servicios.cuadro.eliminar(quien, "c1", "c1:1")
        assert repo.de_fase("c1:1")

    @pytest.mark.parametrize("quien", [PROFE, CURIOSO], ids=["registrador", "visitante"])
    def test_ni_borrar_un_resultado(self, mundo, quien):
        servicios, _ = mundo
        servicios.cuadro.registrar(ADMIN, "c1", "c1:1", 0, 0, Marcador(2, 1))
        with pytest.raises(PermisoDenegado):
            servicios.cuadro.borrar_resultado(quien, "c1", "c1:1", 0, 0)
        assert servicios.cuadro.actual("c1", "c1:1").slot(0, 0).marcador is not None

    @pytest.mark.parametrize("quien", [PROFE, CURIOSO], ids=["registrador", "visitante"])
    def test_ni_intercambiar(self, mundo, quien):
        servicios, _ = mundo
        antes = _equipos_de_la_primera(servicios)
        with pytest.raises(PermisoDenegado):
            servicios.cuadro.intercambiar(quien, "c1", "c1:1", antes[0], antes[1])
        assert _equipos_de_la_primera(servicios) == antes

    def test_el_registrador_sigue_cargando_resultados(self, mundo):
        servicios, _ = mundo
        assert servicios.cuadro.registrar(PROFE, "c1", "c1:1", 0, 0, Marcador(1, 0))
