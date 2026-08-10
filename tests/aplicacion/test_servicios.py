"""Los casos de uso, contra repositorios en memoria. Ni una llamada de red."""

from __future__ import annotations

import datetime as dt
import random

import pytest

from itc_deporte.aplicacion.errores import NoEncontrado, OperacionInvalida
from itc_deporte.aplicacion.permisos import (
    ANONIMO,
    Accion,
    Concesion,
    Identidad,
    PermisoDenegado,
    Politica,
    Rol,
)
from itc_deporte.aplicacion.servicios import (
    ServicioDeClasificacion,
    ServicioDeCompeticiones,
    ServicioDeCuadroFinal,
    ServicioDeInscripciones,
    ServicioDeRegistradores,
    ServicioDeResultados,
    ServicioDeSorteo,
)
from itc_deporte.infraestructura.autenticacion import (
    AutenticadorEnMemoria,
    ConcesionesEnMemoria,
)
from itc_deporte.domain.calendario import Calendario
from itc_deporte.domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    FaseDeGrupos,
    FaseEliminatoria,
    Grupo,
    ReglasDeCompeticion,
)
from itc_deporte.domain.enfrentamiento import Enfrentamiento, Marcador
from itc_deporte.domain.errores import ReglaInvalida
from itc_deporte.domain.reglas.fixture import ConfigFixture
from itc_deporte.domain.reglas.puntuacion import PorSets
from itc_deporte.infraestructura.memoria import (
    CompeticionesEnMemoria,
    EnfrentamientosEnMemoria,
    ParticipantesEnMemoria,
)

MICROFUTBOL = Deporte("microfutbol", "Microfútbol", "⚽")
VOLEIBOL = Deporte("voleyball", "Voleyball", "🏐")

LUNES = dt.date(2026, 7, 20)

ADMIN = Identidad("admin", "admin@itc.edu.co")
REGISTRADOR = Identidad("registrador", "profe@itc.edu.co")
CURIOSO = Identidad("curioso", "alguien@itc.edu.co")


@pytest.fixture
def repos():
    return {
        "competiciones": CompeticionesEnMemoria(),
        "participantes": ParticipantesEnMemoria(),
        "enfrentamientos": EnfrentamientosEnMemoria(),
        "concesiones": ConcesionesEnMemoria(
            [
                Concesion("admin", Rol.ADMIN),
                Concesion("registrador", Rol.REGISTRADOR, "c1"),
            ]
        ),
        "autenticador": AutenticadorEnMemoria([ADMIN, REGISTRADOR, CURIOSO]),
    }


@pytest.fixture
def politica(repos):
    return Politica(repos["concesiones"])


@pytest.fixture
def servicios(repos, politica):
    clasificacion = ServicioDeClasificacion(
        repos["competiciones"], repos["participantes"], repos["enfrentamientos"]
    )
    return {
        "competiciones": ServicioDeCompeticiones(
            repos["competiciones"], repos["concesiones"], politica
        ),
        "inscripciones": ServicioDeInscripciones(
            repos["competiciones"], repos["participantes"], politica
        ),
        "sorteo": ServicioDeSorteo(
            repos["competiciones"],
            repos["participantes"],
            repos["enfrentamientos"],
            politica,
            azar=random.Random(42),
        ),
        "resultados": ServicioDeResultados(
            repos["enfrentamientos"], repos["competiciones"], politica
        ),
        "clasificacion": clasificacion,
        "cuadro": ServicioDeCuadroFinal(
            repos["competiciones"], repos["enfrentamientos"], clasificacion, politica
        ),
        "registradores": ServicioDeRegistradores(
            repos["competiciones"],
            repos["concesiones"],
            repos["autenticador"],
            politica,
        ),
    }


