from __future__ import annotations

import pytest

from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.errores import ErrorDeDominio
from itc_deporte.domain.motor.bracket import (
    Bracket,
    SlotDeBracket,
    nombre_de_ronda,
)


def equipos(n: int) -> list[str]:
    return [f"p{i}" for i in range(1, n + 1)]


def gana_local(bracket: Bracket, ronda: int, posicion: int) -> Bracket:
    return bracket.con_resultado(ronda, posicion, Marcador(1, 0))


def resolver_ronda(bracket: Bracket, ronda: int) -> Bracket:
    """Cierra todos los cruces jugables de una ronda con victoria local."""
    for casilla in bracket.rondas[ronda]:
        if casilla.listo and casilla.ganador() is None:
            bracket = gana_local(bracket, ronda, casilla.posicion)
    return bracket


class TestNombreDeRonda:
    @pytest.mark.parametrize(
        "partidos,esperado",
        [
            (1, "Final"),
            (2, "Semifinal"),
            (4, "Cuartos de final"),
            (8, "Octavos de final"),
            (16, "Dieciseisavos de final"),
        ],
    )
    def test_nombres_habituales(self, partidos, esperado):
        assert nombre_de_ronda(partidos) == esperado

    def test_mas_alla_se_nombra_por_tamano(self):
        """El cuadro ya no topa en 16, así que hay rondas sin nombre propio."""
        assert nombre_de_ronda(32) == "Ronda de 64"

    def test_rechaza_una_ronda_vacia(self):
        with pytest.raises(ErrorDeDominio):
            nombre_de_ronda(0)


class TestSlot:
    def test_una_casilla_con_los_dos_esta_lista(self):
        assert SlotDeBracket(0, 0, "a", "b").listo

    def test_una_casilla_a_medias_no_esta_lista(self):
        assert not SlotDeBracket(0, 0, "a", None).listo

    def test_un_bye_avanza_solo(self):
        assert SlotDeBracket(0, 0, "a", None).ganador() == "a"
        assert SlotDeBracket(0, 0, None, "b").ganador() == "b"

    def test_una_casilla_vacia_no_es_bye(self):
        vacia = SlotDeBracket(0, 0)
        assert not vacia.es_bye and vacia.ganador() is None

    def test_sin_marcador_no_hay_ganador(self):
        assert SlotDeBracket(0, 0, "a", "b").ganador() is None

    def test_gana_quien_marca_mas(self):
        assert SlotDeBracket(0, 0, "a", "b", Marcador(2, 1)).ganador() == "a"
        assert SlotDeBracket(0, 0, "a", "b", Marcador(1, 2)).ganador() == "b"

    def test_un_empate_no_resuelve(self):
        """El cuadro no puede avanzar a nadie con un 1-1."""
        assert SlotDeBracket(0, 0, "a", "b", Marcador(1, 1)).ganador() is None


