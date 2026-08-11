"""El entregable de la Fase 6.

Los casos de uso se invocan aquí **directamente**, sin interfaz de por medio, y
aun así fallan cuando el actor no tiene permiso. En el sistema anterior el rol
solo escondía botones (`app.py:350`, `app.py:414`): este mismo código habría
funcionado sin obstáculo.
"""

from __future__ import annotations

import datetime as dt
import random

import pytest

from itc_deporte.aplicacion.errores import NoEncontrado
from itc_deporte.aplicacion.permisos import (
    ANONIMO,
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
    ReglasDeCompeticion,
)
from itc_deporte.domain.enfrentamiento import Enfrentamiento, Marcador
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
def servicios(repos):
    politica = Politica(repos["concesiones"])
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


class TestCrearCompeticiones:
    def test_un_visitante_no_puede(self, servicios):
        with pytest.raises(PermisoDenegado, match="crear_competicion"):
            servicios["competiciones"].crear(CURIOSO, competicion_de_prueba("c9", "Nueva"))

    def test_un_anonimo_tampoco(self, servicios):
        with pytest.raises(PermisoDenegado):
            servicios["competiciones"].crear(ANONIMO, competicion_de_prueba("c9", "Nueva"))

    def test_un_registrador_si_puede_crear_la_suya(self, servicios):
        """Cambió a propósito: su concesión es por competición, así que crear
        una no ocurre dentro de ninguna y no podía autorizarse por ámbito.
        Quien la crea queda como registrador de ella; administrarla, no."""
        creada = servicios["competiciones"].crear(
            REGISTRADOR, competicion_de_prueba("c9", "Nueva")
        )
        assert creada.id == "c9"

    def test_pero_sigue_sin_poder_administrarla(self, servicios):
        servicios["competiciones"].crear(REGISTRADOR, competicion_de_prueba("c9", "Nueva"))
        with pytest.raises(PermisoDenegado):
            servicios["competiciones"].cambiar_estado(
                REGISTRADOR, "c9", EstadoCompeticion.FINALIZADA
            )

    def test_un_visitante_no_cambia_el_estado(self, servicios):
        crear_liga(servicios, inscritos=1)
        with pytest.raises(PermisoDenegado):
            servicios["competiciones"].cambiar_estado(
                CURIOSO, "c1", EstadoCompeticion.FINALIZADA
            )


class TestAlcanceDeLaConcesion:
    def test_un_registrador_inscribe_en_la_suya(self, servicios):
        crear_liga(servicios, inscritos=1)
        inscrito = servicios["inscripciones"].inscribir(
            REGISTRADOR, "c1", "p9", "Los Nuevos"
        )
        assert inscrito.nombre == "Los Nuevos"

    def test_pero_no_en_otra(self, servicios):
        """Fuera de su competición es un visitante más."""
        crear_liga(servicios, inscritos=1)
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba("c2", "Otra"))
        with pytest.raises(PermisoDenegado, match="c2"):
            servicios["inscripciones"].inscribir(REGISTRADOR, "c2", "p9", "Ajenos")

    def test_un_registrador_no_sortea_ni_en_la_suya(self, servicios):
        """Ejecutar sorteos es del Admin."""
        grupos, _ = crear_liga(servicios)
        with pytest.raises(PermisoDenegado, match="sortear"):
            servicios["sorteo"].sortear(REGISTRADOR, "c1", grupos, desde=LUNES)

    def test_un_registrador_registra_resultados_en_la_suya(self, servicios):
        grupos, _ = crear_liga(servicios)
        partido = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)[0]
        cerrado = servicios["resultados"].registrar(
            REGISTRADOR, partido.id, Marcador(2, 1)
        )
        assert cerrado.esta_finalizado

    def test_el_ambito_sale_del_partido_no_de_quien_llama(self, servicios, repos):
        """Un registrador de c1 no toca un partido de c2 aunque lo pida por id."""
        servicios["competiciones"].crear(ADMIN, competicion_de_prueba("c2", "Otra"))
        repos["enfrentamientos"].guardar(
            Enfrentamiento("x1", "a", "b", competicion_id="c2", fase_id="c2:0")
        )
        with pytest.raises(PermisoDenegado, match="c2"):
            servicios["resultados"].registrar(REGISTRADOR, "x1", Marcador(1, 0))

    def test_un_visitante_no_registra_resultados(self, servicios):
        grupos, _ = crear_liga(servicios)
        partido = servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)[0]
        with pytest.raises(PermisoDenegado):
            servicios["resultados"].registrar(CURIOSO, partido.id, Marcador(2, 1))

    def test_un_visitante_no_retira_participantes(self, servicios):
        crear_liga(servicios, inscritos=2)
        with pytest.raises(PermisoDenegado):
            servicios["inscripciones"].retirar(CURIOSO, "p1")


