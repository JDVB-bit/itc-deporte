"""El traductor de la migración.

El requisito de §9 del plan es que **las filas irresolubles no se descarten en
silencio**. La mayoría de estos tests comprueban exactamente eso: que lo que no
se puede traducir aparece en el reporte con su motivo, en vez de desaparecer.

Los casos raros no son inventados: salen de los tests de caracterización de la
Fase 0, que documentaron cómo se comporta el parser heredado.
"""

from __future__ import annotations

import datetime as dt

import pytest

from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.infraestructura.migracion import traducir
from itc_deporte.infraestructura.migracion.traductor import (
    id_de_competicion,
    id_de_participante,
)


def equipo(id_=1, categoria="PRIMERA", deporte="Microfutbol", curso="601", nombre="Los Tigres"):
    return dict(
        id=id_, categoria=categoria, deporte=deporte, curso=curso, nombre=nombre
    )


def partido(id_=10, enf="Los Tigres (601) vs Las Panteras (602)", estado="Finalizado",
            g1=3, g2=1, categoria="PRIMERA", deporte="Microfutbol",
            fecha="2026-07-25 15:00"):
    return dict(
        id=id_, categoria=categoria, deporte=deporte, fecha=fecha, enf=enf,
        estado=estado, g1=g1, g2=g2,
    )


def llave(id_=20, ronda="FINAL", slot=0, equipo1="Los Tigres", curso1="601",
          equipo2="Las Panteras", curso2="602", estado="Pendiente", g1=0, g2=0):
    return dict(
        id=id_, categoria="PRIMERA", deporte="Microfutbol", ronda=ronda, slot=slot,
        equipo1=equipo1, curso1=curso1, equipo2=equipo2, curso2=curso2,
        estado=estado, g1=g1, g2=g2,
    )


DOS_EQUIPOS = [
    equipo(1, curso="601", nombre="Los Tigres"),
    equipo(2, curso="602", nombre="Las Panteras"),
]


def motivos(reporte):
    return [c.motivo for c in reporte.conflictos]


class TestCompeticiones:
    def test_una_por_pareja_de_categoria_y_deporte(self):
        reporte = traducir(
            [
                equipo(1, categoria="PRIMERA", deporte="Microfutbol"),
                equipo(2, categoria="PRIMERA", deporte="Baloncesto", curso="602"),
                equipo(3, categoria="SEGUNDA", deporte="Microfutbol", curso="801"),
            ]
        )
        assert len(reporte.competiciones) == 3

    def test_cada_una_lleva_sus_dos_fases(self):
        reporte = traducir(DOS_EQUIPOS)
        fases = reporte.competiciones[0].fases_ordenadas
        assert [f.nombre for f in fases] == ["Fase de grupos", "Eliminación directa"]

    def test_conserva_las_siete_jornadas_del_sistema_anterior(self):
        reporte = traducir(DOS_EQUIPOS)
        grupos = reporte.competiciones[0].fases_ordenadas[0]
        assert grupos.config_fixture.jornadas_forzadas == 7

    def test_el_voleibol_migra_con_puntuacion_por_sets(self):
        """El cambio de §12 ocurre aquí: los partidos ya jugados se recalculan."""
        reporte = traducir([equipo(deporte="Voleyball")])
        reglas = reporte.competiciones[0].reglas
        assert reglas.puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_el_resto_conserva_el_3_1_0(self):
        reporte = traducir([equipo(deporte="Microfutbol")])
        reglas = reporte.competiciones[0].reglas
        assert reglas.puntuacion.puntos(Marcador(2, 1)) == (3, 0)


class TestParticipantes:
    def test_cada_equipo_pasa_a_participante(self):
        reporte = traducir(DOS_EQUIPOS)
        assert len(reporte.participantes) == 2

    def test_el_curso_pasa_a_division(self):
        reporte = traducir(DOS_EQUIPOS)
        assert reporte.participantes[0].division_id == "601"

    def test_la_categoria_es_la_division_padre(self):
        reporte = traducir(DOS_EQUIPOS)
        curso = next(d for d in reporte.divisiones if d.id == "601")
        assert curso.padre_id == "PRIMERA"

    def test_el_nombre_deja_de_ser_la_identidad(self):
        """Lo que arregla el problema 2 del diagnóstico."""
        reporte = traducir(DOS_EQUIPOS)
        assert all(p.id != p.nombre for p in reporte.participantes)

    def test_dos_equipos_homonimos_en_cursos_distintos_no_se_mezclan(self):
        reporte = traducir(
            [
                equipo(1, curso="601", nombre="Los Tigres"),
                equipo(2, curso="602", nombre="Los Tigres"),
            ]
        )
        assert len({p.id for p in reporte.participantes}) == 2
        assert not reporte.hay_conflictos


