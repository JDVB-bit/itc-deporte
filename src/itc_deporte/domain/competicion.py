"""Competición: la raíz que compone fases.

Una competición es una lista ordenada de fases —de grupos, eliminatorias, o
ambas— que es exactamente el "grupos y/o partidos" del requisito. El sistema
anterior no tenía este concepto: la competición era la pareja implícita
`(categoria, deporte)` repetida como par de argumentos en cada función, y el
formato estaba fijado en el código (round-robin de 7 jornadas, luego un cuadro
de 16 que nunca llegó a conectarse a la interfaz).

`Deporte` también deja de ser una constante: la lista de cuatro deportes del ITC
pasa a ser dato configurable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .calendario import Calendario
from .errores import ErrorDeDominio
from .identidades import CompeticionId, FaseId, GrupoId, ParticipanteId
from .reglas.fixture import ConfigFixture
from .reglas.desempate import DESEMPATE_CLASICO, CriterioDeDesempate
from .reglas.puntuacion import SistemaDePuntuacion, VictoriaDerrota


@dataclass(frozen=True, slots=True)
class Deporte:
    """Antes: las constantes `DEPORTES` e `ICONOS_DEP`."""

    id: str
    nombre: str
    icono: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Un deporte necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Un deporte necesita un nombre no vacío.")


@dataclass(frozen=True, slots=True, eq=False)
class Grupo:
    id: GrupoId
    nombre: str
    participantes: tuple[ParticipanteId, ...] = ()

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Un grupo necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Un grupo necesita un nombre no vacío.")
        if len(self.participantes) != len(set(self.participantes)):
            raise ErrorDeDominio(f"Participante repetido en el grupo {self.id!r}.")

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Grupo):
            return NotImplemented
        return self.id == otro.id

    def __hash__(self) -> int:
        return hash(self.id)

    def con_participante(self, participante_id: ParticipanteId) -> Grupo:
        if participante_id in self.participantes:
            raise ErrorDeDominio(
                f"El participante {participante_id!r} ya está en el grupo {self.id!r}."
            )
        return replace(self, participantes=self.participantes + (participante_id,))

    def sin_participante(self, participante_id: ParticipanteId) -> Grupo:
        if participante_id not in self.participantes:
            raise ErrorDeDominio(
                f"El participante {participante_id!r} no está en el grupo {self.id!r}."
            )
        restantes = tuple(p for p in self.participantes if p != participante_id)
        return replace(self, participantes=restantes)


@dataclass(frozen=True, slots=True, eq=False)
class Fase:
    """Base común.

    `orden` fija la secuencia dentro de la competición. `fixture` y
    `config_fixture` dicen cómo se arma su calendario: sin ellos la fase no
    sabría sortearse, y las siete jornadas del ITC volverían a ser un número
    escondido en el código.
    """

    id: FaseId
    nombre: str
    orden: int
    fixture: str = "round_robin"
    config_fixture: ConfigFixture = ConfigFixture()

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Una fase necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Una fase necesita un nombre no vacío.")
        if self.orden < 0:
            raise ErrorDeDominio(f"Orden de fase inválido: {self.orden}")

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Fase):
            return NotImplemented
        return self.id == otro.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(frozen=True, slots=True, eq=False)
class FaseDeGrupos(Fase):
    grupos: tuple[Grupo, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        ids = [g.id for g in self.grupos]
        if len(ids) != len(set(ids)):
            raise ErrorDeDominio(f"Grupos con id repetido en la fase {self.id!r}.")
        inscritos = [p for g in self.grupos for p in g.participantes]
        if len(inscritos) != len(set(inscritos)):
            raise ErrorDeDominio(
                f"Un participante está en dos grupos de la fase {self.id!r}."
            )

    @property
    def participantes(self) -> tuple[ParticipanteId, ...]:
        return tuple(p for g in self.grupos for p in g.participantes)

    def grupo(self, grupo_id: GrupoId) -> Grupo | None:
        return next((g for g in self.grupos if g.id == grupo_id), None)

    def grupo_de(self, participante_id: ParticipanteId) -> Grupo | None:
        return next(
            (g for g in self.grupos if participante_id in g.participantes), None
        )


@dataclass(frozen=True, slots=True, eq=False)
class FaseEliminatoria(Fase):
    """`cupos` es cuántos participantes entran al cuadro.

    Sustituye al tope fijo de 16 del bracket anterior. No tiene que ser potencia
    de dos: un cuadro de 6 se completa con byes.
    """

    cupos: int = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.cupos < 2:
            raise ErrorDeDominio(
                f"Una eliminatoria necesita al menos 2 cupos, no {self.cupos}."
            )


class EstadoCompeticion(Enum):
    BORRADOR = "Borrador"
    EN_CURSO = "En curso"
    FINALIZADA = "Finalizada"


@dataclass(frozen=True, slots=True)
class ReglasDeCompeticion:
    """Cómo puntúa y cómo desempata esta competición.

    Los valores por defecto reproducen lo que el sistema aplicaba a todo: 3/1/0
    y desempate por puntos, diferencia y a favor. Una competición de voleibol
    cambia la puntuación sin que nada más se entere.
    """

    puntuacion: SistemaDePuntuacion = VictoriaDerrota()
    desempate: tuple[CriterioDeDesempate, ...] = DESEMPATE_CLASICO

    def __post_init__(self) -> None:
        if not self.desempate:
            raise ErrorDeDominio(
                "Una competición necesita al menos un criterio de desempate."
            )


@dataclass(frozen=True, slots=True, eq=False)
class Competicion:
    id: CompeticionId
    nombre: str
    deporte: Deporte
    temporada: str | None = None
    estado: EstadoCompeticion = EstadoCompeticion.BORRADOR
    fases: tuple[Fase, ...] = ()
    reglas: ReglasDeCompeticion = ReglasDeCompeticion()
    calendario: Calendario = Calendario()

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Una competición necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Una competición necesita un nombre no vacío.")
        ids = [f.id for f in self.fases]
        if len(ids) != len(set(ids)):
            raise ErrorDeDominio(f"Fases con id repetido en {self.id!r}.")
        ordenes = [f.orden for f in self.fases]
        if len(ordenes) != len(set(ordenes)):
            raise ErrorDeDominio(
                f"Dos fases comparten el mismo orden en {self.id!r}: {sorted(ordenes)}"
            )

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Competicion):
            return NotImplemented
        return self.id == otro.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def fases_ordenadas(self) -> tuple[Fase, ...]:
        return tuple(sorted(self.fases, key=lambda f: f.orden))

    @property
    def primera_fase(self) -> Fase | None:
        ordenadas = self.fases_ordenadas
        return ordenadas[0] if ordenadas else None

    def fase(self, fase_id: FaseId) -> Fase | None:
        return next((f for f in self.fases if f.id == fase_id), None)

    def fase_siguiente_a(self, fase_id: FaseId) -> Fase | None:
        ordenadas = self.fases_ordenadas
        for indice, fase in enumerate(ordenadas):
            if fase.id == fase_id:
                return ordenadas[indice + 1] if indice + 1 < len(ordenadas) else None
        return None

    def con_fase(self, fase: Fase) -> Competicion:
        return replace(self, fases=self.fases + (fase,))

    def sin_fase(self, fase_id: FaseId) -> Competicion:
        if self.fase(fase_id) is None:
            raise ErrorDeDominio(f"La fase {fase_id!r} no existe en {self.id!r}.")
        return replace(self, fases=tuple(f for f in self.fases if f.id != fase_id))
