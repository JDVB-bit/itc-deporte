from __future__ import annotations

import pytest

from itc_deporte.domain.errores import ReglaInvalida
from itc_deporte.domain.reglas.fixture import (
    ConfigFixture,
    Cruce,
    EliminacionDirecta,
    GeneradorDeFixture,
    Jornada,
    RoundRobin,
    orden_de_siembra,
    tamano_de_cuadro,
)


def equipos(n: int) -> list[str]:
    return [f"p{i}" for i in range(1, n + 1)]


def cruces_de(jornadas) -> set[frozenset[str]]:
    return {frozenset((c.local, c.visitante)) for j in jornadas for c in j.cruces}


class TestCruce:
    def test_rechaza_un_participante_contra_si_mismo(self):
        with pytest.raises(ReglaInvalida):
            Cruce("p1", "p1")

    def test_invertido_intercambia_la_localia(self):
        assert Cruce("a", "b").invertido() == Cruce("b", "a")


class TestJornada:
    def test_rechaza_numero_cero(self):
        with pytest.raises(ReglaInvalida):
            Jornada(0)

    def test_participantes_incluye_a_los_que_descansan(self):
        jornada = Jornada(1, (Cruce("a", "b"),), ("c",))
        assert set(jornada.participantes) == {"a", "b", "c"}


class TestConfigFixture:
    def test_rechaza_cero_vueltas(self):
        with pytest.raises(ReglaInvalida):
            ConfigFixture(vueltas=0)

    def test_rechaza_forzar_cero_jornadas(self):
        with pytest.raises(ReglaInvalida):
            ConfigFixture(jornadas_forzadas=0)

    def test_por_defecto_una_vuelta_sin_forzar(self):
        config = ConfigFixture()
        assert config.vueltas == 1 and config.jornadas_forzadas is None


class TestRoundRobin:
    def test_produce_n_menos_1_jornadas(self):
        """Cambio de comportamiento: antes eran siempre 7 (§12 del plan)."""
        assert len(RoundRobin().generar(equipos(4), ConfigFixture())) == 3
        assert len(RoundRobin().generar(equipos(8), ConfigFixture())) == 7
        assert len(RoundRobin().generar(equipos(10), ConfigFixture())) == 9

    def test_todos_se_enfrentan_una_vez(self):
        jornadas = RoundRobin().generar(equipos(6), ConfigFixture())
        assert len(cruces_de(jornadas)) == 15  # C(6,2)

    def test_nadie_juega_dos_veces_en_la_misma_jornada(self):
        for jornada in RoundRobin().generar(equipos(8), ConfigFixture()):
            participantes = list(jornada.participantes)
            assert len(participantes) == len(set(participantes))

    def test_cada_jornada_involucra_a_todos(self):
        for jornada in RoundRobin().generar(equipos(6), ConfigFixture()):
            assert set(jornada.participantes) == set(equipos(6))

    def test_las_jornadas_se_numeran_desde_uno(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture())
        assert [j.numero for j in jornadas] == [1, 2, 3]

    def test_alterna_la_localia_entre_jornadas(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture())
        assert jornadas[0].cruces[0] == Cruce("p1", "p4")
        assert jornadas[1].cruces[0] == Cruce("p3", "p1")


class TestRoundRobinConImpares:
    def test_en_cada_jornada_descansa_uno(self):
        """Antes el BYE era una cadena colada entre los equipos."""
        jornadas = RoundRobin().generar(equipos(5), ConfigFixture())
        assert all(len(j.descansan) == 1 for j in jornadas)

    def test_descansan_todos_por_turno(self):
        jornadas = RoundRobin().generar(equipos(5), ConfigFixture())
        descansaron = [j.descansan[0] for j in jornadas]
        assert sorted(descansaron) == sorted(equipos(5))

    def test_con_par_no_descansa_nadie(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture())
        assert all(j.descansan == () for j in jornadas)

    def test_ningun_cruce_menciona_el_hueco(self):
        jornadas = RoundRobin().generar(equipos(5), ConfigFixture())
        nombres = {p for j in jornadas for c in j.cruces for p in (c.local, c.visitante)}
        assert None not in nombres and "BYE" not in nombres


