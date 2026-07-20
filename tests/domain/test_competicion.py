from __future__ import annotations

import pytest

from itc_deporte.domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    Fase,
    FaseDeGrupos,
    FaseEliminatoria,
    Grupo,
    ReglasDeCompeticion,
)
from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.errores import ErrorDeDominio
from itc_deporte.domain.reglas.desempate import (
    DESEMPATE_CLASICO,
    PorAFavor,
    PorPuntos,
)
from itc_deporte.domain.reglas.puntuacion import PorSets, VictoriaDerrota

VOLEIBOL = Deporte("voleyball", "Voleyball", "🏐")


def competicion(**cambios) -> Competicion:
    base = dict(id="c1", nombre="Intercursos 2026", deporte=VOLEIBOL)
    return Competicion(**{**base, **cambios})


class TestDeporte:
    def test_el_icono_es_opcional(self):
        assert Deporte("ajedrez", "Ajedrez").icono == ""

    def test_rechaza_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Deporte("", "Voleyball")

    def test_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Deporte("voleyball", "  ")

    def test_es_un_valor_no_una_entidad(self):
        """Dos deportes con los mismos datos son intercambiables."""
        assert Deporte("v", "Voley", "🏐") == Deporte("v", "Voley", "🏐")


class TestGrupo:
    def test_empieza_vacio(self):
        assert Grupo("g1", "Grupo A").participantes == ()

    def test_rechaza_participantes_repetidos(self):
        with pytest.raises(ErrorDeDominio):
            Grupo("g1", "Grupo A", ("p1", "p1"))

    def test_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Grupo("g1", " ")

    def test_la_identidad_es_el_id(self):
        assert Grupo("g1", "Grupo A") == Grupo("g1", "Grupo Alfa", ("p1",))

    def test_con_participante_devuelve_una_instancia_nueva(self):
        original = Grupo("g1", "Grupo A")
        ampliado = original.con_participante("p1")
        assert original.participantes == ()
        assert ampliado.participantes == ("p1",)

    def test_con_participante_rechaza_a_quien_ya_esta(self):
        with pytest.raises(ErrorDeDominio):
            Grupo("g1", "Grupo A", ("p1",)).con_participante("p1")

    def test_sin_participante_lo_retira(self):
        grupo = Grupo("g1", "Grupo A", ("p1", "p2"))
        assert grupo.sin_participante("p1").participantes == ("p2",)

    def test_sin_participante_rechaza_a_un_ajeno(self):
        with pytest.raises(ErrorDeDominio):
            Grupo("g1", "Grupo A").sin_participante("p9")


class TestFase:
    def test_rechaza_orden_negativo(self):
        with pytest.raises(ErrorDeDominio):
            Fase("f1", "Grupos", -1)

    def test_rechaza_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Fase("", "Grupos", 0)

    def test_la_identidad_es_el_id(self):
        assert Fase("f1", "Grupos", 0) == Fase("f1", "Otra cosa", 5)

    def test_las_subclases_comparten_la_identidad_por_id(self):
        assert FaseDeGrupos("f1", "Grupos", 0) == Fase("f1", "Grupos", 0)


class TestFaseDeGrupos:
    def test_reune_los_participantes_de_todos_los_grupos(self):
        fase = FaseDeGrupos(
            "f1",
            "Grupos",
            0,
            (Grupo("a", "A", ("p1", "p2")), Grupo("b", "B", ("p3",))),
        )
        assert fase.participantes == ("p1", "p2", "p3")

    def test_rechaza_un_participante_en_dos_grupos(self):
        with pytest.raises(ErrorDeDominio):
            FaseDeGrupos(
                "f1",
                "Grupos",
                0,
                (Grupo("a", "A", ("p1",)), Grupo("b", "B", ("p1",))),
            )

    def test_rechaza_grupos_con_id_repetido(self):
        with pytest.raises(ErrorDeDominio):
            FaseDeGrupos("f1", "Grupos", 0, (Grupo("a", "A"), Grupo("a", "Otra")))

    def test_hereda_las_invariantes_de_fase(self):
        with pytest.raises(ErrorDeDominio):
            FaseDeGrupos("f1", "Grupos", -1)

    def test_grupo_por_id(self):
        fase = FaseDeGrupos("f1", "Grupos", 0, (Grupo("a", "A"),))
        assert fase.grupo("a").nombre == "A"
        assert fase.grupo("z") is None

    def test_grupo_de_un_participante(self):
        fase = FaseDeGrupos(
            "f1", "Grupos", 0, (Grupo("a", "A", ("p1",)), Grupo("b", "B", ("p2",)))
        )
        assert fase.grupo_de("p2").id == "b"
        assert fase.grupo_de("p9") is None

    def test_una_fase_sin_grupos_es_valida(self):
        """El sorteo todavía no se ha ejecutado."""
        assert FaseDeGrupos("f1", "Grupos", 0).participantes == ()


class TestFaseEliminatoria:
    def test_rechaza_menos_de_dos_cupos(self):
        with pytest.raises(ErrorDeDominio):
            FaseEliminatoria("f2", "Eliminatoria", 1, cupos=1)

    def test_admite_un_numero_de_cupos_que_no_es_potencia_de_dos(self):
        """Un cuadro de 6 se completa con byes; el tope ya no es 16 fijo."""
        assert FaseEliminatoria("f2", "Eliminatoria", 1, cupos=6).cupos == 6

    def test_hereda_las_invariantes_de_fase(self):
        with pytest.raises(ErrorDeDominio):
            FaseEliminatoria("", "Eliminatoria", 1)


