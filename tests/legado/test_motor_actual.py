"""Tests de caracterización: fijan lo que el sistema hace HOY.

No juzgan si el comportamiento es correcto. Varios de estos tests documentan
rarezas que el plan marca para cambiar (§12); cuando el motor nuevo las corrija,
el test que quede obsoleto se borra en el mismo commit que introduce el cambio,
y así el cambio de comportamiento queda visible en el diff en lugar de colarse.
"""

from __future__ import annotations

import pytest

from itc_deporte.legado.motor_actual import (
    CURSOS_VALIDOS,
    calcular_tabla_desde,
    enf_limpio,
    gen_seeds,
    generar_cursos,
    generar_round_robin,
    parsear_enf,
    parsear_lado,
    tamano_bracket,
)


def partido(enf, estado="Finalizado", g1=0, g2=0, pid=1, fecha="2026-07-25 15:00"):
    return [pid, fecha, enf, estado, g1, g2]


class TestGenerarCursos:
    def test_rellena_con_cero_a_la_izquierda(self):
        assert generar_cursos(6, 3) == ["601", "602", "603"]

    def test_cantidad_cero_da_lista_vacia(self):
        assert generar_cursos(6, 0) == []

    def test_los_cursos_validos_son_38(self):
        assert len(CURSOS_VALIDOS) == 38


class TestParseoDeLado:
    def test_extrae_nombre_y_curso(self):
        assert parsear_lado("Los Tigres (601)") == ("Los Tigres", "601")

    def test_usa_el_ultimo_parentesis(self):
        assert parsear_lado("Real (Madrid) (601)") == ("Real (Madrid)", "601")

    def test_sin_parentesis_el_curso_es_interrogante(self):
        assert parsear_lado("Los Tigres") == ("Los Tigres", "?")

    def test_reconoce_una_tupla_serializada(self):
        """Rastro de haber guardado tuplas de Python en la base."""
        assert parsear_lado("('Los Tigres', '601')") == ("Los Tigres", "601")

    def test_reconoce_una_tupla_serializada_con_marca_de_duda(self):
        assert parsear_lado("('Los Tigres', '601') (?)") == ("Los Tigres", "601")

    def test_un_parentesis_vacio_da_curso_vacio(self):
        assert parsear_lado("Los Tigres ()") == ("Los Tigres", "")


class TestParseoDeEnfrentamiento:
    def test_separa_los_dos_lados(self):
        assert parsear_enf("A (601) vs B (602)") == ("A", "601", "B", "602")

    def test_sin_separador_devuelve_none(self):
        assert parsear_enf("A (601) contra B (602)") is None

    def test_un_no_string_devuelve_none(self):
        assert parsear_enf(None) is None
        assert parsear_enf(42) is None

    def test_un_nombre_que_contiene_vs_rompe_el_parseo(self):
        """Rareza vigente: parte por el primer ' vs ', no por el separador real.

        Es la consecuencia directa de identificar equipos por texto.
        """
        assert parsear_enf("Nos vs Ellos (601) vs B (602)") == (
            "Nos",
            "?",
            "Ellos (601) vs B",
            "602",
        )

    def test_enf_limpio_normaliza_el_formato(self):
        assert enf_limpio("('A', '601') vs ('B', '602')") == "A (601) vs B (602)"

    def test_enf_limpio_devuelve_el_original_si_no_puede_parsear(self):
        assert enf_limpio("texto suelto") == "texto suelto"


class TestRoundRobin:
    def test_siempre_devuelve_siete_jornadas(self):
        """Rareza vigente: repite o trunca hasta 7 (§12 del plan)."""
        for n in (2, 3, 4, 8):
            assert len(generar_round_robin([f"e{i}" for i in range(n)])) == 7

    def test_sin_equipos_revienta(self):
        """Rareza vigente: con la lista vacía lanza IndexError, no devuelve [].

        En producción no salta porque `realizar_sorteo` corta antes si hay menos
        de 2 equipos, pero la función no se defiende por su cuenta.
        """
        with pytest.raises(IndexError):
            generar_round_robin([])

    def test_un_solo_equipo_produce_siete_jornadas_contra_bye(self):
        jornadas = generar_round_robin(["e1"])
        assert len(jornadas) == 7
        assert all(jornada == [("e1", "BYE")] for jornada in jornadas)

    def test_con_numero_impar_aparece_bye(self):
        jornadas = generar_round_robin(["a", "b", "c"])
        assert any("BYE" in cruce for jornada in jornadas for cruce in jornada)

    def test_cada_jornada_empareja_a_todos_una_vez(self):
        jornadas = generar_round_robin(["a", "b", "c", "d"])
        for jornada in jornadas:
            participantes = [e for cruce in jornada for e in cruce]
            assert sorted(participantes) == ["a", "b", "c", "d"]

    def test_las_primeras_n_menos_1_jornadas_no_repiten_cruces(self):
        equipos = ["a", "b", "c", "d"]
        cruces = [
            frozenset(cruce) for jornada in generar_round_robin(equipos)[:3] for cruce in jornada
        ]
        assert len(cruces) == len(set(cruces)) == 6

    def test_la_jornada_8_seria_la_1_otra_vez(self):
        """Con 4 equipos hay 3 rondas naturales: la 4ª repite la 1ª."""
        jornadas = generar_round_robin(["a", "b", "c", "d"])
        assert jornadas[3] == jornadas[0]

    def test_alterna_localia_en_las_rondas_impares(self):
        """El método del círculo invierte el orden en las rondas impares.

        Con solo 2 equipos no se aprecia: hay una única ronda natural que se
        repite 7 veces, siempre con el mismo local.
        """
        jornadas = generar_round_robin(["a", "b", "c", "d"])
        assert jornadas[0] == [("a", "d"), ("b", "c")]
        assert jornadas[1] == [("c", "a"), ("b", "d")]

    def test_con_dos_equipos_el_local_nunca_cambia(self):
        assert generar_round_robin(["a", "b"]) == [[("a", "b")]] * 7


