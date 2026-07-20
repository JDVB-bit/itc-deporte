from __future__ import annotations

import datetime as dt

import pytest

from itc_deporte.domain.competicion import (
    Deporte,
    EstadoCompeticion,
    FaseDeGrupos,
    FaseEliminatoria,
)
from itc_deporte.domain.division import Division
from itc_deporte.domain.enfrentamiento import Marcador
from itc_deporte.domain.errores import ErrorDeDominio, ReglaInvalida
from itc_deporte.domain.calendario import Calendario
from itc_deporte.domain.plantilla import (
    EspecificacionDeFase,
    EspecificacionDeRegla,
    PlantillaDeCompeticion,
    TipoDeFase,
)
from itc_deporte.domain.reglas.fixture import (
    ConfigFixture,
    EliminacionDirecta,
    RoundRobin,
)

FUTBOL = Deporte("microfutbol", "Microfútbol", "⚽")


def plantilla(**cambios) -> PlantillaDeCompeticion:
    base = dict(id="basica", nombre="Liga simple", deporte=FUTBOL)
    return PlantillaDeCompeticion(**{**base, **cambios})


class TestEspecificacionDeRegla:
    def test_los_parametros_son_opcionales(self):
        assert dict(EspecificacionDeRegla("por_sets").parametros) == {}

    def test_los_parametros_quedan_inmutables(self):
        spec = EspecificacionDeRegla("por_sets", {"umbral_ajustado": 1})
        with pytest.raises(TypeError):
            spec.parametros["umbral_ajustado"] = 9

    def test_no_comparte_estado_con_el_dict_original(self):
        origen = {"victoria": 3}
        spec = EspecificacionDeRegla("victoria_derrota", origen)
        origen["victoria"] = 99
        assert spec.parametros["victoria"] == 3

    def test_rechaza_tipo_vacio(self):
        with pytest.raises(ErrorDeDominio):
            EspecificacionDeRegla("")


class TestEspecificacionDeFase:
    def test_una_fase_de_grupos_se_instancia_como_tal(self):
        spec = EspecificacionDeFase(TipoDeFase.GRUPOS, "Fase de grupos", 0)
        fase = spec.instanciar("f1")
        assert isinstance(fase, FaseDeGrupos)
        assert fase.grupos == ()

    def test_una_eliminatoria_conserva_sus_cupos(self):
        spec = EspecificacionDeFase(TipoDeFase.ELIMINATORIA, "Copa", 1, cupos=8)
        fase = spec.instanciar("f2")
        assert isinstance(fase, FaseEliminatoria)
        assert fase.cupos == 8

    def test_resuelve_su_generador_de_fixture(self):
        grupos = EspecificacionDeFase(TipoDeFase.GRUPOS, "Liga", 0)
        copa = EspecificacionDeFase(
            TipoDeFase.ELIMINATORIA, "Copa", 1, fixture="eliminacion_directa"
        )
        assert isinstance(grupos.generador(), RoundRobin)
        assert isinstance(copa.generador(), EliminacionDirecta)

    def test_rechaza_un_generador_inexistente(self):
        spec = EspecificacionDeFase(TipoDeFase.GRUPOS, "Liga", 0, fixture="suizo")
        with pytest.raises(ReglaInvalida, match="round_robin"):
            spec.generador()

    def test_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            EspecificacionDeFase(TipoDeFase.GRUPOS, "  ", 0)

    def test_rechaza_orden_negativo(self):
        with pytest.raises(ErrorDeDominio):
            EspecificacionDeFase(TipoDeFase.GRUPOS, "Liga", -1)


