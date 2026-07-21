from __future__ import annotations

import pytest

from itc_deporte.domain.clasificacion import FilaClasificacion
from itc_deporte.domain.enfrentamiento import Enfrentamiento, Marcador
from itc_deporte.domain.reglas.desempate import (
    DESEMPATE_CLASICO,
    ContextoDeDesempate,
    CriterioDeDesempate,
    PorAFavor,
    PorDiferencia,
    PorEnContra,
    PorEnfrentamientoDirecto,
    PorPartidosGanados,
    PorPuntos,
    ordenar_clasificacion,
)
from itc_deporte.domain.reglas.puntuacion import VictoriaDerrota


def fila(pid, **cambios) -> FilaClasificacion:
    base = dict(jugados=0, ganados=0, empatados=0, perdidos=0)
    return FilaClasificacion(pid, **{**base, **cambios})


def ganado(pid, puntos=3, a_favor=0, en_contra=0) -> FilaClasificacion:
    return FilaClasificacion(
        pid, jugados=1, ganados=1, a_favor=a_favor, en_contra=en_contra, puntos=puntos
    )


def cerrado(id_, local, visitante, gl, gv) -> Enfrentamiento:
    return Enfrentamiento(id_, local, visitante).finalizar(Marcador(gl, gv))


SIN_CONTEXTO = ContextoDeDesempate(empatados=())


class TestCriteriosSimples:
    def test_por_puntos(self):
        assert PorPuntos().valor(fila("p1", puntos=7), SIN_CONTEXTO) == 7

    def test_por_diferencia(self):
        f = fila("p1", jugados=1, ganados=1, a_favor=5, en_contra=2)
        assert PorDiferencia().valor(f, SIN_CONTEXTO) == 3

    def test_por_a_favor(self):
        f = fila("p1", jugados=1, ganados=1, a_favor=5)
        assert PorAFavor().valor(f, SIN_CONTEXTO) == 5

    def test_por_en_contra_invierte_el_signo(self):
        """Encajar menos debe ordenar más arriba."""
        menos = PorEnContra().valor(fila("p1", jugados=1, perdidos=1, en_contra=1), SIN_CONTEXTO)
        mas = PorEnContra().valor(fila("p2", jugados=1, perdidos=1, en_contra=9), SIN_CONTEXTO)
        assert menos > mas

    def test_por_partidos_ganados(self):
        f = fila("p1", jugados=3, ganados=2, perdidos=1)
        assert PorPartidosGanados().valor(f, SIN_CONTEXTO) == 2

    @pytest.mark.parametrize(
        "criterio",
        [PorPuntos(), PorDiferencia(), PorAFavor(), PorEnContra(), PorPartidosGanados()],
    )
    def test_satisfacen_el_protocolo(self, criterio):
        assert isinstance(criterio, CriterioDeDesempate)


class TestOrdenacion:
    def test_ordena_por_puntos_descendente(self):
        filas = [ganado("p1", puntos=1), ganado("p2", puntos=7), ganado("p3", puntos=4)]
        orden = ordenar_clasificacion(filas, [PorPuntos()])
        assert [f.participante_id for f in orden] == ["p2", "p3", "p1"]

    def test_el_segundo_criterio_desempata_dentro_del_bloque(self):
        filas = [
            ganado("p1", puntos=3, a_favor=1, en_contra=0),  # DG +1
            ganado("p2", puntos=3, a_favor=5, en_contra=0),  # DG +5
            ganado("p3", puntos=9, a_favor=0, en_contra=0),
        ]
        orden = ordenar_clasificacion(filas, [PorPuntos(), PorDiferencia()])
        assert [f.participante_id for f in orden] == ["p3", "p2", "p1"]

    def test_el_orden_clasico_reproduce_el_del_sistema_anterior(self):
        """Puntos, luego diferencia, luego a favor."""
        filas = [
            ganado("a", puntos=3, a_favor=3, en_contra=0),  # DG +3
            ganado("b", puntos=3, a_favor=1, en_contra=0),  # DG +1
            ganado("c", puntos=3, a_favor=5, en_contra=2),  # DG +3, más a favor
        ]
        orden = ordenar_clasificacion(filas, DESEMPATE_CLASICO)
        assert [f.participante_id for f in orden] == ["c", "a", "b"]

    def test_un_empate_irresoluble_conserva_el_orden_de_entrada(self):
        """Determinismo: la misma tabla produce siempre la misma clasificación."""
        filas = [ganado("p1"), ganado("p2"), ganado("p3")]
        orden = ordenar_clasificacion(filas, DESEMPATE_CLASICO)
        assert [f.participante_id for f in orden] == ["p1", "p2", "p3"]

    def test_sin_criterios_conserva_el_orden_de_entrada(self):
        filas = [ganado("p2", puntos=0), ganado("p1", puntos=99)]
        orden = ordenar_clasificacion(filas, [])
        assert [f.participante_id for f in orden] == ["p2", "p1"]

    def test_una_tabla_vacia_no_rompe(self):
        assert ordenar_clasificacion([], DESEMPATE_CLASICO) == ()

    def test_una_tabla_de_uno_no_rompe(self):
        assert len(ordenar_clasificacion([fila("p1")], DESEMPATE_CLASICO)) == 1

    def test_una_competicion_sin_partidos_jugados_no_rompe(self):
        filas = [fila("p1"), fila("p2"), fila("p3")]
        orden = ordenar_clasificacion(filas, DESEMPATE_CLASICO)
        assert len(orden) == 3


