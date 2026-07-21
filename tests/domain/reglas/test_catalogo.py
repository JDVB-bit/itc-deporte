"""El catálogo de reglas, en sus dos direcciones.

El test que más vale es `TestRoundTrip`: recorre **todas** las reglas
registradas y comprueba que guardar y volver a leer devuelve la misma. Así, dar
de alta una regla nueva y olvidarse de la mitad del registro se detecta solo.
"""

from __future__ import annotations

import pytest

from itc_deporte.domain.errores import ReglaInvalida
from itc_deporte.domain.reglas.catalogo import (
    DESEMPATES,
    FIXTURES,
    NOMBRES_DE_DESEMPATE,
    NOMBRES_DE_FIXTURE,
    NOMBRES_DE_PUNTUACION,
    PUNTUACIONES,
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