def competicion_de_prueba(id_="c1", nombre="Prueba", deporte=MICROFUTBOL, puntuacion=None):
    """Arma una competición a mano, que es como se crean ahora.

    Reproduce la configuración con la que opera el ITC —siete jornadas, sábados
    a las 15:00, cuadro a 16— sin que eso sea una plantilla precargada.
    """
    reglas = ReglasDeCompeticion(puntuacion=puntuacion) if puntuacion else ReglasDeCompeticion()
    return Competicion(
        id=id_,
        nombre=nombre,
        deporte=deporte,
        fases=(
            FaseDeGrupos(
                f"{id_}:0", "Fase de grupos", 0,
                config_fixture=ConfigFixture(jornadas_forzadas=7),
            ),
            FaseEliminatoria(
                f"{id_}:1", "Eliminación directa", 1,
                fixture="eliminacion_directa", cupos=16,
            ),
        ),
        reglas=reglas,
        calendario=Calendario(dia_de_la_semana=5, hora=dt.time(15, 0)),
    )


def crear_liga(servicios, deporte=None, inscritos=4):
    servicios["competiciones"].crear(
        ADMIN, competicion_de_prueba(deporte=deporte or MICROFUTBOL)
    )
    for i in range(1, inscritos + 1):
        servicios["inscripciones"].inscribir(ADMIN, "c1", f"p{i}", f"Equipo {i}")
    return "c1:0", "c1:1"


class TestCompeticiones:
    def test_crear(self, servicios):
        competicion = servicios["competiciones"].crear(
            ADMIN, competicion_de_prueba(nombre="Intercursos 2026")
        )
        assert competicion.nombre == "Intercursos 2026"
        assert len(competicion.fases) == 2

    def test_la_competicion_queda_guardada(self, servicios):
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba())
        assert servicios["competiciones"].obtener("c1") is not None

    def test_rechaza_un_id_ya_usado(self, servicios):
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba())
        with pytest.raises(OperacionInvalida, match="Ya existe"):
            servicios["competiciones"].crear(ADMIN, competicion_de_prueba())

    def test_obtener_lo_que_no_existe_falla(self, servicios):
        with pytest.raises(NoEncontrado):
            servicios["competiciones"].obtener("fantasma")

    def test_cambiar_estado(self, servicios):
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba())
        competicion = servicios["competiciones"].cambiar_estado(
            ADMIN, "c1", EstadoCompeticion.EN_CURSO
        )
        assert competicion.estado is EstadoCompeticion.EN_CURSO

    def test_el_deporte_y_la_puntuacion_salen_del_catalogo(self, servicios):
        """Siguen siendo dato configurable sin necesidad de plantillas."""
        voley = competicion_de_prueba(deporte=VOLEIBOL, puntuacion=PorSets())
        creada = servicios["competiciones"].crear(ADMIN, voley)
        assert creada.deporte.nombre == "Voleyball"
        assert creada.reglas.puntuacion.puntos(Marcador(3, 2)) == (2, 1)