class TestConflictosDeEquipos:
    def test_un_curso_invalido_se_reporta(self):
        reporte = traducir([equipo(curso="999")])
        assert motivos(reporte) == ["curso inválido"]
        assert reporte.participantes == []

    def test_un_nombre_vacio_se_reporta(self):
        reporte = traducir([equipo(nombre="   ")])
        assert motivos(reporte) == ["nombre vacío"]

    def test_un_equipo_duplicado_se_reporta(self):
        """La corrupción que `limpiar_equipos_corruptos` borraba en silencio."""
        reporte = traducir([equipo(1), equipo(2)])
        assert motivos(reporte) == ["equipo duplicado"]
        assert len(reporte.participantes) == 1

    def test_el_conflicto_dice_de_qué_fila_viene(self):
        reporte = traducir([equipo(id_=77, curso="999")])
        assert reporte.conflictos[0].fila_id == 77
        assert "999" in str(reporte.conflictos[0])


class TestJugadores:
    def test_pasan_a_miembros_del_participante(self):
        reporte = traducir(
            DOS_EQUIPOS,
            jugadores=[
                dict(id=1, categoria="PRIMERA", deporte="Microfutbol", curso="601",
                     equipo="Los Tigres", nombre="Ana"),
                dict(id=2, categoria="PRIMERA", deporte="Microfutbol", curso="601",
                     equipo="Los Tigres", nombre="Luis"),
            ],
        )
        tigres = next(p for p in reporte.participantes if p.nombre == "Los Tigres")
        assert {m.nombre for m in tigres.miembros} == {"Ana", "Luis"}

    def test_un_jugador_de_un_equipo_inexistente_se_reporta(self):
        reporte = traducir(
            DOS_EQUIPOS,
            jugadores=[
                dict(id=1, categoria="PRIMERA", deporte="Microfutbol", curso="601",
                     equipo="Fantasma", nombre="Ana")
            ],
        )
        assert motivos(reporte) == ["el equipo del jugador no existe"]

    def test_un_jugador_duplicado_se_reporta(self):
        jugador = dict(id=1, categoria="PRIMERA", deporte="Microfutbol", curso="601",
                       equipo="Los Tigres", nombre="Ana")
        reporte = traducir(DOS_EQUIPOS, jugadores=[jugador, {**jugador, "id": 2}])
        assert motivos(reporte) == ["jugador duplicado"]


class TestPartidos:
    def test_se_resuelven_a_ids_de_participante(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido()])
        enfrentamiento = reporte.enfrentamientos[0]
        competicion = id_de_competicion("PRIMERA", "Microfutbol")
        assert enfrentamiento.local == id_de_participante(competicion, "601", "Los Tigres")
        assert enfrentamiento.visitante == id_de_participante(
            competicion, "602", "Las Panteras"
        )

    def test_conserva_el_marcador(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido(g1=3, g2=1)])
        assert reporte.enfrentamientos[0].marcador == Marcador(3, 1)

    def test_un_partido_pendiente_no_lleva_marcador(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido(estado="Pendiente")])
        assert not reporte.enfrentamientos[0].esta_finalizado

    def test_conserva_la_fecha(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido()])
        assert reporte.enfrentamientos[0].fecha == dt.datetime(2026, 7, 25, 15, 0)

    def test_una_fecha_ilegible_no_tumba_la_migracion(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido(fecha="el sábado")])
        assert reporte.enfrentamientos[0].fecha is None

    def test_van_a_la_fase_de_grupos(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido()])
        competicion = reporte.competiciones[0]
        assert reporte.enfrentamientos[0].fase_id == competicion.fases_ordenadas[0].id