class TestCalendario:
    def test_sin_dia_fijo_arranca_en_la_fecha_dada(self):
        cal = Calendario(hora=dt.time(9, 0))
        fechas = cal.fechas(dt.date(2026, 7, 20), 2)
        assert fechas[0] == dt.datetime(2026, 7, 20, 9, 0)

    def test_busca_el_siguiente_dia_de_la_semana(self):
        """20/07/2026 es lunes; el sábado siguiente es el 25."""
        cal = Calendario(dia_de_la_semana=5)
        assert cal.fechas(dt.date(2026, 7, 20), 1)[0].date() == dt.date(2026, 7, 25)

    def test_estando_en_el_dia_fijado_programa_para_el_siguiente(self):
        """Es lo que hacía el sorteo actual con su `or 7`."""
        cal = Calendario(dia_de_la_semana=5)
        sabado = dt.date(2026, 7, 25)
        assert cal.fechas(sabado, 1)[0].date() == dt.date(2026, 8, 1)

    def test_reproduce_el_calendario_del_itc(self):
        """Sábados a las 15:00, semanal."""
        cal = Calendario(dia_de_la_semana=5, hora=dt.time(15, 0))
        fechas = cal.fechas(dt.date(2026, 7, 20), 3)
        assert fechas == (
            dt.datetime(2026, 7, 25, 15, 0),
            dt.datetime(2026, 8, 1, 15, 0),
            dt.datetime(2026, 8, 8, 15, 0),
        )

    def test_la_cadencia_es_configurable(self):
        cal = Calendario(cadencia_dias=3)
        fechas = cal.fechas(dt.date(2026, 7, 20), 2)
        assert (fechas[1] - fechas[0]).days == 3

    def test_cero_fechas_es_vacio(self):
        assert Calendario().fechas(dt.date(2026, 7, 20), 0) == ()

    def test_rechaza_un_dia_de_la_semana_fuera_de_rango(self):
        with pytest.raises(ErrorDeDominio):
            Calendario(dia_de_la_semana=7)

    def test_rechaza_cadencia_de_cero_dias(self):
        with pytest.raises(ErrorDeDominio):
            Calendario(cadencia_dias=0)

    def test_rechaza_una_cantidad_negativa(self):
        with pytest.raises(ErrorDeDominio):
            Calendario().fechas(dt.date(2026, 7, 20), -1)


class TestPlantilla:
    def test_rechaza_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            plantilla(id="")

    def test_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            plantilla(nombre="   ")

    def test_rechaza_quedarse_sin_desempate(self):
        with pytest.raises(ErrorDeDominio):
            plantilla(desempate=())

    def test_rechaza_dos_fases_con_el_mismo_orden(self):
        fases = (
            EspecificacionDeFase(TipoDeFase.GRUPOS, "A", 0),
            EspecificacionDeFase(TipoDeFase.ELIMINATORIA, "B", 0),
        )
        with pytest.raises(ErrorDeDominio):
            plantilla(fases=fases)

    def test_construye_su_catalogo_de_divisiones(self):
        divisiones = (
            Division("PRIMERA", "Primera"),
            Division("601", "601", padre_id="PRIMERA"),
        )
        catalogo = plantilla(divisiones=divisiones).catalogo_de_divisiones()
        assert [d.id for d in catalogo.hojas()] == ["601"]

    def test_una_jerarquia_incoherente_falla_al_construir_el_catalogo(self):
        mala = plantilla(divisiones=(Division("601", "601", padre_id="NO_EXISTE"),))
        with pytest.raises(ErrorDeDominio):
            mala.catalogo_de_divisiones()


