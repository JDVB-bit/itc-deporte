from __future__ import annotations

import pytest

from itc_deporte.domain.competicion import ReglasDeCompeticion
from itc_deporte.domain.enfrentamiento import Enfrentamiento, Marcador
from itc_deporte.domain.errores import ReglaInvalida
from itc_deporte.domain.motor.clasificacion import calcular_clasificacion
from itc_deporte.domain.reglas.desempate import PorEnfrentamientoDirecto, PorPuntos
from itc_deporte.domain.reglas.puntuacion import PorSets, VictoriaDerrota

CONTADOR = iter(range(1000))


def jugado(local, visitante, gl, gv) -> Enfrentamiento:
    return Enfrentamiento(f"e{next(CONTADOR)}", local, visitante).finalizar(
        Marcador(gl, gv)
    )


def pendiente(local, visitante) -> Enfrentamiento:
    return Enfrentamiento(f"e{next(CONTADOR)}", local, visitante)


def por_id(filas):
    return {f.participante_id: f for f in filas}


class TestTablaBasica:
    def test_una_victoria_da_tres_puntos(self):
        tabla = por_id(calcular_clasificacion(["a", "b"], [jugado("a", "b", 2, 1)]))
        assert (tabla["a"].puntos, tabla["a"].ganados) == (3, 1)
        assert (tabla["b"].puntos, tabla["b"].perdidos) == (0, 1)

    def test_un_empate_da_un_punto_a_cada_uno(self):
        tabla = por_id(calcular_clasificacion(["a", "b"], [jugado("a", "b", 1, 1)]))
        assert all(f.puntos == 1 and f.empatados == 1 for f in tabla.values())

    def test_acumula_a_favor_y_en_contra(self):
        tabla = por_id(
            calcular_clasificacion(
                ["a", "b", "c"],
                [jugado("a", "b", 3, 1), jugado("a", "c", 0, 2)],
            )
        )
        assert (tabla["a"].a_favor, tabla["a"].en_contra) == (3, 3)
        assert tabla["a"].diferencia == 0
        assert tabla["a"].jugados == 2

    def test_los_participantes_sin_partidos_aparecen_en_cero(self):
        tabla = calcular_clasificacion(["a", "b", "c"], [])
        assert len(tabla) == 3
        assert all(f.jugados == 0 and f.puntos == 0 for f in tabla)

    def test_una_competicion_sin_participantes_da_tabla_vacia(self):
        assert calcular_clasificacion([], []) == ()

    def test_los_partidos_pendientes_no_cuentan(self):
        tabla = por_id(calcular_clasificacion(["a", "b"], [pendiente("a", "b")]))
        assert all(f.jugados == 0 for f in tabla.values())

    @pytest.mark.parametrize(
        "ajeno", [("a", "z", 9, 0), ("z", "a", 0, 9)], ids=["visitante", "local"]
    )
    def test_ignora_partidos_de_ajenos_a_la_tabla(self, ajeno):
        """Permite calcular la tabla de un grupo sin los partidos de los demás.

        Da igual de qué lado esté el ajeno.
        """
        tabla = por_id(
            calcular_clasificacion(
                ["a", "b"], [jugado("a", "b", 1, 0), jugado(*ajeno)]
            )
        )
        assert tabla["a"].jugados == 1
        assert "z" not in tabla

    def test_un_participante_repetido_aparece_una_vez(self):
        assert len(calcular_clasificacion(["a", "a", "b"], [])) == 2


class TestOrden:
    def test_ordena_por_puntos(self):
        tabla = calcular_clasificacion(
            ["a", "b", "c"],
            [jugado("a", "b", 1, 0), jugado("b", "c", 0, 1), jugado("a", "c", 1, 0)],
        )
        assert [f.participante_id for f in tabla] == ["a", "c", "b"]

    def test_desempata_por_diferencia(self):
        tabla = calcular_clasificacion(
            ["a", "b", "c", "d"],
            [jugado("a", "b", 5, 0), jugado("c", "d", 1, 0)],
        )
        assert [f.participante_id for f in tabla[:2]] == ["a", "c"]

    def test_usa_el_desempate_configurado(self):
        """`b` gana el mano a mano pese a tener peor diferencia."""
        reglas = ReglasDeCompeticion(
            desempate=(PorPuntos(), PorEnfrentamientoDirecto(VictoriaDerrota()))
        )
        partidos = [
            jugado("b", "a", 1, 0),
            jugado("a", "c", 9, 0),
            jugado("b", "c", 1, 0),
        ]
        tabla = calcular_clasificacion(["a", "b", "c"], partidos, reglas)
        assert [f.participante_id for f in tabla][:2] == ["b", "a"]

    def test_un_empate_irresoluble_conserva_el_orden_de_entrada(self):
        tabla = calcular_clasificacion(["b", "a"], [])
        assert [f.participante_id for f in tabla] == ["b", "a"]


class TestVoleibol:
    """La tabla que el sistema anterior no podía producir."""

    @pytest.fixture
    def reglas(self):
        return ReglasDeCompeticion(puntuacion=PorSets())

    def test_un_3_2_reparte_2_1(self, reglas):
        tabla = por_id(
            calcular_clasificacion(["a", "b"], [jugado("a", "b", 3, 2)], reglas)
        )
        assert (tabla["a"].puntos, tabla["b"].puntos) == (2, 1)

    def test_el_perdedor_de_un_3_2_suma(self, reglas):
        """Bajo la regla anterior habría sumado cero."""
        tabla = por_id(
            calcular_clasificacion(["a", "b"], [jugado("a", "b", 3, 2)], reglas)
        )
        assert tabla["b"].puntos == 1 and tabla["b"].perdidos == 1

    def test_los_sets_se_acumulan_como_a_favor_y_en_contra(self, reglas):
        tabla = por_id(
            calcular_clasificacion(["a", "b"], [jugado("a", "b", 3, 1)], reglas)
        )
        assert (tabla["a"].a_favor, tabla["a"].en_contra) == (3, 1)

    def test_un_marcador_empatado_delata_el_dato_corrupto(self, reglas):
        """Bajo la regla vieja esto era un empate legítimo y pasaba inadvertido."""
        with pytest.raises(ReglaInvalida):
            calcular_clasificacion(["a", "b"], [jugado("a", "b", 2, 2)], reglas)


class TestCoherencia:
    def test_los_jugados_cuadran_con_los_resultados(self):
        partidos = [
            jugado("a", "b", 1, 0),
            jugado("b", "c", 2, 2),
            jugado("c", "a", 0, 3),
        ]
        for fila in calcular_clasificacion(["a", "b", "c"], partidos):
            assert fila.jugados == fila.ganados + fila.empatados + fila.perdidos

    def test_los_goles_a_favor_totales_igualan_a_los_en_contra(self):
        partidos = [jugado("a", "b", 3, 1), jugado("b", "c", 2, 2)]
        tabla = calcular_clasificacion(["a", "b", "c"], partidos)
        assert sum(f.a_favor for f in tabla) == sum(f.en_contra for f in tabla)

    def test_es_determinista(self):
        partidos = [jugado("a", "b", 1, 0), jugado("c", "d", 1, 0)]
        una = calcular_clasificacion(["a", "b", "c", "d"], partidos)
        otra = calcular_clasificacion(["a", "b", "c", "d"], partidos)
        assert [f.participante_id for f in una] == [f.participante_id for f in otra]

    def test_no_muta_los_enfrentamientos(self):
        partido = jugado("a", "b", 1, 0)
        calcular_clasificacion(["a", "b"], [partido])
        assert partido.marcador == Marcador(1, 0)