class TestConflictosDePartidos:
    def test_un_enfrentamiento_no_parseable_se_reporta(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido(enf="texto suelto")])
        assert motivos(reporte) == ["no se pudo parsear"]
        assert reporte.enfrentamientos == []

    def test_un_equipo_no_inscrito_se_reporta(self):
        reporte = traducir(
            DOS_EQUIPOS, partidos=[partido(enf="Fantasma (601) vs Las Panteras (602)")]
        )
        assert motivos(reporte) == ["no se pudo resolver a un equipo inscrito"]
        assert "Fantasma (601)" in reporte.conflictos[0].dato

    def test_dice_cuál_de_los_dos_lados_falló(self):
        reporte = traducir(
            DOS_EQUIPOS, partidos=[partido(enf="Fantasma (601) vs Otro (602)")]
        )
        assert " y " in reporte.conflictos[0].dato

    def test_un_nombre_con_vs_no_se_traduce_a_ciegas(self):
        """El caso que los tests de la Fase 0 documentaron como roto.

        El parser heredado parte por el primer ' vs ', así que este enfrentamiento
        produce basura. Lo importante es que sale en el reporte en lugar de
        migrarse mal.
        """
        reporte = traducir(
            DOS_EQUIPOS,
            partidos=[partido(enf="Nos vs Ellos (601) vs Las Panteras (602)")],
        )
        assert motivos(reporte) == ["no se pudo resolver a un equipo inscrito"]
        assert reporte.enfrentamientos == []

    def test_un_equipo_contra_si_mismo_se_reporta(self):
        reporte = traducir(
            [equipo(1, curso="601", nombre="Los Tigres")],
            partidos=[partido(enf="Los Tigres (601) vs Los Tigres (601)")],
        )
        assert motivos(reporte) == ["un equipo contra sí mismo"]

    def test_un_partido_de_otra_categoria_no_cruza(self):
        """El índice está acotado por competición: un equipo de PRIMERA no
        resuelve un partido de SEGUNDA."""
        reporte = traducir(
            DOS_EQUIPOS,
            partidos=[partido(categoria="SEGUNDA")],
        )
        assert motivos(reporte) == ["no se pudo resolver a un equipo inscrito"]


class TestLlaves:
    def test_el_cuadro_heredado_se_migra(self):
        """El que la interfaz nunca llegó a mostrar."""
        reporte = traducir(DOS_EQUIPOS, llaves=[llave()])
        assert len(reporte.enfrentamientos) == 1
        assert reporte.enfrentamientos[0].ronda == 3  # FINAL

    def test_las_rondas_se_numeran_en_orden(self):
        reporte = traducir(
            DOS_EQUIPOS,
            llaves=[llave(1, ronda="OCTAVOS"), llave(2, ronda="SEMIFINAL")],
        )
        assert sorted(e.ronda for e in reporte.enfrentamientos) == [0, 2]

    def test_una_casilla_vacia_se_migra_igual(self):
        """Existe antes de saberse quién la ocupa."""
        reporte = traducir(DOS_EQUIPOS, llaves=[llave(equipo1=None, equipo2=None)])
        casilla = reporte.enfrentamientos[0]
        assert casilla.local is None and casilla.visitante is None

    def test_van_a_la_fase_eliminatoria(self):
        reporte = traducir(DOS_EQUIPOS, llaves=[llave()])
        competicion = reporte.competiciones[0]
        assert reporte.enfrentamientos[0].fase_id == competicion.fases_ordenadas[1].id

    def test_una_ronda_desconocida_se_reporta(self):
        reporte = traducir(DOS_EQUIPOS, llaves=[llave(ronda="TREINTAYDOSAVOS")])
        assert motivos(reporte) == ["ronda desconocida"]

    def test_una_casilla_con_equipo_no_inscrito_se_reporta(self):
        reporte = traducir(DOS_EQUIPOS, llaves=[llave(equipo1="Fantasma")])
        assert motivos(reporte) == ["casilla con un equipo no inscrito"]


