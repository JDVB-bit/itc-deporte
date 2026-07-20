"""Traduce los datos heredados al modelo nuevo.

Función pura: entran las filas de las tablas viejas, sale el modelo nuevo más un
**reporte de conflictos**. No toca la base ni decide nada; quien ejecute la
migración mira el reporte antes de escribir nada.

Aquí se usa `parsear_enf` **por última vez**. Cada enfrentamiento guardado como
`"Nombre (Curso) vs Nombre (Curso)"` se resuelve a ids de participante, y a
partir de la migración el parser desaparece del código.

**Las filas irresolubles no se descartan en silencio.** Salen en el reporte con
el motivo, para resolución manual. Es el requisito de §9 del plan, y no es
paranoia: los tests de caracterización de la Fase 0 dejaron documentado que un
equipo cuyo nombre contenga " vs " rompe el parser, así que hay filas que de
verdad no se pueden resolver.

Los ids son **deterministas**: traducir dos veces produce exactamente lo mismo.
Eso permite ensayar la migración cuantas veces haga falta antes de escribir.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from ...domain.competicion import (
    Competicion,
    Deporte,
    EstadoCompeticion,
    FaseDeGrupos,
    FaseEliminatoria,
)
from ...domain.division import Division
from ...domain.enfrentamiento import Enfrentamiento, Marcador
from ...domain.participante import Miembro, Participante
from ...domain.reglas.fixture import ConfigFixture
from ...legado.motor_actual import CURSOS_VALIDOS, ICONOS_DEP, parsear_enf

#: Orden de las rondas en la tabla `llaves` heredada.
RONDAS_LEGADO = ["OCTAVOS", "CUARTOS", "SEMIFINAL", "FINAL"]


@dataclass(frozen=True, slots=True)
class Conflicto:
    """Una fila que no se pudo traducir. Requiere decisión humana."""

    tabla: str
    fila_id: object
    motivo: str
    dato: str

    def __str__(self) -> str:
        return f"[{self.tabla}#{self.fila_id}] {self.motivo}: {self.dato}"


@dataclass
class Reporte:
    competiciones: list[Competicion] = field(default_factory=list)
    divisiones: list[Division] = field(default_factory=list)
    participantes: list[Participante] = field(default_factory=list)
    enfrentamientos: list[Enfrentamiento] = field(default_factory=list)
    conflictos: list[Conflicto] = field(default_factory=list)

    @property
    def hay_conflictos(self) -> bool:
        return bool(self.conflictos)

    def resumen(self) -> str:
        return (
            f"{len(self.competiciones)} competiciones, "
            f"{len(self.participantes)} participantes, "
            f"{len(self.enfrentamientos)} enfrentamientos, "
            f"{len(self.conflictos)} conflictos"
        )


def _clave(texto: str) -> str:
    """Convierte un texto en algo usable como id: sin tildes, sin espacios."""
    sin_tildes = "".join(
        c
        for c in unicodedata.normalize("NFD", str(texto))
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")


def id_de_competicion(categoria: str, deporte: str) -> str:
    return f"{_clave(categoria)}-{_clave(deporte)}"


def id_de_participante(competicion_id: str, curso: str, nombre: str) -> str:
    return f"{competicion_id}:{_clave(curso)}:{_clave(nombre)}"


def _reglas_de(deporte: str):
    """El voleibol pasa a puntuación por sets; el resto conserva el 3/1/0.

    Es el cambio de comportamiento previsto en §12, y ocurre aquí: los partidos
    ya jugados se recalculan con la regla nueva al leerlos.
    """
    from ...domain.competicion import ReglasDeCompeticion
    from ...domain.reglas.puntuacion import PorSets

    if _clave(deporte) == "voleyball":
        return ReglasDeCompeticion(puntuacion=PorSets())
    return ReglasDeCompeticion()


def traducir(
    equipos: Sequence[Mapping],
    jugadores: Sequence[Mapping] = (),
    partidos: Sequence[Mapping] = (),
    llaves: Sequence[Mapping] = (),
) -> Reporte:
    """Traduce todo el estado heredado. No escribe nada."""
    reporte = Reporte()

    # ── Competiciones: una por cada pareja (categoría, deporte) ──────────────
    parejas = sorted(
        {(str(e["categoria"]), str(e["deporte"])) for e in equipos}
        | {(str(p["categoria"]), str(p["deporte"])) for p in partidos}
        | {(str(l["categoria"]), str(l["deporte"])) for l in llaves}
    )
    por_pareja: dict[tuple[str, str], Competicion] = {}
    for categoria, deporte in parejas:
        competicion_id = id_de_competicion(categoria, deporte)
        competicion = Competicion(
            id=competicion_id,
            nombre=f"{categoria} — {deporte}",
            deporte=Deporte(_clave(deporte), deporte, ICONOS_DEP.get(deporte, "")),
            estado=EstadoCompeticion.EN_CURSO,
            fases=(
                FaseDeGrupos(
                    f"{competicion_id}:0",
                    "Fase de grupos",
                    0,
                    config_fixture=ConfigFixture(jornadas_forzadas=7),
                ),
                FaseEliminatoria(
                    f"{competicion_id}:1",
                    "Eliminación directa",
                    1,
                    fixture="eliminacion_directa",
                    cupos=16,
                ),
            ),
            reglas=_reglas_de(deporte),
        )
        por_pareja[(categoria, deporte)] = competicion
        reporte.competiciones.append(competicion)
        reporte.divisiones.append(Division(categoria, categoria))

    # ── Participantes ───────────────────────────────────────────────────────
    # Índice (competicion, nombre, curso) -> id, que es lo que permite resolver
    # los enfrentamientos guardados como texto.
    indice: dict[tuple[str, str, str], str] = {}
    vistos: set[str] = set()

    for fila in equipos:
        categoria, deporte = str(fila["categoria"]), str(fila["deporte"])
        curso = str(fila["curso"]).strip().strip("'\"")
        nombre = str(fila["nombre"]).strip()
        competicion_id = id_de_competicion(categoria, deporte)

        if curso not in CURSOS_VALIDOS:
            reporte.conflictos.append(
                Conflicto("equipos", fila.get("id"), "curso inválido", f"{nombre} ({curso})")
            )
            continue
        if not nombre:
            reporte.conflictos.append(
                Conflicto("equipos", fila.get("id"), "nombre vacío", f"curso {curso}")
            )
            continue

        participante_id = id_de_participante(competicion_id, curso, nombre)
        if participante_id in vistos:
            reporte.conflictos.append(
                Conflicto(
                    "equipos", fila.get("id"), "equipo duplicado", f"{nombre} ({curso})"
                )
            )
            continue

        vistos.add(participante_id)
        indice[(competicion_id, nombre, curso)] = participante_id
        if categoria not in {d.id for d in reporte.divisiones}:
            reporte.divisiones.append(Division(categoria, categoria))
        if curso not in {d.id for d in reporte.divisiones}:
            reporte.divisiones.append(Division(curso, curso, padre_id=categoria))
        reporte.participantes.append(
            Participante(
                id=participante_id,
                nombre=nombre,
                competicion_id=competicion_id,
                division_id=curso,
            )
        )

    _agregar_miembros(jugadores, indice, reporte)
    _traducir_partidos(partidos, indice, reporte)
    _traducir_llaves(llaves, indice, reporte)
    return reporte


def _agregar_miembros(
    jugadores: Iterable[Mapping], indice: Mapping, reporte: Reporte
) -> None:
    por_id = {p.id: p for p in reporte.participantes}
    for fila in jugadores:
        competicion_id = id_de_competicion(
            str(fila["categoria"]), str(fila["deporte"])
        )
        curso = str(fila["curso"]).strip().strip("'\"")
        equipo = str(fila["equipo"]).strip()
        nombre = str(fila["nombre"]).strip()

        participante_id = indice.get((competicion_id, equipo, curso))
        if participante_id is None:
            reporte.conflictos.append(
                Conflicto(
                    "jugadores",
                    fila.get("id"),
                    "el equipo del jugador no existe",
                    f"{nombre} → {equipo} ({curso})",
                )
            )
            continue
        if not nombre:
            reporte.conflictos.append(
                Conflicto("jugadores", fila.get("id"), "nombre vacío", equipo)
            )
            continue
        miembro_id = f"{participante_id}:{_clave(nombre)}"
        actual = por_id[participante_id]
        if actual.miembro(miembro_id) is not None:
            reporte.conflictos.append(
                Conflicto(
                    "jugadores", fila.get("id"), "jugador duplicado", f"{nombre} en {equipo}"
                )
            )
            continue
        por_id[participante_id] = actual.con_miembro(Miembro(miembro_id, nombre))

    reporte.participantes = [por_id[p.id] for p in reporte.participantes]


def _resolver(
    lado: tuple[str, str], competicion_id: str, indice: Mapping
) -> str | None:
    nombre, curso = lado
    return indice.get((competicion_id, nombre.strip(), curso.strip()))


def _traducir_partidos(
    partidos: Iterable[Mapping], indice: Mapping, reporte: Reporte
) -> None:
    for fila in partidos:
        categoria, deporte = str(fila["categoria"]), str(fila["deporte"])
        competicion_id = id_de_competicion(categoria, deporte)
        fase_id = f"{competicion_id}:0"
        enf = fila.get("enf")

        parseado = parsear_enf(enf)
        if parseado is None:
            reporte.conflictos.append(
                Conflicto("partidos", fila.get("id"), "no se pudo parsear", str(enf))
            )
            continue

        n1, c1, n2, c2 = parseado
        local = _resolver((n1, c1), competicion_id, indice)
        visitante = _resolver((n2, c2), competicion_id, indice)
        if local is None or visitante is None:
            falta = []
            if local is None:
                falta.append(f"{n1} ({c1})")
            if visitante is None:
                falta.append(f"{n2} ({c2})")
            reporte.conflictos.append(
                Conflicto(
                    "partidos",
                    fila.get("id"),
                    "no se pudo resolver a un equipo inscrito",
                    " y ".join(falta),
                )
            )
            continue
        if local == visitante:
            reporte.conflictos.append(
                Conflicto(
                    "partidos", fila.get("id"), "un equipo contra sí mismo", str(enf)
                )
            )
            continue

        finalizado = str(fila.get("estado", "")) == "Finalizado"
        partido = Enfrentamiento(
            id=f"legado:partido:{fila.get('id')}",
            local=local,
            visitante=visitante,
            competicion_id=competicion_id,
            fase_id=fase_id,
            fecha=_fecha(fila.get("fecha")),
        )
        if finalizado:
            partido = partido.finalizar(
                Marcador(int(fila.get("g1") or 0), int(fila.get("g2") or 0))
            )
        reporte.enfrentamientos.append(partido)


def _traducir_llaves(
    llaves: Iterable[Mapping], indice: Mapping, reporte: Reporte
) -> None:
    """El cuadro heredado, que la interfaz nunca llegó a mostrar."""
    for fila in llaves:
        categoria, deporte = str(fila["categoria"]), str(fila["deporte"])
        competicion_id = id_de_competicion(categoria, deporte)
        fase_id = f"{competicion_id}:1"
        ronda_nombre = str(fila.get("ronda", ""))

        if ronda_nombre not in RONDAS_LEGADO:
            reporte.conflictos.append(
                Conflicto("llaves", fila.get("id"), "ronda desconocida", ronda_nombre)
            )
            continue

        lados = []
        for numero in ("1", "2"):
            nombre = fila.get(f"equipo{numero}")
            curso = fila.get(f"curso{numero}")
            if not nombre:
                lados.append(None)
                continue
            resuelto = _resolver(
                (str(nombre), str(curso or "")), competicion_id, indice
            )
            if resuelto is None:
                reporte.conflictos.append(
                    Conflicto(
                        "llaves",
                        fila.get("id"),
                        "casilla con un equipo no inscrito",
                        f"{nombre} ({curso})",
                    )
                )
                lados.append(None)
                continue
            lados.append(resuelto)

        local, visitante = lados
        if local is not None and local == visitante:
            reporte.conflictos.append(
                Conflicto(
                    "llaves", fila.get("id"), "un equipo contra sí mismo", str(local)
                )
            )
            continue

        casilla = Enfrentamiento(
            id=f"legado:llave:{fila.get('id')}",
            local=local,
            visitante=visitante,
            competicion_id=competicion_id,
            fase_id=fase_id,
            ronda=RONDAS_LEGADO.index(ronda_nombre),
            slot=int(fila.get("slot") or 0),
        )
        if (
            str(fila.get("estado", "")) == "Finalizado"
            and local is not None
            and visitante is not None
        ):
            casilla = casilla.finalizar(
                Marcador(int(fila.get("g1") or 0), int(fila.get("g2") or 0))
            )
        reporte.enfrentamientos.append(casilla)


def _fecha(valor):
    import datetime as dt

    if not valor:
        return None
    for formato in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(str(valor), formato)
        except ValueError:
            continue
    return None
