"""El catálogo de reglas, en sus dos direcciones.

El test que más vale es `TestRoundTrip`: recorre **todas** las reglas
registradas y comprueba que guardar y volver a leer devuelve la misma. Así, dar
de alta una regla nueva y olvidarse de la mitad del registro se detecta solo.
"""

from __future__ import annotations

import pytest

from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.errores import ReglaInvalida
from itc_deporte.domain.reglas.catalogo import (
    DEPORTES,
    DESEMPATES,
    FIXTURES,
    NOMBRES_DE_DESEMPATE,
    NOMBRES_DE_FIXTURE,
    NOMBRES_DE_PUNTUACION,
    PUNTUACIONES,
    DeporteDelCatalogo,
    crear_desempate,
    crear_fixture,
    crear_puntuacion,
    nombre_de_desempate,
    nombre_de_fixture,
    nombre_de_puntuacion,
    parametros_de,
)
from itc_deporte.domain.reglas.desempate import PorEnfrentamientoDirecto, PorPuntos
from itc_deporte.domain.reglas.puntuacion import PorSets, VictoriaDerrota


class TestRoundTrip:
    """Guardar y volver a leer no puede cambiar la regla."""

    @pytest.mark.parametrize("tipo", sorted(PUNTUACIONES))
    def test_toda_puntuacion_registrada_va_y_vuelve(self, tipo):
        original = crear_puntuacion(tipo)
        assert nombre_de_puntuacion(original) == tipo
        assert crear_puntuacion(tipo, parametros_de(original)) == original

    @pytest.mark.parametrize("tipo", sorted(DESEMPATES))
    def test_todo_desempate_registrado_va_y_vuelve(self, tipo):
        original = crear_desempate(tipo, VictoriaDerrota())
        assert nombre_de_desempate(original) == tipo

    @pytest.mark.parametrize("tipo", sorted(FIXTURES))
    def test_todo_fixture_registrado_va_y_vuelve(self, tipo):
        original = crear_fixture(tipo)
        assert nombre_de_fixture(original) == tipo

    def test_conserva_los_parametros_a_medida(self):
        original = PorSets(umbral_ajustado=1, victoria=5)
        copia = crear_puntuacion(
            nombre_de_puntuacion(original), parametros_de(original)
        )
        assert copia == original


class TestLosDosRegistrosCoinciden:
    """Un nombre en un sentido y no en el otro deja una regla inguardable."""

    def test_las_puntuaciones(self):
        assert set(NOMBRES_DE_PUNTUACION.values()) == set(PUNTUACIONES)

    def test_los_desempates(self):
        assert set(NOMBRES_DE_DESEMPATE.values()) == set(DESEMPATES)

    def test_los_fixtures(self):
        assert set(NOMBRES_DE_FIXTURE.values()) == set(FIXTURES)


class TestParametros:
    def test_una_regla_sin_parametros_da_vacio(self):
        assert parametros_de(PorPuntos()) == {}

    def test_no_guarda_la_puntuacion_compuesta(self):
        """El enfrentamiento directo compone una puntuación; no se guarda dos
        veces, se reconstruye desde la de la competición."""
        criterio = PorEnfrentamientoDirecto(PorSets())
        assert parametros_de(criterio) == {}

    def test_los_valores_son_serializables(self):
        import json

        json.dumps(parametros_de(VictoriaDerrota()))


class TestReglasNoRegistradas:
    def test_una_puntuacion_ajena_no_se_puede_guardar(self):
        class MiRegla:
            def puntos(self, marcador):
                return (1, 0)

        with pytest.raises(ReglaInvalida, match="Añádela al catálogo"):
            nombre_de_puntuacion(MiRegla())

    def test_un_desempate_ajeno_tampoco(self):
        class MiCriterio:
            def valor(self, fila, contexto):
                return 0

        with pytest.raises(ReglaInvalida):
            nombre_de_desempate(MiCriterio())

    def test_un_fixture_ajeno_tampoco(self):
        class MiGenerador:
            def generar(self, participantes, config):
                return ()

        with pytest.raises(ReglaInvalida):
            nombre_de_fixture(MiGenerador())