class TestIdempotencia:
    """Traducir dos veces produce lo mismo: permite ensayar antes de escribir."""

    def test_los_ids_son_deterministas(self):
        una = traducir(DOS_EQUIPOS, partidos=[partido()])
        otra = traducir(DOS_EQUIPOS, partidos=[partido()])
        assert [p.id for p in una.participantes] == [p.id for p in otra.participantes]
        assert [e.id for e in una.enfrentamientos] == [
            e.id for e in otra.enfrentamientos
        ]

    def test_los_ids_toleran_tildes_y_espacios(self):
        reporte = traducir([equipo(nombre="Águilas del Récord")])
        assert reporte.participantes[0].id.endswith("aguilas-del-record")

    def test_el_nombre_original_se_conserva_intacto(self):
        reporte = traducir([equipo(nombre="Águilas del Récord")])
        assert reporte.participantes[0].nombre == "Águilas del Récord"


class TestNadaSePierdeEnSilencio:
    """El requisito de §9: toda fila o se traduce o se reporta."""

    def test_cada_equipo_sale_traducido_o_en_conflicto(self):
        equipos = [
            equipo(1, curso="601", nombre="Bueno"),
            equipo(2, curso="999", nombre="Curso malo"),
            equipo(3, curso="602", nombre="   "),
            equipo(4, curso="601", nombre="Bueno"),  # duplicado
        ]
        reporte = traducir(equipos)
        assert len(reporte.participantes) + len(reporte.conflictos) == len(equipos)

    def test_cada_partido_sale_traducido_o_en_conflicto(self):
        partidos = [
            partido(1),
            partido(2, enf="basura"),
            partido(3, enf="Fantasma (601) vs Las Panteras (602)"),
        ]
        reporte = traducir(DOS_EQUIPOS, partidos=partidos)
        assert len(reporte.enfrentamientos) + len(reporte.conflictos) == len(partidos)

    def test_una_migracion_limpia_no_reporta_nada(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido()])
        assert not reporte.hay_conflictos

    def test_el_resumen_cuenta_todo(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido()])
        assert "2 participantes" in reporte.resumen()
        assert "0 conflictos" in reporte.resumen()

    def test_sin_datos_no_revienta(self):
        reporte = traducir([])
        assert reporte.resumen().startswith("0 competiciones")


class TestCasosBorde:
    def test_un_jugador_sin_nombre_se_reporta(self):
        reporte = traducir(
            DOS_EQUIPOS,
            jugadores=[
                dict(id=1, categoria="PRIMERA", deporte="Microfutbol", curso="601",
                     equipo="Los Tigres", nombre="  ")
            ],
        )
        assert motivos(reporte) == ["nombre vacío"]

    def test_una_casilla_del_cuadro_contra_si_misma_se_reporta(self):
        reporte = traducir(
            [equipo(1, curso="601", nombre="Los Tigres")],
            llaves=[llave(equipo1="Los Tigres", curso1="601",
                          equipo2="Los Tigres", curso2="601")],
        )
        assert motivos(reporte) == ["un equipo contra sí mismo"]

    def test_una_casilla_finalizada_conserva_su_marcador(self):
        reporte = traducir(
            DOS_EQUIPOS, llaves=[llave(estado="Finalizado", g1=2, g2=0)]
        )
        assert reporte.enfrentamientos[0].marcador == Marcador(2, 0)

    def test_una_casilla_a_medias_no_se_finaliza(self):
        """Sin los dos contendientes no hay partido que cerrar."""
        reporte = traducir(
            DOS_EQUIPOS,
            llaves=[llave(equipo2=None, estado="Finalizado", g1=1, g2=0)],
        )
        assert not reporte.enfrentamientos[0].esta_finalizado

    def test_una_fecha_vacia_queda_en_none(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido(fecha=None)])
        assert reporte.enfrentamientos[0].fecha is None

    def test_una_fecha_sin_hora_se_entiende(self):
        reporte = traducir(DOS_EQUIPOS, partidos=[partido(fecha="2026-07-25")])
        assert reporte.enfrentamientos[0].fecha == dt.datetime(2026, 7, 25, 0, 0)

    def test_la_division_de_categoria_no_se_duplica(self):
        reporte = traducir(
            [equipo(1, curso="601"), equipo(2, curso="602", nombre="Otro")]
        )
        primeras = [d for d in reporte.divisiones if d.id == "PRIMERA"]
        assert len(primeras) == 1
