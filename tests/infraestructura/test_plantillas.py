"""La semilla ITC y su carga.

El test central de esta fase es `TestParidadConElSistemaActual`: comprueba que
instanciar la plantilla ITC reproduce la configuración que el software maneja
hoy, contrastándola contra las constantes del módulo heredado en lugar de
contra valores tecleados a mano.
"""

from __future__ import annotations

import datetime as dt
import json

import pytest

from itc_deporte.domain.competicion import FaseDeGrupos, FaseEliminatoria
from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.errores import ReglaInvalida
from itc_deporte.infraestructura.plantillas.cargador import (
    SEMILLAS,
    CatalogoIlegible,
    cargar_catalogo,
    cargar_semillas,
)
from itc_deporte.legado.motor_actual import CATEGORIAS_LOCAL, CURSOS_VALIDOS, DEPORTES

ITC = SEMILLAS / "itc.json"


@pytest.fixture
def semillas():
    return cargar_semillas()


@pytest.fixture
def voleibol(semillas):
    return next(p for p in semillas if p.deporte.nombre == "Voleyball")


@pytest.fixture
def microfutbol(semillas):
    return next(p for p in semillas if p.deporte.nombre == "Microfutbol")


class TestCarga:
    def test_la_semilla_itc_existe_en_el_repositorio(self):
        assert ITC.is_file()

    def test_carga_una_plantilla_por_deporte(self, semillas):
        assert len(semillas) == len(DEPORTES)

    def test_todas_vienen_marcadas_como_semilla(self, semillas):
        assert all(p.es_semilla for p in semillas)

    def test_los_ids_no_se_repiten(self, semillas):
        assert len({p.id for p in semillas}) == len(semillas)

    def test_todas_llevan_descripcion(self, semillas):
        assert all(p.descripcion for p in semillas)


class TestParidadConElSistemaActual:
    """Entregable de la fase: la plantilla reproduce lo que hay hoy."""

    def test_cubre_los_cuatro_deportes(self, semillas):
        assert {p.deporte.nombre for p in semillas} == set(DEPORTES)

    def test_conserva_los_iconos(self, semillas):
        assert all(p.deporte.icono for p in semillas)

    def test_las_divisiones_hoja_son_los_cursos_validos(self, microfutbol):
        catalogo = microfutbol.catalogo_de_divisiones()
        assert {d.id for d in catalogo.hojas()} == CURSOS_VALIDOS

    def test_las_raices_son_las_tres_categorias(self, microfutbol):
        catalogo = microfutbol.catalogo_de_divisiones()
        assert {d.id for d in catalogo.raices()} == set(CATEGORIAS_LOCAL)

    def test_cada_curso_cuelga_de_su_categoria(self, microfutbol):
        catalogo = microfutbol.catalogo_de_divisiones()
        for categoria, cursos in CATEGORIAS_LOCAL.items():
            assert {d.id for d in catalogo.hijas(categoria)} == set(cursos)

    def test_todas_las_plantillas_comparten_las_divisiones(self, semillas):
        divisiones = [{d.id for d in p.divisiones} for p in semillas]
        assert all(d == divisiones[0] for d in divisiones)

    def test_el_calendario_es_sabados_a_las_tres(self, microfutbol):
        calendario = microfutbol.calendario
        assert calendario.dia_de_la_semana == 5
        assert calendario.hora == dt.time(15, 0)
        assert calendario.cadencia_dias == 7

    def test_las_siete_jornadas_son_ahora_configuracion_explicita(self, microfutbol):
        """El `range(7)` mágico, trasladado a dato de la plantilla."""
        grupos = microfutbol.fases[0]
        assert grupos.config_fixture.jornadas_forzadas == 7

    def test_el_cuadro_final_sigue_siendo_de_dieciseis(self, microfutbol):
        eliminatoria = microfutbol.fases[1]
        assert eliminatoria.cupos == 16

    def test_el_desempate_es_el_de_siempre(self, microfutbol):
        assert microfutbol.desempate == ("puntos", "diferencia", "a_favor")


class TestPuntuacionPorDeporte:
    def test_los_deportes_de_gol_conservan_el_3_1_0(self, microfutbol):
        puntuacion = microfutbol.reglas().puntuacion
        assert puntuacion.puntos(Marcador(2, 1)) == (3, 0)
        assert puntuacion.puntos(Marcador(1, 1)) == (1, 1)

    def test_el_voleibol_pasa_a_puntuacion_por_sets(self, voleibol):
        """El cambio de comportamiento que motivaba el problema 6."""
        assert voleibol.reglas().puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_el_voleibol_ya_no_admite_empates(self, voleibol):
        with pytest.raises(ReglaInvalida):
            voleibol.reglas().puntuacion.puntos(Marcador(2, 2))