class TestRoundRobinCasosBorde:
    def test_lista_vacia_devuelve_vacio(self):
        """Cambio de comportamiento: el generador anterior lanzaba IndexError."""
        assert RoundRobin().generar([], ConfigFixture()) == ()

    def test_un_solo_participante_devuelve_vacio(self):
        assert RoundRobin().generar(["p1"], ConfigFixture()) == ()

    def test_dos_participantes_dan_una_jornada(self):
        jornadas = RoundRobin().generar(equipos(2), ConfigFixture())
        assert len(jornadas) == 1
        assert jornadas[0].cruces == (Cruce("p1", "p2"),)

    def test_rechaza_participantes_repetidos(self):
        with pytest.raises(ReglaInvalida):
            RoundRobin().generar(["p1", "p2", "p1"], ConfigFixture())


class TestRoundRobinIdaYVuelta:
    def test_duplica_las_jornadas(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture(vueltas=2))
        assert len(jornadas) == 6

    def test_la_vuelta_invierte_la_localia(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture(vueltas=2))
        assert jornadas[3].cruces[0] == jornadas[0].cruces[0].invertido()

    def test_cada_pareja_se_ve_dos_veces(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture(vueltas=2))
        todos = [frozenset((c.local, c.visitante)) for j in jornadas for c in j.cruces]
        assert len(todos) == 12 and len(set(todos)) == 6


class TestJornadasForzadas:
    def test_reproduce_el_calendario_de_siete_del_sistema_anterior(self):
        """El `range(7)` mágico, ahora pedido explícitamente."""
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture(jornadas_forzadas=7))
        assert len(jornadas) == 7

    def test_repite_el_ciclo_cuando_faltan_jornadas(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture(jornadas_forzadas=7))
        assert jornadas[3].cruces == jornadas[0].cruces

    def test_trunca_cuando_sobran(self):
        jornadas = RoundRobin().generar(equipos(8), ConfigFixture(jornadas_forzadas=3))
        assert len(jornadas) == 3

    def test_renumera_de_forma_continua(self):
        jornadas = RoundRobin().generar(equipos(4), ConfigFixture(jornadas_forzadas=7))
        assert [j.numero for j in jornadas] == [1, 2, 3, 4, 5, 6, 7]


class TestTamanoDeCuadro:
    @pytest.mark.parametrize(
        "n,esperado", [(2, 2), (3, 4), (4, 4), (5, 8), (8, 8), (9, 16), (16, 16)]
    )
    def test_redondea_a_la_potencia_de_dos_siguiente(self, n, esperado):
        assert tamano_de_cuadro(n) == esperado

    def test_por_encima_de_16_el_cuadro_crece(self):
        """Cambio de comportamiento: antes se recortaba a 16 (§12)."""
        assert tamano_de_cuadro(17) == 32
        assert tamano_de_cuadro(100) == 128

    def test_rechaza_menos_de_dos(self):
        with pytest.raises(ReglaInvalida):
            tamano_de_cuadro(1)