class TestCrearDesdeElNombre:
    """Cubierto antes por los tests de plantilla, que ya no existen."""

    def test_crea_una_puntuacion(self):
        assert crear_puntuacion("por_sets") == PorSets()

    def test_pasa_los_parametros(self):
        assert crear_puntuacion("victoria_derrota", {"victoria": 2}).victoria == 2

    def test_crea_un_generador_de_fixture(self):
        assert type(crear_fixture("round_robin")).__name__ == "RoundRobin"
        assert type(crear_fixture("eliminacion_directa")).__name__ == "EliminacionDirecta"

    def test_el_enfrentamiento_directo_recibe_la_puntuacion(self):
        criterio = crear_desempate("enfrentamiento_directo", PorSets())
        assert criterio.puntuacion == PorSets()

    def test_los_demas_criterios_la_ignoran(self):
        assert crear_desempate("puntos", PorSets()) == PorPuntos()

    def test_una_puntuacion_inexistente_lista_las_que_hay(self):
        with pytest.raises(ReglaInvalida, match="por_sets"):
            crear_puntuacion("por_karma")

    def test_un_desempate_inexistente_tambien(self):
        with pytest.raises(ReglaInvalida, match="enfrentamiento_directo"):
            crear_desempate("por_simpatia", VictoriaDerrota())

    def test_un_fixture_inexistente_tambien(self):
        with pytest.raises(ReglaInvalida, match="round_robin"):
            crear_fixture("suizo")

    def test_parametros_que_la_regla_no_conoce(self):
        with pytest.raises(ReglaInvalida, match="Parámetros inválidos"):
            crear_puntuacion("por_sets", {"color": "azul"})


class TestCatalogoDeDeportes:
    """Cada deporte trae sus reglas. Antes toda competición nacía con el 3/1/0
    del fútbol, viniera del deporte que viniera."""

    @pytest.mark.parametrize("clave", sorted(DEPORTES))
    def test_todo_deporte_registrado_produce_reglas_validas(self, clave):
        """El test que más vale: recorre el catálogo entero, así que registrar
        un deporte con una regla mal escrita se detecta solo."""
        deporte = DEPORTES[clave]
        reglas = deporte.reglas()
        assert reglas.puntuacion is not None
        assert len(reglas.desempate) == len(deporte.desempate)

    @pytest.mark.parametrize("clave", sorted(DEPORTES))
    def test_la_clave_coincide_con_el_id(self, clave):
        assert DEPORTES[clave].id == clave

    @pytest.mark.parametrize("clave", sorted(DEPORTES))
    def test_su_puntuacion_esta_registrada(self, clave):
        """Si no lo estuviera, la competición no se podría guardar."""
        deporte = DEPORTES[clave]
        assert nombre_de_puntuacion(deporte.puntuacion_por_defecto()) == deporte.puntuacion

    @pytest.mark.parametrize("clave", sorted(DEPORTES))
    def test_se_convierte_en_un_deporte_del_dominio(self, clave):
        deporte = DEPORTES[clave].deporte()
        assert deporte.id == clave
        assert deporte.nombre

    def test_el_voleibol_puntua_por_sets(self):
        puntuacion = DEPORTES["voleyball"].puntuacion_por_defecto()
        assert puntuacion.puntos(Marcador(3, 0)) == (3, 0)
        assert puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_el_microfutbol_sigue_con_el_clasico(self):
        puntuacion = DEPORTES["microfutbol"].puntuacion_por_defecto()
        assert puntuacion.puntos(Marcador(2, 1)) == (3, 0)
        assert puntuacion.puntos(Marcador(1, 1)) == (1, 1)

    def test_el_baloncesto_no_premia_el_empate(self):
        puntuacion = DEPORTES["baloncesto"].puntuacion_por_defecto()
        assert puntuacion.puntos(Marcador(80, 70)) == (2, 0)
        assert puntuacion.puntos(Marcador(70, 70)) == (0, 0)

    def test_las_reglas_se_pueden_ajustar_al_crear(self):
        """El desempate se rehace sobre la puntuación ajustada, no sobre la de
        por defecto."""
        deporte = DEPORTES["microfutbol"]
        reglas = deporte.reglas(VictoriaDerrota(victoria=2, empate=1, derrota=0))
        assert reglas.puntuacion.puntos(Marcador(3, 0)) == (2, 0)

    def test_el_enfrentamiento_directo_se_arma_sobre_la_puntuacion_elegida(self):
        """Compone un sistema de puntuación: uno armado sobre el 3/1/0 daría
        otra cosa dentro de una competición por sets."""
        a_medida = DeporteDelCatalogo(
            "x", "X", puntuacion="por_sets", desempate=("enfrentamiento_directo",)
        )
        criterio = a_medida.reglas().desempate[0]
        assert criterio.puntuacion == PorSets()

    def test_un_deporte_a_medida_con_puntuacion_ajena_lo_dice(self):
        with pytest.raises(ReglaInvalida, match="por_sets"):
            DeporteDelCatalogo("x", "X", puntuacion="por_karma").reglas()