class TestCompeticion:
    def test_empieza_en_borrador_y_sin_fases(self):
        c = competicion()
        assert c.estado is EstadoCompeticion.BORRADOR
        assert c.fases == ()
        assert c.primera_fase is None

    def test_la_identidad_es_el_id(self):
        assert competicion(nombre="Uno") == competicion(nombre="Dos")
        assert competicion(id="c1") != competicion(id="c2")

    def test_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            competicion(nombre="   ")

    def test_rechaza_fases_con_id_repetido(self):
        fases = (FaseDeGrupos("f1", "Grupos", 0), FaseEliminatoria("f1", "Elim", 1))
        with pytest.raises(ErrorDeDominio):
            competicion(fases=fases)

    def test_rechaza_dos_fases_con_el_mismo_orden(self):
        fases = (FaseDeGrupos("f1", "Grupos", 0), FaseEliminatoria("f2", "Elim", 0))
        with pytest.raises(ErrorDeDominio):
            competicion(fases=fases)

    def test_con_fase_devuelve_una_instancia_nueva(self):
        original = competicion()
        ampliada = original.con_fase(FaseDeGrupos("f1", "Grupos", 0))
        assert original.fases == ()
        assert len(ampliada.fases) == 1

    def test_sin_fase_la_retira(self):
        c = competicion().con_fase(FaseDeGrupos("f1", "Grupos", 0))
        assert c.sin_fase("f1").fases == ()

    def test_sin_fase_rechaza_una_fase_inexistente(self):
        with pytest.raises(ErrorDeDominio):
            competicion().sin_fase("f9")


class TestComposicionDeFases:
    """El requisito "grupos y/o partidos": la competición compone su formato."""

    @pytest.fixture
    def mixta(self) -> Competicion:
        return competicion(
            fases=(
                FaseEliminatoria("elim", "Eliminatoria", 1, cupos=8),
                FaseDeGrupos("grupos", "Fase de grupos", 0),
            )
        )

    def test_las_fases_se_ordenan_por_orden_no_por_insercion(self, mixta):
        assert [f.id for f in mixta.fases_ordenadas] == ["grupos", "elim"]

    def test_la_primera_fase_es_la_de_menor_orden(self, mixta):
        assert mixta.primera_fase.id == "grupos"

    def test_fase_siguiente(self, mixta):
        assert mixta.fase_siguiente_a("grupos").id == "elim"

    def test_la_ultima_fase_no_tiene_siguiente(self, mixta):
        assert mixta.fase_siguiente_a("elim") is None

    def test_fase_siguiente_a_una_fase_ajena_es_none(self, mixta):
        assert mixta.fase_siguiente_a("f9") is None

    def test_una_competicion_solo_de_grupos_es_valida(self):
        """Liga sin playoffs."""
        c = competicion(fases=(FaseDeGrupos("g", "Liga", 0),))
        assert c.fase_siguiente_a("g") is None

    def test_una_competicion_solo_eliminatoria_es_valida(self):
        """Copa a partido único, sin fase previa."""
        c = competicion(fases=(FaseEliminatoria("e", "Copa", 0, cupos=16),))
        assert c.primera_fase.cupos == 16


class TestIdentidadDeLasEntidades:
    """Las entidades se indexan por id: hash y comparación deben ser coherentes."""

    def test_los_grupos_se_pueden_usar_como_clave(self):
        indice = {Grupo("g1", "Grupo A"): "tabla"}
        assert indice[Grupo("g1", "Renombrado", ("p1",))] == "tabla"

    def test_las_fases_se_pueden_usar_como_clave(self):
        indice = {Fase("f1", "Grupos", 0): "jornadas"}
        assert indice[FaseDeGrupos("f1", "Otra", 9)] == "jornadas"

    def test_las_competiciones_se_pueden_usar_como_clave(self):
        indice = {competicion(): "datos"}
        assert indice[competicion(nombre="Otro nombre")] == "datos"

    def test_ninguna_entidad_se_compara_con_otros_tipos(self):
        assert Grupo("g1", "A") != "g1"
        assert Fase("f1", "Grupos", 0) != "f1"
        assert competicion() != "c1"

    def test_rechazan_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Grupo("", "Grupo A")
        with pytest.raises(ErrorDeDominio):
            Competicion(id="", nombre="X", deporte=VOLEIBOL)

    def test_una_fase_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Fase("f1", "   ", 0)


class TestReglasDeCompeticion:
    def test_por_defecto_reproduce_las_reglas_del_sistema_anterior(self):
        """3/1/0 y desempate por puntos, diferencia y a favor."""
        reglas = ReglasDeCompeticion()
        assert reglas.puntuacion == VictoriaDerrota()
        assert reglas.desempate == DESEMPATE_CLASICO

    def test_una_competicion_nueva_las_lleva_puestas(self):
        assert competicion().reglas.puntuacion.puntos(Marcador(2, 1)) == (3, 0)

    def test_el_voleibol_solo_cambia_la_puntuacion(self):
        """El resto de la competición no se entera."""
        voley = competicion(reglas=ReglasDeCompeticion(puntuacion=PorSets()))
        assert voley.reglas.puntuacion.puntos(Marcador(3, 2)) == (2, 1)
        assert voley.reglas.desempate == DESEMPATE_CLASICO

    def test_admite_otro_orden_de_desempate(self):
        reglas = ReglasDeCompeticion(desempate=(PorPuntos(), PorAFavor()))
        assert len(reglas.desempate) == 2

    def test_rechaza_quedarse_sin_criterios_de_desempate(self):
        with pytest.raises(ErrorDeDominio):
            ReglasDeCompeticion(desempate=())