class TestOrdenDeSiembra:
    def test_cuadro_de_dos(self):
        assert orden_de_siembra(2) == (1, 2)

    def test_cuadro_de_cuatro(self):
        assert orden_de_siembra(4) == (1, 4, 2, 3)

    def test_cuadro_de_ocho(self):
        assert orden_de_siembra(8) == (1, 8, 4, 5, 2, 7, 3, 6)

    def test_cada_pareja_suma_tamano_mas_uno(self):
        for tamano in (2, 4, 8, 16, 32):
            siembra = orden_de_siembra(tamano)
            for i in range(0, tamano, 2):
                assert siembra[i] + siembra[i + 1] == tamano + 1

    def test_contiene_cada_posicion_una_vez(self):
        assert sorted(orden_de_siembra(16)) == list(range(1, 17))

    def test_rechaza_un_tamano_que_no_es_potencia_de_dos(self):
        with pytest.raises(ReglaInvalida):
            orden_de_siembra(6)

    def test_la_siembra_es_la_estandar_de_cualquier_cuadro(self):
        """Los valores exactos quedan fijados arriba; esto comprueba la
        propiedad que los define, para cualquier tamaño."""
        for tamano in (2, 4, 8, 16, 32, 64):
            siembra = orden_de_siembra(tamano)
            assert sorted(siembra) == list(range(1, tamano + 1))
            assert siembra[0] == 1 and siembra[1] == tamano


class TestEliminacionDirecta:
    def test_cruza_al_mejor_con_el_peor(self):
        jornadas = EliminacionDirecta().generar(equipos(4), ConfigFixture())
        assert jornadas[0].cruces == (Cruce("p1", "p4"), Cruce("p2", "p3"))

    def test_produce_una_sola_jornada(self):
        """La primera ronda; el resto del cuadro lo propaga el motor."""
        assert len(EliminacionDirecta().generar(equipos(8), ConfigFixture())) == 1

    def test_un_cuadro_completo_no_tiene_byes(self):
        jornada = EliminacionDirecta().generar(equipos(8), ConfigFixture())[0]
        assert jornada.descansan == ()
        assert len(jornada.cruces) == 4

    def test_los_mejores_sembrados_entran_con_bye(self):
        """Con 5 participantes el cuadro es de 8: los tres primeros pasan."""
        jornada = EliminacionDirecta().generar(equipos(5), ConfigFixture())[0]
        assert set(jornada.descansan) == {"p1", "p2", "p3"}
        assert jornada.cruces == (Cruce("p4", "p5"),)

    def test_nadie_se_queda_fuera(self):
        for n in range(2, 12):
            jornada = EliminacionDirecta().generar(equipos(n), ConfigFixture())[0]
            assert set(jornada.participantes) == set(equipos(n))

    def test_con_tres_participantes_el_primero_espera(self):
        jornada = EliminacionDirecta().generar(equipos(3), ConfigFixture())[0]
        assert jornada.descansan == ("p1",)
        assert jornada.cruces == (Cruce("p2", "p3"),)

    def test_dos_participantes_son_una_final(self):
        jornada = EliminacionDirecta().generar(equipos(2), ConfigFixture())[0]
        assert jornada.cruces == (Cruce("p1", "p2"),)

    def test_menos_de_dos_no_da_cuadro(self):
        assert EliminacionDirecta().generar(["p1"], ConfigFixture()) == ()

    def test_admite_mas_de_16_participantes(self):
        """El tope fijo del bracket anterior desaparece."""
        jornada = EliminacionDirecta().generar(equipos(20), ConfigFixture())[0]
        assert len(jornada.cruces) + len(jornada.descansan) == 16
        assert set(jornada.participantes) == set(equipos(20))

    def test_rechaza_participantes_repetidos(self):
        with pytest.raises(ReglaInvalida):
            EliminacionDirecta().generar(["p1", "p1"], ConfigFixture())


class TestElProtocoloEsElSeam:
    @pytest.mark.parametrize("generador", [RoundRobin(), EliminacionDirecta()])
    def test_ambos_generadores_satisfacen_el_protocolo(self, generador):
        assert isinstance(generador, GeneradorDeFixture)

    def test_se_pueden_usar_sin_saber_cual_es(self):
        """OCP: un formato nuevo no obliga a editar los existentes."""
        config = ConfigFixture()
        for generador in (RoundRobin(), EliminacionDirecta()):
            jornadas = generador.generar(equipos(4), config)
            assert all(isinstance(j, Jornada) for j in jornadas)