class TestEnfrentamientoDirecto:
    """El criterio que no puede decidirse mirando una fila aislada."""

    def test_gana_quien_venció_al_otro(self):
        filas = [ganado("a", puntos=3), ganado("b", puntos=3)]
        partidos = [cerrado("e1", "b", "a", 2, 0)]
        orden = ordenar_clasificacion(
            filas,
            [PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota())],
            partidos,
        )
        assert [f.participante_id for f in orden] == ["b", "a"]

    def test_solo_cuenta_los_partidos_entre_los_empatados(self):
        """La goleada a un tercero no debe influir en el mano a mano."""
        filas = [ganado("a", puntos=3), ganado("b", puntos=3)]
        partidos = [
            cerrado("e1", "b", "a", 1, 0),  # b le ganó a a
            cerrado("e2", "a", "c", 9, 0),  # irrelevante: c no está empatado
        ]
        orden = ordenar_clasificacion(
            filas,
            [PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota())],
            partidos,
        )
        assert [f.participante_id for f in orden] == ["b", "a"]

    def test_solo_ve_a_los_que_siguen_empatados_a_esa_altura(self):
        """`c` tiene más puntos y queda fuera del bloque antes de llegar al
        criterio, así que su victoria sobre `b` no cuenta."""
        filas = [ganado("a", puntos=3), ganado("b", puntos=3), ganado("c", puntos=9)]
        partidos = [
            cerrado("e1", "b", "a", 1, 0),  # b > a entre los empatados
            cerrado("e2", "c", "b", 5, 0),  # c ya está por encima
        ]
        orden = ordenar_clasificacion(
            filas,
            [PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota())],
            partidos,
        )
        assert [f.participante_id for f in orden] == ["c", "b", "a"]

    def test_los_partidos_pendientes_no_cuentan(self):
        filas = [ganado("a", puntos=3), ganado("b", puntos=3)]
        pendiente = Enfrentamiento("e1", "b", "a", marcador=Marcador(5, 0))
        orden = ordenar_clasificacion(
            filas,
            [PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota())],
            [pendiente],
        )
        assert [f.participante_id for f in orden] == ["a", "b"]

    def test_sin_partidos_entre_ellos_no_desempata(self):
        filas = [ganado("a", puntos=3), ganado("b", puntos=3)]
        orden = ordenar_clasificacion(
            filas, [PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota())], []
        )
        assert [f.participante_id for f in orden] == ["a", "b"]

    def test_un_mano_a_mano_empatado_no_desempata(self):
        filas = [ganado("a", puntos=3), ganado("b", puntos=3)]
        partidos = [cerrado("e1", "a", "b", 1, 1)]
        orden = ordenar_clasificacion(
            filas,
            [PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota())],
            partidos,
        )
        assert [f.participante_id for f in orden] == ["a", "b"]

    def test_triple_empate_se_resuelve_por_la_liguilla_entre_los_tres(self):
        filas = [ganado("a", puntos=3), ganado("b", puntos=3), ganado("c", puntos=3)]
        partidos = [
            cerrado("e1", "a", "b", 1, 0),  # a: 3
            cerrado("e2", "b", "c", 1, 0),  # b: 3
            cerrado("e3", "c", "a", 1, 0),  # c: 3  -> ciclo, nadie destaca
            cerrado("e4", "a", "c", 2, 0),  # a suma otra victoria: a=6
        ]
        orden = ordenar_clasificacion(
            filas,
            [PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota())],
            partidos,
        )
        assert orden[0].participante_id == "a"

    def test_satisface_el_protocolo(self):
        assert isinstance(
            PorEnfrentamientoDirecto(VictoriaDerrota()), CriterioDeDesempate
        )


class TestCriteriosComponibles:
    def test_se_puede_configurar_otro_orden_de_criterios(self):
        """OCP: cambiar la política de desempate es reordenar una lista."""
        filas = [
            ganado("a", puntos=3, a_favor=1, en_contra=0),
            ganado("b", puntos=3, a_favor=9, en_contra=8),
        ]
        por_diferencia = ordenar_clasificacion(filas, [PorPuntos(), PorDiferencia()])
        por_a_favor = ordenar_clasificacion(filas, [PorPuntos(), PorAFavor()])
        assert [f.participante_id for f in por_diferencia] == ["a", "b"]
        assert [f.participante_id for f in por_a_favor] == ["b", "a"]

    def test_admite_un_criterio_ajeno_al_modulo(self):
        class PorNombre:
            def valor(self, fila, contexto):
                return -ord(fila.participante_id[0])

        filas = [ganado("c"), ganado("a"), ganado("b")]
        orden = ordenar_clasificacion(filas, [PorPuntos(), PorNombre()])
        assert [f.participante_id for f in orden] == ["a", "b", "c"]
