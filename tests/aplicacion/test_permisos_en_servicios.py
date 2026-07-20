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
from itc_deporte.domain.competicion import EstadoCompeticion
from itc_deporte.domain.enfrentamiento import Enfrentamiento, Marcador
from itc_deporte.infraestructura.autenticacion import (
    AutenticadorEnMemoria,
    ConcesionesEnMemoria,
)
from itc_deporte.infraestructura.memoria import (
    CompeticionesEnMemoria,
    EnfrentamientosEnMemoria,
    ParticipantesEnMemoria,
    PlantillasEnMemoria,
)
from itc_deporte.infraestructura.plantillas import cargar_semillas

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
        "plantillas": PlantillasEnMemoria(cargar_semillas()),
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
            repos["competiciones"], repos["plantillas"], politica
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
        "resultados": ServicioDeResultados(repos["enfrentamientos"], politica),
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


def crear_liga(servicios, inscritos=4):
    servicios["competiciones"].crear_desde_plantilla(
        ADMIN, "itc-microfutbol", "c1", "Prueba"
    )
    for i in range(1, inscritos + 1):
        servicios["inscripciones"].inscribir(ADMIN, "c1", f"p{i}", f"Equipo {i}")
    return "c1:0", "c1:1"


class TestCrearCompeticiones:
    def test_un_visitante_no_puede(self, servicios):
        with pytest.raises(PermisoDenegado, match="crear_competicion"):
            servicios["competiciones"].crear_desde_plantilla(
                CURIOSO, "itc-microfutbol", "c9"
            )

    def test_un_anonimo_tampoco(self, servicios):
        with pytest.raises(PermisoDenegado):
            servicios["competiciones"].crear_desde_plantilla(
                ANONIMO, "itc-microfutbol", "c9"
            )

    def test_un_registrador_tampoco(self, servicios):
        with pytest.raises(PermisoDenegado):
            servicios["competiciones"].crear_desde_plantilla(
                REGISTRADOR, "itc-microfutbol", "c9"
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
        servicios["competiciones"].crear_desde_plantilla(ADMIN, "itc-baloncesto", "c2")
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
        servicios["competiciones"].crear_desde_plantilla(ADMIN, "itc-baloncesto", "c2")
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