class TestInstanciarLaSemilla:
    def test_produce_una_competicion_con_sus_dos_fases(self, microfutbol):
        competicion = microfutbol.instanciar("c1", temporada="2026")
        grupos, eliminatoria = competicion.fases_ordenadas
        assert isinstance(grupos, FaseDeGrupos)
        assert isinstance(eliminatoria, FaseEliminatoria)

    def test_la_competicion_hereda_las_reglas_del_deporte(self, voleibol):
        competicion = voleibol.instanciar("c1")
        assert competicion.reglas.puntuacion.puntos(Marcador(3, 0)) == (3, 0)

    def test_el_organizador_puede_renombrarla(self, microfutbol):
        """La plantilla precarga; no impone."""
        competicion = microfutbol.instanciar("c1", nombre="Copa de mitad de año")
        assert competicion.nombre == "Copa de mitad de año"

    def test_los_generadores_de_fixture_se_resuelven(self, microfutbol):
        grupos, eliminatoria = microfutbol.fases
        assert type(grupos.generador()).__name__ == "RoundRobin"
        assert type(eliminatoria.generador()).__name__ == "EliminacionDirecta"


class TestFicherosMalFormados:
    def escribir(self, tmp_path, contenido):
        ruta = tmp_path / "catalogo.json"
        ruta.write_text(
            contenido if isinstance(contenido, str) else json.dumps(contenido),
            encoding="utf-8",
        )
        return ruta

    def test_json_invalido(self, tmp_path):
        with pytest.raises(CatalogoIlegible, match="no es JSON válido"):
            cargar_catalogo(self.escribir(tmp_path, "{no soy json"))

    def test_sin_lista_de_plantillas(self, tmp_path):
        with pytest.raises(CatalogoIlegible, match="plantillas"):
            cargar_catalogo(self.escribir(tmp_path, {"divisiones": []}))

    def test_plantilla_sin_id(self, tmp_path):
        catalogo = {"plantillas": [{"nombre": "X", "deporte": {"id": "a", "nombre": "A"}}]}
        with pytest.raises(CatalogoIlegible, match="'id'"):
            cargar_catalogo(self.escribir(tmp_path, catalogo))

    def test_tipo_de_fase_desconocido(self, tmp_path):
        catalogo = {
            "plantillas": [
                {
                    "id": "x",
                    "nombre": "X",
                    "deporte": {"id": "a", "nombre": "A"},
                    "fases": [{"tipo": "suizo", "nombre": "F", "orden": 0}],
                }
            ]
        }
        with pytest.raises(CatalogoIlegible, match="eliminatoria"):
            cargar_catalogo(self.escribir(tmp_path, catalogo))

    def test_hora_invalida(self, tmp_path):
        catalogo = {
            "plantillas": [
                {
                    "id": "x",
                    "nombre": "X",
                    "deporte": {"id": "a", "nombre": "A"},
                    "calendario": {"hora": "las tres"},
                }
            ]
        }
        with pytest.raises(CatalogoIlegible, match="HH:MM"):
            cargar_catalogo(self.escribir(tmp_path, catalogo))


class TestPlantillasPropias:
    """Una plantilla de usuario usa exactamente el mismo mecanismo que ITC."""

    def test_una_plantilla_minima_se_carga(self, tmp_path):
        ruta = tmp_path / "mia.json"
        ruta.write_text(
            json.dumps(
                {
                    "plantillas": [
                        {
                            "id": "ajedrez",
                            "nombre": "Torneo de ajedrez",
                            "deporte": {"id": "ajedrez", "nombre": "Ajedrez"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (plantilla,) = cargar_catalogo(ruta)
        assert plantilla.nombre == "Torneo de ajedrez"
        assert not plantilla.es_semilla
        assert plantilla.instanciar("c1").fases == ()

    def test_puede_traer_sus_propias_divisiones(self, tmp_path):
        ruta = tmp_path / "mia.json"
        ruta.write_text(
            json.dumps(
                {
                    "divisiones": [{"id": "COMUN", "nombre": "Común"}],
                    "plantillas": [
                        {
                            "id": "x",
                            "nombre": "X",
                            "deporte": {"id": "a", "nombre": "A"},
                            "divisiones": [{"id": "PESO", "nombre": "Peso pluma"}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (plantilla,) = cargar_catalogo(ruta)
        assert [d.id for d in plantilla.divisiones] == ["PESO"]


class TestFormatoTrasladadoALaCompeticion:
    """Lo que la plantilla configura debe sobrevivir a `instanciar`."""

    def test_la_fase_de_grupos_conserva_las_siete_jornadas(self, microfutbol):
        grupos = microfutbol.instanciar("c1").fases_ordenadas[0]
        assert grupos.config_fixture.jornadas_forzadas == 7
        assert grupos.fixture == "round_robin"

    def test_la_eliminatoria_conserva_su_generador(self, microfutbol):
        copa = microfutbol.instanciar("c1").fases_ordenadas[1]
        assert copa.fixture == "eliminacion_directa"
        assert copa.cupos == 16

    def test_la_competicion_hereda_el_calendario_de_sabados(self, microfutbol):
        calendario = microfutbol.instanciar("c1").calendario
        assert calendario.dia_de_la_semana == 5
        assert calendario.hora == dt.time(15, 0)