class TestCuadroFinalConPermisos:
    def test_un_registrador_no_genera_el_cuadro(self, servicios):
        grupos, copa = crear_liga(servicios)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        with pytest.raises(PermisoDenegado):
            servicios["cuadro"].generar(REGISTRADOR, "c1", copa, desde_fase=grupos)

    def test_pero_si_carga_sus_resultados(self, servicios):
        grupos, copa = crear_liga(servicios)
        servicios["sorteo"].sortear(ADMIN, "c1", grupos, desde=LUNES)
        servicios["cuadro"].generar(ADMIN, "c1", copa, desde_fase=grupos)
        actualizado = servicios["cuadro"].registrar(
            REGISTRADOR, "c1", copa, 0, 0, Marcador(1, 0)
        )
        assert actualizado.slot(0, 0).ganador() is not None


class TestLeerEsPublico:
    def test_la_tabla_no_pide_identidad(self, servicios):
        grupos, _ = crear_liga(servicios)
        assert len(servicios["clasificacion"].de_fase("c1", grupos)) == 4

    def test_el_catalogo_de_competiciones_tampoco(self, servicios):
        crear_liga(servicios, inscritos=1)
        assert len(servicios["competiciones"].listar()) == 1


class TestPanelDeRegistradores:
    def test_el_admin_otorga_por_correo(self, servicios):
        crear_liga(servicios, inscritos=1)
        concesion = servicios["registradores"].otorgar_por_email(
            ADMIN, "c1", "nuevo@itc.edu.co"
        )
        assert concesion.rol is Rol.REGISTRADOR
        assert concesion.competicion_id == "c1"

    def test_invita_a_quien_no_existe(self, servicios, repos):
        crear_liga(servicios, inscritos=1)
        servicios["registradores"].otorgar_por_email(ADMIN, "c1", "nuevo@itc.edu.co")
        assert repos["autenticador"].por_email("nuevo@itc.edu.co") is not None

    def test_a_quien_ya_existe_no_lo_duplica(self, servicios):
        crear_liga(servicios, inscritos=1)
        concesion = servicios["registradores"].otorgar_por_email(
            ADMIN, "c1", "alguien@itc.edu.co"
        )
        assert concesion.usuario_id == CURIOSO.usuario_id

    def test_otorga_por_usuario_si_no_hay_correo(self, servicios):
        crear_liga(servicios, inscritos=1)
        concesion = servicios["registradores"].otorgar_por_usuario(ADMIN, "c1", "u9")
        assert concesion.usuario_id == "u9"

    def test_la_concesion_surte_efecto_de_inmediato(self, servicios):
        crear_liga(servicios, inscritos=1)
        with pytest.raises(PermisoDenegado):
            servicios["inscripciones"].inscribir(CURIOSO, "c1", "p8", "Antes")
        servicios["registradores"].otorgar_por_email(ADMIN, "c1", "alguien@itc.edu.co")
        assert servicios["inscripciones"].inscribir(CURIOSO, "c1", "p8", "Después")

    def test_revocar_quita_el_permiso(self, servicios):
        crear_liga(servicios, inscritos=1)
        servicios["registradores"].revocar(ADMIN, "c1", "registrador")
        with pytest.raises(PermisoDenegado):
            servicios["inscripciones"].inscribir(REGISTRADOR, "c1", "p9", "Ya no")

    def test_lista_los_registradores(self, servicios):
        crear_liga(servicios, inscritos=1)
        registradores = servicios["registradores"].de_competicion("c1")
        assert [c.usuario_id for c in registradores] == ["registrador"]

    def test_los_lista_por_su_correo(self, servicios):
        """El panel concede por correo y listaba por id, así que mostraba UUID
        crudos: no había forma de saber a quién se le revocaba el permiso."""
        crear_liga(servicios, inscritos=1)
        registradores = servicios["registradores"].de_competicion("c1")
        assert [c.etiqueta for c in registradores] == ["profe@itc.edu.co"]

    def test_sin_correo_conocido_queda_el_id(self, servicios, repos):
        """Una concesión sobrevive a su usuario el tiempo que tarde el borrado
        en cascada, y el panel tiene que poder pintar esa fila igual."""
        from itc_deporte.aplicacion.permisos import Concesion, Rol

        crear_liga(servicios, inscritos=1)
        repos["concesiones"].otorgar(Concesion("fantasma", Rol.REGISTRADOR, "c1"))
        etiquetas = [c.etiqueta for c in servicios["registradores"].de_competicion("c1")]
        assert "fantasma" in etiquetas

    def test_un_registrador_no_reparte_permisos(self, servicios):
        """Ni siquiera en su propia competición."""
        crear_liga(servicios, inscritos=1)
        with pytest.raises(PermisoDenegado, match="gestionar_registradores"):
            servicios["registradores"].otorgar_por_email(
                REGISTRADOR, "c1", "amigo@itc.edu.co"
            )

    def test_un_visitante_tampoco(self, servicios):
        crear_liga(servicios, inscritos=1)
        with pytest.raises(PermisoDenegado):
            servicios["registradores"].otorgar_por_usuario(CURIOSO, "c1", "u9")

    def test_rechaza_una_competicion_inexistente(self, servicios):
        with pytest.raises(NoEncontrado, match="competición"):
            servicios["registradores"].otorgar_por_usuario(ADMIN, "fantasma", "u9")

    def test_revocar_exige_permiso(self, servicios):
        crear_liga(servicios, inscritos=1)
        with pytest.raises(PermisoDenegado):
            servicios["registradores"].revocar(CURIOSO, "c1", "registrador")