class TestConstruccion:
    def test_un_cuadro_de_ocho_tiene_tres_rondas(self):
        bracket = Bracket.desde_clasificados(equipos(8))
        assert bracket.total_rondas == 3
        assert [len(r) for r in bracket.rondas] == [4, 2, 1]

    def test_siembra_al_mejor_contra_el_peor(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        primera = bracket.rondas[0]
        assert (primera[0].local, primera[0].visitante) == ("p1", "p4")
        assert (primera[1].local, primera[1].visitante) == ("p2", "p3")

    def test_las_rondas_se_nombran_solas(self):
        bracket = Bracket.desde_clasificados(equipos(8))
        assert [bracket.nombre_de(r) for r in range(3)] == [
            "Cuartos de final",
            "Semifinal",
            "Final",
        ]

    def test_dos_participantes_son_solo_una_final(self):
        bracket = Bracket.desde_clasificados(equipos(2))
        assert bracket.total_rondas == 1
        assert bracket.nombre_de(0) == "Final"

    def test_las_rondas_posteriores_nacen_vacias(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        final = bracket.slot(1, 0)
        assert final.local is None and final.visitante is None

    def test_admite_mas_de_dieciseis(self):
        """El tope fijo del cuadro anterior desaparece."""
        bracket = Bracket.desde_clasificados(equipos(20))
        assert bracket.total_rondas == 5
        assert bracket.nombre_de(0) == "Dieciseisavos de final"

    def test_rechaza_menos_de_dos(self):
        with pytest.raises(ErrorDeDominio):
            Bracket.desde_clasificados(["p1"])

    def test_rechaza_repetidos(self):
        with pytest.raises(ErrorDeDominio):
            Bracket.desde_clasificados(["p1", "p1"])


class TestByes:
    def test_los_mejores_sembrados_entran_con_bye(self):
        bracket = Bracket.desde_clasificados(equipos(5))
        byes = [c for c in bracket.rondas[0] if c.es_bye]
        assert {c.ganador() for c in byes} == {"p1", "p2", "p3"}

    def test_el_bye_avanza_sin_jugar(self):
        """Con 3 participantes, p1 aparece en la final sin haber jugado."""
        bracket = Bracket.desde_clasificados(equipos(3))
        assert bracket.slot(1, 0).local == "p1"

    def test_nadie_se_queda_fuera(self):
        for n in range(2, 18):
            bracket = Bracket.desde_clasificados(equipos(n))
            presentes = {
                p
                for casilla in bracket.rondas[0]
                for p in (casilla.local, casilla.visitante)
                if p is not None
            }
            assert presentes == set(equipos(n))

    def test_un_cuadro_de_tres_lo_decide_una_final(self):
        bracket = Bracket.desde_clasificados(equipos(3))
        bracket = gana_local(bracket, 0, 1)  # p2 vence a p3
        assert (bracket.slot(1, 0).local, bracket.slot(1, 0).visitante) == ("p1", "p2")


class TestPropagacion:
    def test_el_ganador_sube_a_la_ronda_siguiente(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        bracket = gana_local(bracket, 0, 0)  # p1 vence a p4
        assert bracket.slot(1, 0).local == "p1"

    def test_los_dos_ganadores_ocupan_la_final(self):
        bracket = resolver_ronda(Bracket.desde_clasificados(equipos(4)), 0)
        final = bracket.slot(1, 0)
        assert (final.local, final.visitante) == ("p1", "p2")

    def test_propaga_en_cascada_hasta_el_campeon(self):
        bracket = Bracket.desde_clasificados(equipos(8))
        for ronda in range(3):
            bracket = resolver_ronda(bracket, ronda)
        assert bracket.campeon() == "p1"

    def test_sin_terminar_no_hay_campeon(self):
        assert Bracket.desde_clasificados(equipos(4)).campeon() is None

    def test_un_empate_deja_el_cuadro_encallado(self):
        bracket = Bracket.desde_clasificados(equipos(2))
        bracket = bracket.con_resultado(0, 0, Marcador(1, 1))
        assert bracket.campeon() is None

    def test_devuelve_un_cuadro_nuevo(self):
        original = Bracket.desde_clasificados(equipos(4))
        modificado = gana_local(original, 0, 0)
        assert original.slot(0, 0).marcador is None
        assert modificado.slot(0, 0).marcador == Marcador(1, 0)


class TestCorreccionDeResultados:
    def test_corregir_un_resultado_recoloca_al_ganador(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        bracket = gana_local(bracket, 0, 0)
        assert bracket.slot(1, 0).local == "p1"
        bracket = bracket.con_resultado(0, 0, Marcador(0, 3))
        assert bracket.slot(1, 0).local == "p4"

    def test_corregir_arrastra_el_resultado_fantasma_de_la_ronda_siguiente(self):
        """Si cambia quién juega la final, el resultado de la final se descarta."""
        bracket = resolver_ronda(Bracket.desde_clasificados(equipos(4)), 0)
        bracket = gana_local(bracket, 1, 0)  # p1 campeón
        assert bracket.campeon() == "p1"

        bracket = bracket.con_resultado(0, 0, Marcador(0, 3))  # ahora pasa p4
        assert bracket.slot(1, 0).marcador is None
        assert bracket.campeon() is None

    def test_corregir_sin_cambiar_al_ganador_conserva_lo_de_abajo(self):
        bracket = resolver_ronda(Bracket.desde_clasificados(equipos(4)), 0)
        bracket = gana_local(bracket, 1, 0)
        bracket = bracket.con_resultado(0, 0, Marcador(5, 0))  # p1 sigue ganando
        assert bracket.campeon() == "p1"


class TestConsultasYErrores:
    def test_pendientes_lista_los_cruces_jugables_sin_resultado(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        assert len(bracket.pendientes()) == 2

    def test_las_casillas_incompletas_no_son_pendientes(self):
        """La final no está pendiente: todavía no se sabe quién la juega."""
        bracket = Bracket.desde_clasificados(equipos(4))
        assert all(c.ronda == 0 for c in bracket.pendientes())

    def test_un_bye_no_queda_pendiente(self):
        bracket = Bracket.desde_clasificados(equipos(3))
        assert len(bracket.pendientes()) == 1

    def test_al_terminar_no_queda_nada_pendiente(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        for ronda in range(2):
            bracket = resolver_ronda(bracket, ronda)
        assert bracket.pendientes() == ()

    def test_rechaza_una_ronda_inexistente(self):
        with pytest.raises(ErrorDeDominio, match="ronda"):
            Bracket.desde_clasificados(equipos(4)).slot(9, 0)

    def test_rechaza_una_casilla_inexistente(self):
        with pytest.raises(ErrorDeDominio, match="casilla"):
            Bracket.desde_clasificados(equipos(4)).slot(0, 9)

    def test_rechaza_cargar_un_resultado_en_una_casilla_incompleta(self):
        bracket = Bracket.desde_clasificados(equipos(4))
        with pytest.raises(ErrorDeDominio, match="contendientes"):
            bracket.con_resultado(1, 0, Marcador(1, 0))

    def test_rechaza_un_cuadro_sin_rondas(self):
        with pytest.raises(ErrorDeDominio):
            Bracket(())

    def test_rechaza_un_cuadro_que_no_acaba_en_final(self):
        with pytest.raises(ErrorDeDominio):
            Bracket((tuple(SlotDeBracket(0, p) for p in range(2)),))
