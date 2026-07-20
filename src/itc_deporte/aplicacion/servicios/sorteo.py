"""Sortear el calendario de una fase.

Dos diferencias de fondo con `realizar_sorteo`:

- **Una escritura, no N.** El sorteo anterior hacía un `INSERT` por partido
  dentro de un bucle. Aquí el calendario entero se arma en memoria y se guarda
  de una vez con `guardar_muchos`.
- **El azar se inyecta.** Recibe un `random.Random`, así que el mismo sorteo con
  la misma semilla produce el mismo resultado y es reproducible en un test. Antes
  llamaba a `random.shuffle` sobre el estado global.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Sequence

from ...domain.competicion import Competicion, Fase, FaseDeGrupos
from ...domain.enfrentamiento import Enfrentamiento
from ...domain.identidades import CompeticionId, FaseId
from ...domain.reglas.catalogo import crear_fixture
from ..errores import NoEncontrado, OperacionInvalida
from ..permisos import Accion, Identidad, Politica
from ..puertos import (
    RepositorioDeCompeticiones,
    RepositorioDeEnfrentamientos,
    RepositorioDeParticipantes,
)


class ServicioDeSorteo:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        participantes: RepositorioDeParticipantes,
        enfrentamientos: RepositorioDeEnfrentamientos,
        politica: Politica,
        azar: random.Random | None = None,
    ) -> None:
        self._competiciones = competiciones
        self._participantes = participantes
        self._enfrentamientos = enfrentamientos
        self._politica = politica
        self._azar = azar or random.Random()

    def sortear(
        self,
        actor: Identidad,
        competicion_id: CompeticionId,
        fase_id: FaseId,
        desde: dt.date | None = None,
    ) -> tuple[Enfrentamiento, ...]:
        """Genera el calendario de la fase y lo guarda, reemplazando el anterior."""
        self._politica.exigir(actor, Accion.SORTEAR, competicion_id)
        competicion, fase = self._localizar(competicion_id, fase_id)

        inscritos = [p.id for p in self._participantes.de_competicion(competicion_id)]
        if len(inscritos) < 2:
            raise OperacionInvalida(
                f"Se necesitan al menos 2 participantes para sortear, hay "
                f"{len(inscritos)}."
            )
        self._azar.shuffle(inscritos)

        jornadas = crear_fixture(fase.fixture).generar(inscritos, fase.config_fixture)
        fechas = competicion.calendario.fechas(
            desde or dt.date.today(), len(jornadas)
        )

        partidos = tuple(
            Enfrentamiento(
                id=f"{fase.id}:j{jornada.numero}:{posicion}",
                local=cruce.local,
                visitante=cruce.visitante,
                competicion_id=competicion.id,
                fase_id=fase.id,
                jornada=jornada.numero,
                fecha=fecha,
            )
            for jornada, fecha in zip(jornadas, fechas)
            for posicion, cruce in enumerate(jornada.cruces)
        )

        # Rehacer el sorteo descarta el calendario anterior por completo: dejar
        # partidos de un sorteo viejo mezclados con los del nuevo era una de las
        # formas en que se corrompían los datos.
        self._enfrentamientos.eliminar_de_fase(fase.id)
        self._enfrentamientos.guardar_muchos(partidos)
        return partidos

    def _localizar(
        self, competicion_id: CompeticionId, fase_id: FaseId
    ) -> tuple[Competicion, Fase]:
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        fase = competicion.fase(fase_id)
        if fase is None:
            raise NoEncontrado(
                f"La competición {competicion_id!r} no tiene la fase {fase_id!r}."
            )
        if not isinstance(fase, FaseDeGrupos):
            raise OperacionInvalida(
                f"La fase {fase_id!r} no es de grupos: el cuadro final se genera "
                "a partir de la clasificación, no por sorteo."
            )
        return competicion, fase
