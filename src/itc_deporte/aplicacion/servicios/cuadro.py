"""Generar y avanzar el cuadro final.

El cuadro se guarda como enfrentamientos con `ronda` y `slot`, así que vive en
la misma tabla que el resto de partidos en lugar de en una tabla `llaves`
aparte. La propagación ocurre en memoria —el motor devuelve el cuadro entero ya
resuelto— y se persiste de una vez, en lugar de con un UPDATE por casilla.
"""

from __future__ import annotations

from ...domain.enfrentamiento import Enfrentamiento, Marcador
from ...domain.identidades import CompeticionId, FaseId
from ...domain.competicion import FaseEliminatoria
from ...domain.motor.bracket import Bracket, SlotDeBracket
from ..errores import NoEncontrado, OperacionInvalida
from ..permisos import Accion, Identidad, Politica
from ..puertos import RepositorioDeCompeticiones, RepositorioDeEnfrentamientos
from .clasificacion import ServicioDeClasificacion


class ServicioDeCuadroFinal:
    def __init__(
        self,
        competiciones: RepositorioDeCompeticiones,
        enfrentamientos: RepositorioDeEnfrentamientos,
        clasificacion: ServicioDeClasificacion,
        politica: Politica,
    ) -> None:
        self._competiciones = competiciones
        self._enfrentamientos = enfrentamientos
        self._clasificacion = clasificacion
        self._politica = politica

    def generar(
        self,
        actor: Identidad,
        competicion_id: CompeticionId,
        fase_id: FaseId,
        desde_fase: FaseId,
    ) -> Bracket:
        """Arma el cuadro con los mejores clasificados de `desde_fase`."""
        self._politica.exigir(actor, Accion.SORTEAR, competicion_id)
        fase = self._eliminatoria(competicion_id, fase_id)
        tabla = self._clasificacion.de_fase(competicion_id, desde_fase)
        clasificados = [fila.participante_id for fila in tabla[: fase.cupos]]
        if len(clasificados) < 2:
            raise OperacionInvalida(
                f"Hacen falta al menos 2 clasificados para el cuadro, hay "
                f"{len(clasificados)}."
            )
        bracket = Bracket.desde_clasificados(clasificados)
        self._persistir(competicion_id, fase_id, bracket)
        return bracket

    def actual(self, competicion_id: CompeticionId, fase_id: FaseId) -> Bracket:
        """Reconstruye el cuadro a partir de lo guardado."""
        self._eliminatoria(competicion_id, fase_id)
        partidos = self._enfrentamientos.de_fase(fase_id)
        if not partidos:
            raise NoEncontrado(f"La fase {fase_id!r} todavía no tiene cuadro.")
        return _reconstruir(partidos)

    def registrar(
        self,
        actor: Identidad,
        competicion_id: CompeticionId,
        fase_id: FaseId,
        ronda: int,
        posicion: int,
        marcador: Marcador,
    ) -> Bracket:
        """Carga un resultado y persiste el cuadro ya propagado."""
        self._politica.exigir(
            actor, Accion.REGISTRAR_RESULTADO, competicion_id
        )
        # Por el mismo motivo que en `ServicioDeResultados`: un marcador que la
        # puntuación no admite entraba y reventaba después al calcular la tabla.
        # El cuadro comparte tabla y reglas con la fase de grupos.
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        competicion.reglas.exigir_que_admita(marcador)
        bracket = self.actual(competicion_id, fase_id).con_resultado(
            ronda, posicion, marcador
        )
        self._persistir(competicion_id, fase_id, bracket)
        return bracket

    # ── Interno ─────────────────────────────────────────────────────────────

    def _eliminatoria(
        self, competicion_id: CompeticionId, fase_id: FaseId
    ) -> FaseEliminatoria:
        competicion = self._competiciones.obtener(competicion_id)
        if competicion is None:
            raise NoEncontrado(f"No existe la competición {competicion_id!r}.")
        fase = competicion.fase(fase_id)
        if not isinstance(fase, FaseEliminatoria):
            raise OperacionInvalida(f"La fase {fase_id!r} no es una eliminatoria.")
        return fase

    def _persistir(
        self, competicion_id: CompeticionId, fase_id: FaseId, bracket: Bracket
    ) -> None:
        partidos = [
            _a_enfrentamiento(competicion_id, fase_id, casilla)
            for ronda in bracket.rondas
            for casilla in ronda
        ]
        self._enfrentamientos.eliminar_de_fase(fase_id)
        self._enfrentamientos.guardar_muchos(partidos)


def _a_enfrentamiento(
    competicion_id: CompeticionId, fase_id: FaseId, casilla: SlotDeBracket
) -> Enfrentamiento:
    partido = Enfrentamiento(
        id=f"{fase_id}:r{casilla.ronda}:{casilla.posicion}",
        local=casilla.local,
        visitante=casilla.visitante,
        competicion_id=competicion_id,
        fase_id=fase_id,
        ronda=casilla.ronda,
        slot=casilla.posicion,
    )
    return partido.finalizar(casilla.marcador) if casilla.marcador else partido


def _reconstruir(partidos: tuple[Enfrentamiento, ...]) -> Bracket:
    por_ronda: dict[int, list[Enfrentamiento]] = {}
    for partido in partidos:
        por_ronda.setdefault(partido.ronda, []).append(partido)
    rondas = tuple(
        tuple(
            SlotDeBracket(
                ronda=p.ronda,
                posicion=p.slot,
                local=p.local,
                visitante=p.visitante,
                marcador=p.marcador,
            )
            for p in sorted(por_ronda[numero], key=lambda p: p.slot)
        )
        for numero in sorted(por_ronda)
    )
    return Bracket(rondas)