class TestUnRegistradorCreaLaSuya:
    """Su concesión es por competición, así que la que acaba de crear no estaba
    en ninguna: sin quedarse con ella, podía dar de alta una competición y no
    poder inscribir a nadie en ella."""

    def test_puede_crearla(self, servicios):
        creada = servicios["competiciones"].crear(
            REGISTRADOR, competicion_de_prueba("c9", "La del profe")
        )
        assert creada.id == "c9"

    def test_y_queda_como_registrador_de_ella(self, servicios, repos):
        servicios["competiciones"].crear(
            REGISTRADOR, competicion_de_prueba("c9", "La del profe")
        )
        concesiones = repos["concesiones"].de_competicion("c9")
        assert [(c.usuario_id, c.rol) for c in concesiones] == [
            ("registrador", Rol.REGISTRADOR)
        ]

    def test_asi_que_puede_inscribir_en_ella(self, servicios):
        servicios["competiciones"].crear(
            REGISTRADOR, competicion_de_prueba("c9", "La del profe")
        )
        inscrito = servicios["inscripciones"].inscribir(
            REGISTRADOR, "c9", "p1", "Los Tigres"
        )
        assert inscrito.competicion_id == "c9"

    def test_pero_no_sortearla(self, servicios):
        """Crear no arrastra administrar: eso sigue siendo del admin."""
        servicios["competiciones"].crear(
            REGISTRADOR, competicion_de_prueba("c9", "La del profe")
        )
        for i in range(1, 5):
            servicios["inscripciones"].inscribir(REGISTRADOR, "c9", f"p{i}", f"E{i}")
        with pytest.raises(PermisoDenegado):
            servicios["sorteo"].sortear(REGISTRADOR, "c9", "c9:0", desde=LUNES)

    def test_ni_cambiarle_el_estado(self, servicios):
        servicios["competiciones"].crear(
            REGISTRADOR, competicion_de_prueba("c9", "La del profe")
        )
        with pytest.raises(PermisoDenegado):
            servicios["competiciones"].cambiar_estado(
                REGISTRADOR, "c9", EstadoCompeticion.EN_CURSO
            )

    def test_al_admin_no_se_le_otorga_nada(self, servicios, repos):
        """Su rol ya es global, y una concesión de admin con competición está
        prohibida por el propio tipo."""
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba("c9"))
        assert repos["concesiones"].de_competicion("c9") == ()

    def test_quien_no_es_registrador_de_nada_no_puede_crear(self, servicios):
        with pytest.raises(PermisoDenegado, match="crear_competicion"):
            servicios["competiciones"].crear(CURIOSO, competicion_de_prueba())

    def test_ni_un_visitante_sin_identificar(self, servicios):
        with pytest.raises(PermisoDenegado):
            servicios["competiciones"].crear(ANONIMO, competicion_de_prueba())

    def test_si_falla_el_alta_no_deja_concesion_suelta(self, servicios, repos):
        """Un id repetido corta antes de guardar; la concesión no debe quedar."""
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba("c9"))
        with pytest.raises(OperacionInvalida):
            servicios["competiciones"].crear(REGISTRADOR, competicion_de_prueba("c9"))
        assert repos["concesiones"].de_competicion("c9") == ()


class TestInscripciones:
    def test_inscribir(self, servicios):
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba())
        participante = servicios["inscripciones"].inscribir(ADMIN, "c1", "p1", "Los Tigres")
        assert participante.competicion_id == "c1"

    def test_los_inscritos_se_listan(self, servicios):
        crear_liga(servicios, inscritos=3)
        assert len(servicios["inscripciones"].inscritos("c1")) == 3

    def test_rechaza_una_competicion_inexistente(self, servicios):
        with pytest.raises(NoEncontrado, match="competición"):
            servicios["inscripciones"].inscribir(ADMIN, "fantasma", "p1", "X")

    def test_rechaza_un_nombre_repetido_en_la_misma_competicion(self, servicios):
        crear_liga(servicios, inscritos=1)
        with pytest.raises(OperacionInvalida, match="Ya hay un participante"):
            servicios["inscripciones"].inscribir(ADMIN, "c1", "p9", "Equipo 1")

    def test_el_mismo_nombre_en_otra_competicion_si_vale(self, servicios):
        crear_liga(servicios, inscritos=1)
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba("c2", "Otra"))
        assert servicios["inscripciones"].inscribir(ADMIN, "c2", "p9", "Equipo 1")

    def test_normaliza_los_espacios_del_nombre(self, servicios):
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba())
        inscrito = servicios["inscripciones"].inscribir(ADMIN, "c1", "p1", "  Los Tigres  ")
        assert inscrito.nombre == "Los Tigres"

    def test_rechaza_un_id_ya_usado(self, servicios):
        crear_liga(servicios, inscritos=1)
        with pytest.raises(OperacionInvalida, match="Ya existe el participante"):
            servicios["inscripciones"].inscribir(ADMIN, "c1", "p1", "Otro nombre")

    def test_no_se_inscribe_en_una_competicion_terminada(self, servicios):
        crear_liga(servicios, inscritos=1)
        servicios["competiciones"].cambiar_estado(ADMIN, "c1", EstadoCompeticion.FINALIZADA)
        with pytest.raises(OperacionInvalida, match="ya terminó"):
            servicios["inscripciones"].inscribir(ADMIN, "c1", "p9", "Tarde")

    def test_retirar(self, servicios):
        crear_liga(servicios, inscritos=2)
        servicios["inscripciones"].retirar(ADMIN, "p1")
        assert len(servicios["inscripciones"].inscritos("c1")) == 1

    def test_retirar_a_quien_no_esta_falla(self, servicios):
        with pytest.raises(NoEncontrado):
            servicios["inscripciones"].retirar(ADMIN, "fantasma")