class TestReglasDeLaPlantilla:
    def test_por_defecto_son_las_del_sistema_anterior(self):
        reglas = plantilla().reglas()
        assert reglas.puntuacion.puntos(Marcador(2, 1)) == (3, 0)
        assert len(reglas.desempate) == 3

    def test_resuelve_la_puntuacion_por_sets(self):
        voley = plantilla(puntuacion=EspecificacionDeRegla("por_sets"))
        assert voley.reglas().puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_pasa_los_parametros_a_la_regla(self):
        spec = EspecificacionDeRegla("victoria_derrota", {"victoria": 2})
        assert plantilla(puntuacion=spec).reglas().puntuacion.puntos(
            Marcador(1, 0)
        ) == (2, 0)

    def test_rechaza_una_puntuacion_inexistente(self):
        mala = plantilla(puntuacion=EspecificacionDeRegla("por_karma"))
        with pytest.raises(ReglaInvalida, match="por_sets"):
            mala.reglas()

    def test_rechaza_parametros_que_la_regla_no_conoce(self):
        spec = EspecificacionDeRegla("por_sets", {"color": "azul"})
        with pytest.raises(ReglaInvalida, match="Parámetros inválidos"):
            plantilla(puntuacion=spec).reglas()

    def test_rechaza_un_desempate_inexistente(self):
        with pytest.raises(ReglaInvalida, match="enfrentamiento_directo"):
            plantilla(desempate=("por_simpatia",)).reglas()

    def test_el_enfrentamiento_directo_recibe_la_puntuacion_de_la_plantilla(self):
        voley = plantilla(
            puntuacion=EspecificacionDeRegla("por_sets"),
            desempate=("puntos", "enfrentamiento_directo"),
        )
        criterio = voley.reglas().desempate[1]
        assert criterio.puntuacion.puntos(Marcador(3, 2)) == (2, 1)


class TestInstanciar:
    @pytest.fixture
    def mixta(self) -> PlantillaDeCompeticion:
        return plantilla(
            fases=(
                EspecificacionDeFase(TipoDeFase.ELIMINATORIA, "Copa", 1, cupos=8),
                EspecificacionDeFase(TipoDeFase.GRUPOS, "Liga", 0),
            )
        )

    def test_produce_una_competicion_en_borrador(self, mixta):
        competicion = mixta.instanciar("c1")
        assert competicion.id == "c1"
        assert competicion.estado is EstadoCompeticion.BORRADOR

    def test_hereda_el_nombre_de_la_plantilla_por_defecto(self, mixta):
        assert mixta.instanciar("c1").nombre == "Liga simple"

    def test_el_nombre_se_puede_sobrescribir(self, mixta):
        """La plantilla es un punto de partida, no un candado."""
        assert mixta.instanciar("c1", nombre="Intercursos 2026").nombre == (
            "Intercursos 2026"
        )

    def test_lleva_la_temporada_que_se_le_pase(self, mixta):
        assert mixta.instanciar("c1", temporada="2026").temporada == "2026"

    def test_crea_las_fases_en_orden(self, mixta):
        fases = mixta.instanciar("c1").fases_ordenadas
        assert [f.nombre for f in fases] == ["Liga", "Copa"]

    def test_las_fases_reciben_ids_unicos(self, mixta):
        fases = mixta.instanciar("c1").fases
        assert len({f.id for f in fases}) == 2

    def test_conserva_el_tipo_de_cada_fase(self, mixta):
        liga, copa = mixta.instanciar("c1").fases_ordenadas
        assert isinstance(liga, FaseDeGrupos)
        assert isinstance(copa, FaseEliminatoria) and copa.cupos == 8

    def test_las_fases_nacen_vacias(self, mixta):
        """El sorteo aún no se ha ejecutado."""
        liga = mixta.instanciar("c1").fases_ordenadas[0]
        assert liga.grupos == ()

    def test_traslada_las_reglas(self):
        voley = plantilla(puntuacion=EspecificacionDeRegla("por_sets"))
        competicion = voley.instanciar("c1")
        assert competicion.reglas.puntuacion.puntos(Marcador(3, 2)) == (2, 1)

    def test_dos_competiciones_de_la_misma_plantilla_son_independientes(self, mixta):
        una = mixta.instanciar("c1")
        otra = mixta.instanciar("c2", nombre="Otra")
        assert una != otra
        assert una.nombre != otra.nombre

    def test_una_plantilla_sin_fases_da_una_competicion_sin_fases(self):
        assert plantilla().instanciar("c1").fases == ()

    def test_la_config_de_fixture_viaja_en_la_especificacion(self):
        """Las 7 jornadas del ITC son un dato de la plantilla."""
        spec = EspecificacionDeFase(
            TipoDeFase.GRUPOS, "Liga", 0, config_fixture=ConfigFixture(jornadas_forzadas=7)
        )
        assert spec.config_fixture.jornadas_forzadas == 7