class TestTamanoBracket:
    @pytest.mark.parametrize(
        "n,esperado",
        [(1, 2), (2, 2), (3, 4), (4, 4), (5, 8), (8, 8), (9, 16), (16, 16)],
    )
    def test_redondea_a_la_potencia_de_dos_siguiente(self, n, esperado):
        assert tamano_bracket(n) == esperado

    def test_por_encima_de_16_se_recorta_a_16(self):
        """Rareza vigente: el cuadro no crece más allá de octavos (§12)."""
        assert tamano_bracket(32) == 16
        assert tamano_bracket(100) == 16


class TestGenSeeds:
    def test_bracket_de_dos(self):
        assert gen_seeds(2) == [1, 2]

    def test_bracket_de_cuatro(self):
        assert gen_seeds(4) == [1, 4, 2, 3]

    def test_bracket_de_ocho(self):
        assert gen_seeds(8) == [1, 8, 4, 5, 2, 7, 3, 6]

    def test_el_primero_se_cruza_con_el_ultimo(self):
        seeds = gen_seeds(16)
        assert (seeds[0], seeds[1]) == (1, 16)

    def test_cada_cruce_suma_size_mas_uno(self):
        """Propiedad de la siembra estándar."""
        size = 16
        seeds = gen_seeds(size)
        for i in range(0, size, 2):
            assert seeds[i] + seeds[i + 1] == size + 1

    def test_contiene_todas_las_posiciones_sin_repetir(self):
        assert sorted(gen_seeds(16)) == list(range(1, 17))


class TestCalcularTabla:
    def test_una_victoria_da_tres_puntos(self):
        tabla = calcular_tabla_desde([partido("A (601) vs B (602)", g1=2, g2=1)], {})
        por_equipo = {f["Equipo"]: f for f in tabla}
        assert por_equipo["A"]["Pts"] == 3
        assert por_equipo["A"]["PG"] == 1
        assert por_equipo["B"]["Pts"] == 0
        assert por_equipo["B"]["PP"] == 1

    def test_un_empate_da_un_punto_a_cada_uno(self):
        tabla = calcular_tabla_desde([partido("A (601) vs B (602)", g1=1, g2=1)], {})
        assert all(f["Pts"] == 1 and f["PE"] == 1 for f in tabla)

    def test_los_partidos_pendientes_no_cuentan(self):
        tabla = calcular_tabla_desde(
            [partido("A (601) vs B (602)", estado="Pendiente", g1=5, g2=0)], {}
        )
        assert tabla == []

    def test_acumula_goles_a_favor_y_en_contra(self):
        tabla = calcular_tabla_desde(
            [
                partido("A (601) vs B (602)", g1=3, g2=1, pid=1),
                partido("A (601) vs C (603)", g1=0, g2=2, pid=2),
            ],
            {},
        )
        fila_a = next(f for f in tabla if f["Equipo"] == "A")
        assert (fila_a["GF"], fila_a["GC"], fila_a["DG"], fila_a["PJ"]) == (3, 3, 0, 2)

    def test_los_equipos_sin_partidos_aparecen_en_cero(self):
        tabla = calcular_tabla_desde([], {"601": ["A"], "602": ["B"]})
        assert len(tabla) == 2
        assert all(f["Pts"] == 0 and f["PJ"] == 0 for f in tabla)

    def test_ordena_por_puntos_luego_diferencia_luego_goles_a_favor(self):
        tabla = calcular_tabla_desde(
            [
                # A: 3 pts, DG +3    B: 0 pts
                partido("A (601) vs B (602)", g1=3, g2=0, pid=1),
                # C: 3 pts, DG +1    D: 0 pts
                partido("C (603) vs D (604)", g1=1, g2=0, pid=2),
            ],
            {},
        )
        assert [f["Equipo"] for f in tabla[:2]] == ["A", "C"]
        assert [f["#"] for f in tabla] == [1, 2, 3, 4]

    def test_un_curso_invalido_descarta_el_partido(self):
        tabla = calcular_tabla_desde([partido("A (999) vs B (602)", g1=2, g2=1)], {})
        assert tabla == []

    def test_un_enfrentamiento_no_parseable_se_ignora(self):
        tabla = calcular_tabla_desde([partido("texto suelto", g1=2, g2=1)], {})
        assert tabla == []

    def test_dos_equipos_homonimos_en_cursos_distintos_no_se_mezclan(self):
        tabla = calcular_tabla_desde([partido("A (601) vs A (602)", g1=2, g2=1)], {})
        assert len(tabla) == 2
        assert {f["Curso"] for f in tabla} == {"601", "602"}

    def test_el_voleibol_admite_empates(self):
        """Rareza vigente: se puntúa por goles, así que un 2-2 en sets empata.

        Es el problema 6 del diagnóstico, y lo que arregla `Marcador.por_sets`.
        """
        tabla = calcular_tabla_desde([partido("A (601) vs B (602)", g1=2, g2=2)], {})
        assert all(f["PE"] == 1 for f in tabla)