class TestSorteo:
    def test_genera_el_calendario_de_la_fase(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        assert len(partidos) > 0
        assert all(p.fase_id == grupos for p in partidos)

    def test_respeta_las_siete_jornadas_configuradas(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        assert {p.jornada for p in partidos} == set(range(1, 8))

    def test_los_partidos_caen_en_sabado_a_las_tres(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        assert all(p.fecha.weekday() == 5 for p in partidos)
        assert all(p.fecha.hour == 15 for p in partidos)

    def test_las_jornadas_van_semana_a_semana(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        fechas = sorted({p.fecha for p in partidos})
        assert (fechas[1] - fechas[0]).days == 7

    def test_el_calendario_queda_guardado(self, servicios, repos):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        assert len(repos["enfrentamientos"].de_fase(grupos)) == len(partidos)

    def test_con_la_misma_semilla_el_sorteo_es_reproducible(self, repos):
        """El azar se inyecta, así que un sorteo se puede repetir en un test."""
        def sortear(semilla):
            comp = CompeticionesEnMemoria()
            parts = ParticipantesEnMemoria()
            enfs = EnfrentamientosEnMemoria()
            pol = Politica(ConcesionesEnMemoria([Concesion("admin", Rol.ADMIN)]))
            servicio_comp = ServicioDeCompeticiones(
                comp, ConcesionesEnMemoria(), pol
            )
            servicio_comp.crear(ADMIN, competicion_de_prueba())
            inscripciones = ServicioDeInscripciones(comp, parts, pol)
            for i in range(1, 5):
                inscripciones.inscribir(ADMIN, "c1", f"p{i}", f"Equipo {i}")
            sorteo = ServicioDeSorteo(
                comp, parts, enfs, pol, azar=random.Random(semilla)
            )
            return [
                (p.local, p.visitante)
                for p in sorteo.sortear(ADMIN, "c1", "c1:0", LUNES)
            ]

        assert sortear(1) == sortear(1)
        assert sortear(1) != sortear(999)

    def test_resortear_descarta_el_calendario_anterior(self, servicios, repos):
        grupos, _ = crear_liga(servicios, inscritos=4)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        primeros = len(repos["enfrentamientos"].de_fase(grupos))
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        assert len(repos["enfrentamientos"].de_fase(grupos)) == primeros

    def test_rechaza_sortear_con_menos_de_dos(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=1)
        with pytest.raises(OperacionInvalida, match="al menos 2"):
            servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)

    def test_rechaza_una_fase_inexistente(self, servicios):
        crear_liga(servicios)
        with pytest.raises(NoEncontrado, match="fase"):
            servicios["sorteo"].sortear(ADMIN, "c1", "fantasma", desde=LUNES)

    def test_rechaza_sortear_una_eliminatoria(self, servicios):
        _, copa = crear_liga(servicios)
        with pytest.raises(OperacionInvalida, match="no es de grupos"):
            servicios["sorteo"].sortear(ADMIN, "c1", copa, desde=LUNES)

    def test_con_impares_descansa_uno_por_jornada(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=5)
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        por_jornada = {}
        for partido in partidos:
            por_jornada.setdefault(partido.jornada, []).append(partido)
        assert all(len(p) == 2 for p in por_jornada.values())  # 5 -> 2 cruces


class TestResultados:
    def test_registrar_cierra_el_partido(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partido = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)[0]
        cerrado = servicios["resultados"].registrar(ADMIN, partido.id, Marcador(2, 1))
        assert cerrado.esta_finalizado and cerrado.ganador() == partido.local

    def test_queda_guardado(self, servicios, repos):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partido = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)[0]
        servicios["resultados"].registrar(ADMIN, partido.id, Marcador(2, 1))
        assert repos["enfrentamientos"].obtener(partido.id).esta_finalizado

    def test_volver_a_registrar_corrige(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partido = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)[0]
        servicios["resultados"].registrar(ADMIN, partido.id, Marcador(2, 1))
        corregido = servicios["resultados"].registrar(ADMIN, partido.id, Marcador(0, 3))
        assert corregido.ganador() == partido.visitante

    def test_rechaza_un_partido_inexistente(self, servicios):
        with pytest.raises(NoEncontrado):
            servicios["resultados"].registrar(ADMIN, "fantasma", Marcador(1, 0))


class TestElMarcadorTieneQueCaberEnLasReglas:
    """El fallo: registrar no consultaba las reglas de la competición.

    Un 2-2 en una competición por sets entraba sin queja, y la excepción
    saltaba después y en otro sitio —al calcular la tabla, cada vez que alguien
    abría la pestaña—. Con el dato ya guardado, la página quedaba rota de forma
    permanente y sin manera de corregirla desde la aplicación.
    """

    def _partido_de_voley(self, servicios):
        servicios["competiciones"].crear(
            ADMIN, competicion_de_prueba(deporte=VOLEIBOL, puntuacion=PorSets())
        )
        for i in range(1, 5):
            servicios["inscripciones"].inscribir(ADMIN, "c1", f"p{i}", f"Equipo {i}")
        return servicios["sorteo"].sortear(ADMIN, "c1", "c1:0", desde=LUNES)[0]

    def test_un_empate_por_sets_se_rechaza_al_registrar(self, servicios):
        partido = self._partido_de_voley(servicios)
        with pytest.raises(ReglaInvalida, match="no puede quedar empatado"):
            servicios["resultados"].registrar(ADMIN, partido.id, Marcador(2, 2))

    def test_y_no_llega_a_guardarse(self, servicios, repos):
        partido = self._partido_de_voley(servicios)
        with pytest.raises(ReglaInvalida):
            servicios["resultados"].registrar(ADMIN, partido.id, Marcador(2, 2))
        assert not repos["enfrentamientos"].obtener(partido.id).esta_finalizado

    def test_asi_la_tabla_se_sigue_pudiendo_calcular(self, servicios):
        """Lo que de verdad se protege: que la pestaña no quede inservible."""
        partido = self._partido_de_voley(servicios)
        with pytest.raises(ReglaInvalida):
            servicios["resultados"].registrar(ADMIN, partido.id, Marcador(2, 2))
        assert servicios["clasificacion"].de_fase("c1", "c1:0")

    def test_un_resultado_valido_sigue_entrando(self, servicios):
        partido = self._partido_de_voley(servicios)
        cerrado = servicios["resultados"].registrar(ADMIN, partido.id, Marcador(3, 2))
        assert cerrado.esta_finalizado

    def test_en_una_liga_normal_el_empate_es_legitimo(self, servicios):
        """La comprobación es de la regla, no una prohibición general."""
        grupos, _ = crear_liga(servicios, inscritos=4)
        partido = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)[0]
        assert servicios["resultados"].registrar(
            ADMIN, partido.id, Marcador(1, 1)
        ).esta_finalizado

    def test_el_cuadro_final_lo_comprueba_igual(self, servicios):
        """Comparte tabla y reglas con la fase de grupos, así que un marcador
        imposible ahí envenena la misma consulta."""
        self._partido_de_voley(servicios)
        for indice, otro in enumerate(servicios["resultados"].de_fase("c1:0")):
            servicios["resultados"].registrar(ADMIN, otro.id, Marcador(3, indice % 3))
        servicios["cuadro"].generar(ADMIN, "c1", "c1:1", desde_fase="c1:0")
        with pytest.raises(ReglaInvalida, match="no puede quedar empatado"):
            servicios["cuadro"].registrar(ADMIN, "c1", "c1:1", 0, 0, Marcador(1, 1))


class TestClasificacion:
    def test_todos_los_inscritos_aparecen(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        tabla = servicios["clasificacion"].de_fase("c1", grupos)
        assert len(tabla) == 4

    def test_refleja_los_resultados(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partido = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)[0]
        servicios["resultados"].registrar(ADMIN, partido.id, Marcador(3, 0))
        tabla = {f.participante_id: f for f in servicios["clasificacion"].de_fase("c1", grupos)}
        assert tabla[partido.local].puntos == 3
        assert tabla[partido.visitante].puntos == 0

    def test_usa_la_puntuacion_de_la_competicion(self, servicios):
        """En voleibol un 3-2 reparte 2-1, no 3-0."""
        servicios["competiciones"].crear(
            ADMIN, competicion_de_prueba(deporte=VOLEIBOL, puntuacion=PorSets())
        )
        for i in range(1, 5):
            servicios["inscripciones"].inscribir(ADMIN, "c1", f"p{i}", f"Equipo {i}")
        partido = servicios["sorteo"].sortear(ADMIN, "c1", "c1:0", desde=LUNES)[0]
        servicios["resultados"].registrar(ADMIN, partido.id, Marcador(3, 2))
        tabla = {f.participante_id: f for f in servicios["clasificacion"].de_fase("c1", "c1:0")}
        assert (tabla[partido.local].puntos, tabla[partido.visitante].puntos) == (2, 1)

    def test_rechaza_una_competicion_inexistente(self, servicios):
        with pytest.raises(NoEncontrado):
            servicios["clasificacion"].de_fase("fantasma", "f1")

    def test_rechaza_una_fase_inexistente(self, servicios):
        crear_liga(servicios)
        with pytest.raises(NoEncontrado, match="fase"):
            servicios["clasificacion"].de_fase("c1", "fantasma")


class TestCuadroFinal:
    def test_genera_el_cuadro_con_los_mejores(self, servicios):
        grupos, copa = crear_liga(servicios, inscritos=4)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        bracket = servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        assert bracket.total_rondas == 2

    def test_el_cuadro_queda_guardado_como_enfrentamientos(self, servicios, repos):
        grupos, copa = crear_liga(servicios, inscritos=4)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        guardados = repos["enfrentamientos"].de_fase(copa)
        assert len(guardados) == 3  # 2 semifinales + final
        assert all(p.ronda is not None for p in guardados)

    def test_se_recupera_lo_guardado(self, servicios):
        grupos, copa = crear_liga(servicios, inscritos=4)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        assert servicios["cuadro"].actual("c1", copa).total_rondas == 2

    def test_registrar_propaga_al_ganador(self, servicios):
        grupos, copa = crear_liga(servicios, inscritos=4)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        bracket = servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        primero = bracket.slot(0, 0).local
        actualizado = servicios["cuadro"].registrar(ADMIN, "c1", copa, 0, 0, Marcador(1, 0))
        assert actualizado.slot(1, 0).local == primero

    def test_la_propagacion_persiste(self, servicios):
        grupos, copa = crear_liga(servicios, inscritos=4)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        bracket = servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        esperado = bracket.slot(0, 0).local
        servicios["cuadro"].registrar(ADMIN, "c1", copa, 0, 0, Marcador(1, 0))
        assert servicios["cuadro"].actual("c1", copa).slot(1, 0).local == esperado

    def test_sin_cuadro_generado_falla(self, servicios):
        _, copa = crear_liga(servicios)
        with pytest.raises(NoEncontrado, match="todavía no tiene cuadro"):
            servicios["cuadro"].actual("c1", copa)

    def test_rechaza_una_fase_que_no_es_eliminatoria(self, servicios):
        grupos, _ = crear_liga(servicios)
        with pytest.raises(OperacionInvalida, match="no es una eliminatoria"):
            servicios["cuadro"].actual("c1", grupos)

    def test_rechaza_generar_sin_clasificados_suficientes(self, servicios):
        grupos, copa = crear_liga(servicios, inscritos=1)
        with pytest.raises(OperacionInvalida, match="al menos 2"):
            servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)


class TestDePuntaAPunta:
    """Una competición entera: del sorteo al campeón, sin tocar la red."""

    def test_del_sorteo_al_campeon(self, servicios):
        grupos, copa = crear_liga(servicios, inscritos=4)

        # Liga: se juega todo con victoria local
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        for partido in partidos:
            servicios["resultados"].registrar(ADMIN, partido.id, Marcador(1, 0))

        tabla = servicios["clasificacion"].de_fase("c1", grupos)
        assert len(tabla) == 4
        assert sum(f.jugados for f in tabla) == len(partidos) * 2

        # Cuadro final con los cuatro clasificados
        bracket = servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        assert bracket.campeon() is None

        for ronda in range(bracket.total_rondas):
            for casilla in servicios["cuadro"].actual("c1", copa).rondas[ronda]:
                if casilla.listo and casilla.ganador() is None:
                    servicios["cuadro"].registrar(
                        ADMIN, "c1", copa, ronda, casilla.posicion, Marcador(1, 0)
                    )

        final = servicios["cuadro"].actual("c1", copa)
        assert final.campeon() is not None
        assert final.pendientes() == ()

    def test_el_campeon_es_el_mejor_sembrado_si_siempre_gana_el_local(self, servicios):
        grupos, copa = crear_liga(servicios, inscritos=4)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        bracket = servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        mejor = bracket.slot(0, 0).local

        for ronda in range(bracket.total_rondas):
            for casilla in servicios["cuadro"].actual("c1", copa).rondas[ronda]:
                if casilla.listo and casilla.ganador() is None:
                    servicios["cuadro"].registrar(
                        ADMIN, "c1", copa, ronda, casilla.posicion, Marcador(1, 0)
                    )

        assert servicios["cuadro"].actual("c1", copa).campeon() == mejor


class TestClasificacionPorGrupo:
    """Tabla de un grupo: solo sus inscritos, solo sus partidos."""

    @pytest.fixture
    def con_grupos(self, servicios, repos):
        from dataclasses import replace

        
        grupos_id, _ = crear_liga(servicios, inscritos=4)
        competicion = servicios["competiciones"].obtener("c1")
        fase = competicion.fase(grupos_id)
        con_reparto = replace(
            fase,
            grupos=(
                Grupo("A", "Grupo A", ("p1", "p2")),
                Grupo("B", "Grupo B", ("p3", "p4")),
            ),
        )
        repos["competiciones"].guardar(
            replace(
                competicion,
                fases=tuple(
                    con_reparto if f.id == grupos_id else f for f in competicion.fases
                ),
            )
        )
        return grupos_id

    def test_solo_salen_los_del_grupo(self, servicios, con_grupos):
        tabla = servicios["clasificacion"].de_grupo("c1", con_grupos, "A")
        assert {f.participante_id for f in tabla} == {"p1", "p2"}

    def test_refleja_los_resultados_del_grupo(self, servicios, repos, con_grupos):
        
        repos["enfrentamientos"].guardar(
            Enfrentamiento("x1", "p1", "p2", fase_id=con_grupos).finalizar(
                Marcador(2, 0)
            )
        )
        tabla = {f.participante_id: f for f in servicios["clasificacion"].de_grupo("c1", con_grupos, "A")}
        assert tabla["p1"].puntos == 3

    def test_rechaza_un_grupo_inexistente(self, servicios, con_grupos):
        with pytest.raises(NoEncontrado, match="grupo"):
            servicios["clasificacion"].de_grupo("c1", con_grupos, "Z")

    def test_rechaza_una_competicion_inexistente(self, servicios):
        with pytest.raises(NoEncontrado, match="competición"):
            servicios["clasificacion"].de_grupo("fantasma", "f1", "A")

    def test_una_eliminatoria_no_tiene_grupos(self, servicios):
        _, copa = crear_liga(servicios)
        with pytest.raises(NoEncontrado, match="no es de grupos"):
            servicios["clasificacion"].de_grupo("c1", copa, "A")


class TestConsultasSueltas:
    def test_listar_competiciones(self, servicios):
        assert servicios["competiciones"].listar() == ()
        crear_liga(servicios)
        assert len(servicios["competiciones"].listar()) == 1

    def test_resultados_de_una_fase(self, servicios):
        grupos, _ = crear_liga(servicios, inscritos=4)
        partidos = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        assert len(servicios["resultados"].de_fase(grupos)) == len(partidos)

    def test_sortear_una_competicion_inexistente_falla(self, servicios):
        with pytest.raises(NoEncontrado, match="competición"):
            servicios["sorteo"].sortear(ADMIN, "fantasma", "f1", desde=LUNES)

    def test_el_cuadro_de_una_competicion_inexistente_falla(self, servicios):
        with pytest.raises(NoEncontrado, match="competición"):
            servicios["cuadro"].actual("fantasma", "f1")
