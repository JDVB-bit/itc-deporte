"""Repositorios sobre Supabase.

Quedan finos porque la traducción vive en `mapeadores.py`, que sí está probada.
Lo que hay aquí es la conversación con la red: qué se consulta, en qué orden y
cuántas veces.

**Estado de verificación: comprobados.** Heredan los tests de contrato de
`tests/contratos/` y los 42 pasan contra una instancia real
(`pytest -m supabase`). Lo que corre aquí es lo mismo que corre contra los
repositorios en memoria, así que ninguna implementación puede desviarse de la
otra sin que la suite lo diga.

Una nota sobre las escrituras: `guardar_muchos` hace **un** `upsert` con todas
las filas. Es el arreglo del problema 10 del diagnóstico —el sorteo insertaba un
partido por llamada y el cuadro actualizaba una casilla por llamada—, y la razón
de que el puerto admita el lote.
"""

from __future__ import annotations

import uuid as _uuid
from typing import Any, Sequence

from ...domain.competicion import Competicion, Deporte
from ...domain.enfrentamiento import Enfrentamiento
from ...domain.identidades import (
    CompeticionId,
    EnfrentamientoId,
    FaseId,
    ParticipanteId,
)
from ...domain.participante import Participante
from ...aplicacion.permisos import Concesion, Rol
from . import mapeadores as m


class _Base:
    def __init__(self, cliente: Any) -> None:
        self._db = cliente

    def _filas(self, respuesta) -> list[dict]:
        return list(getattr(respuesta, "data", None) or [])

    def _una(self, respuesta) -> dict | None:
        filas = self._filas(respuesta)
        return filas[0] if filas else None


class CompeticionesSupabase(_Base):
    def obtener(self, competicion_id: CompeticionId) -> Competicion | None:
        fila = self._una(
            self._db.table("competiciones").select("*").eq("id", competicion_id).execute()
        )
        if fila is None:
            return None
        return self._componer([fila])[0]

    def listar(self) -> tuple[Competicion, ...]:
        """Tres consultas en total, no dos por competición.

        Antes componía cada competición por su cuenta, con una consulta para su
        deporte y otra para sus fases. La barra lateral las lista todas en cada
        recarga, así que con seis competiciones eran trece viajes de red para
        pintar un menú.
        """
        filas = self._filas(self._db.table("competiciones").select("*").execute())
        return self._componer(filas)

    def guardar(self, competicion: Competicion) -> None:
        self._db.table("deportes").upsert(
            m.deporte_a_fila(competicion.deporte), on_conflict="id"
        ).execute()
        self._db.table("competiciones").upsert(
            m.competicion_a_fila(competicion), on_conflict="id"
        ).execute()
        if competicion.fases:
            # Un solo upsert con todas las fases, no una llamada por fase.
            self._db.table("fases").upsert(
                [m.fase_a_fila(f, competicion.id) for f in competicion.fases],
                on_conflict="competicion_id,id",
            ).execute()

    def eliminar(self, competicion_id: CompeticionId) -> None:
        self._db.table("competiciones").delete().eq("id", competicion_id).execute()

    def _componer(self, filas: list[dict]) -> tuple[Competicion, ...]:
        """Compone el lote entero con dos consultas, sean una o veinte filas."""
        if not filas:
            return ()
        deportes = self._deportes({f["deporte_id"] for f in filas})
        fases = self._fases([f["id"] for f in filas])
        return tuple(
            m.competicion_desde_fila(
                fila,
                deportes.get(fila["deporte_id"])
                # Un deporte que no está en el catálogo no impide leer la
                # competición: se muestra con su id por nombre.
                or Deporte(fila["deporte_id"], fila["deporte_id"]),
                fases.get(fila["id"], ()),
            )
            for fila in filas
        )

    def _deportes(self, ids: set[str]) -> dict[str, Deporte]:
        filas = self._filas(
            self._db.table("deportes").select("*").in_("id", sorted(ids)).execute()
        )
        return {f["id"]: m.deporte_desde_fila(f) for f in filas}

    def _fases(self, competiciones: Sequence[str]) -> dict[str, tuple]:
        filas = self._filas(
            self._db.table("fases")
            .select("*")
            .in_("competicion_id", list(competiciones))
            .order("orden")
            .execute()
        )
        agrupadas: dict[str, list] = {}
        for fila in filas:
            agrupadas.setdefault(fila["competicion_id"], []).append(
                m.fase_desde_fila(fila)
            )
        return {clave: tuple(valor) for clave, valor in agrupadas.items()}


class ParticipantesSupabase(_Base):
    def obtener(self, participante_id: ParticipanteId) -> Participante | None:
        fila = self._una(
            self._db.table("participantes").select("*").eq("id", participante_id).execute()
        )
        if fila is None:
            return None
        return m.participante_desde_fila(fila, tuple(self._miembros([participante_id])))

    def de_competicion(self, competicion_id: CompeticionId) -> tuple[Participante, ...]:
        filas = self._filas(
            self._db.table("participantes")
            .select("*")
            .eq("competicion_id", competicion_id)
            .execute()
        )
        if not filas:
            return ()
        # Los miembros de todos los participantes en una sola consulta, no una
        # por participante.
        miembros = self._miembros([f["id"] for f in filas])
        por_participante: dict[str, list[dict]] = {}
        for miembro in miembros:
            por_participante.setdefault(miembro["participante_id"], []).append(miembro)
        return tuple(
            m.participante_desde_fila(f, tuple(por_participante.get(f["id"], ())))
            for f in filas
        )

    def guardar(self, participante: Participante) -> None:
        self._asegurar_division(participante)
        self._db.table("participantes").upsert(
            m.participante_a_fila(participante), on_conflict="id"
        ).execute()
        self._db.table("miembros").delete().eq(
            "participante_id", participante.id
        ).execute()
        filas = m.miembros_a_filas(participante)
        if filas:
            self._db.table("miembros").upsert(filas, on_conflict="id").execute()

    def _asegurar_division(self, participante: Participante) -> None:
        """Da de alta la división del participante si aún no existe.

        `participantes` referencia `divisiones` con una clave ajena compuesta,
        y **nada** escribía nunca en esa tabla: no hay repositorio de
        divisiones ni servicio que las cree. En memoria no se notaba, porque no
        hay integridad referencial; contra Postgres, inscribir a alguien con su
        curso —que es lo que pide el formulario, con «601» de ejemplo— era una
        violación de clave ajena. Inscribir sin curso no fallaba, porque una
        clave ajena compuesta con un lado nulo no se comprueba, y por eso el
        camino roto era justo el que usa el colegio.

        La división nace con el curso como nombre. La jerarquía de
        `CatalogoDeDivisiones` sigue sin usarse: darle padres es otra pantalla,
        no un requisito para poder inscribir.
        """
        if not participante.division_id:
            return
        self._db.table("divisiones").upsert(
            {
                "id": participante.division_id,
                "competicion_id": participante.competicion_id,
                "nombre": participante.division_id,
            },
            on_conflict="competicion_id,id",
        ).execute()

    def eliminar(self, participante_id: ParticipanteId) -> None:
        self._db.table("participantes").delete().eq("id", participante_id).execute()

    def _miembros(self, participantes: Sequence[str]) -> list[dict]:
        if not participantes:
            return []
        return self._filas(
            self._db.table("miembros")
            .select("*")
            .in_("participante_id", list(participantes))
            .execute()
        )


class EnfrentamientosSupabase(_Base):
    def obtener(self, enfrentamiento_id: EnfrentamientoId) -> Enfrentamiento | None:
        fila = self._una(
            self._db.table("enfrentamientos")
            .select("*")
            .eq("id", enfrentamiento_id)
            .execute()
        )
        if fila is None:
            return None
        marcadores = self._marcadores([enfrentamiento_id])
        return m.enfrentamiento_desde_fila(fila, marcadores.get(enfrentamiento_id))

    def de_fase(self, fase_id: FaseId) -> tuple[Enfrentamiento, ...]:
        filas = self._filas(
            self._db.table("enfrentamientos").select("*").eq("fase_id", fase_id).execute()
        )
        if not filas:
            return ()
        marcadores = self._marcadores([f["id"] for f in filas])
        return tuple(
            m.enfrentamiento_desde_fila(f, marcadores.get(f["id"])) for f in filas
        )

    def guardar(self, enfrentamiento: Enfrentamiento) -> None:
        self.guardar_muchos([enfrentamiento])

    def guardar_muchos(self, enfrentamientos: Sequence[Enfrentamiento]) -> None:
        """Una escritura para todo el lote, no una por enfrentamiento.

        El dominio admite un enfrentamiento sin fase ni competición —el motor de
        clasificación y el de brackets trabajan con partidos sin saber dónde se
        guardan—, pero persistirlo sí las exige. Se comprueba aquí para que el
        error diga qué falta en vez de llegar como una violación de restricción.
        """
        if not enfrentamientos:
            return
        huerfanos = [
            e.id
            for e in enfrentamientos
            if not e.competicion_id or not e.fase_id
        ]
        if huerfanos:
            raise ValueError(
                "No se puede guardar un enfrentamiento sin competición ni fase: "
                + ", ".join(map(repr, huerfanos))
            )
        self._db.table("enfrentamientos").upsert(
            [m.enfrentamiento_a_fila(e) for e in enfrentamientos], on_conflict="id"
        ).execute()

        marcadores = [
            fila
            for fila in (m.marcador_a_fila(e) for e in enfrentamientos)
            if fila is not None
        ]
        if marcadores:
            self._db.table("marcadores").upsert(
                marcadores, on_conflict="enfrentamiento_id"
            ).execute()

        # Un enfrentamiento que perdió su marcador —una casilla del cuadro que
        # se recalculó— tiene que perderlo también en la base.
        sin_marcador = [e.id for e in enfrentamientos if e.marcador is None]
        if sin_marcador:
            self._db.table("marcadores").delete().in_(
                "enfrentamiento_id", sin_marcador
            ).execute()

    def eliminar_de_fase(self, fase_id: FaseId) -> None:
        self._db.table("enfrentamientos").delete().eq("fase_id", fase_id).execute()

    def _marcadores(self, ids: Sequence[str]) -> dict[str, dict]:
        if not ids:
            return {}
        filas = self._filas(
            self._db.table("marcadores")
            .select("*")
            .in_("enfrentamiento_id", list(ids))
            .execute()
        )
        return {f["enfrentamiento_id"]: f for f in filas}


class ConcesionesSupabase(_Base):
    def de_usuario(self, usuario_id: str) -> tuple[Concesion, ...]:
        """Concesiones de un usuario. Sin concesiones si el id no es un UUID.

        `concesiones.usuario_id` es de tipo `uuid`: preguntar por un id que no
        lo sea no devuelve cero filas, sino un error de PostgREST que sube por
        toda la pila. Quien no existe no tiene concesiones, y esa es la
        respuesta correcta —no una excepción.
        """
        if not _es_uuid(usuario_id):
            return ()
        filas = self._filas(
            self._db.table("concesiones").select("*").eq("usuario_id", usuario_id).execute()
        )
        return tuple(_concesion_desde_fila(f) for f in filas)

    def de_competicion(self, competicion_id: CompeticionId) -> tuple[Concesion, ...]:
        filas = self._filas(
            self._db.table("concesiones")
            .select("*")
            .eq("competicion_id", competicion_id)
            .execute()
        )
        return tuple(_concesion_desde_fila(f) for f in filas)

    def otorgar(self, concesion: Concesion) -> None:
        self._db.table("concesiones").upsert(
            {
                "usuario_id": concesion.usuario_id,
                "competicion_id": concesion.competicion_id,
                "rol": concesion.rol.value,
            },
            on_conflict="usuario_id,competicion_id",
        ).execute()

    def revocar(
        self, usuario_id: str, competicion_id: CompeticionId | None = None
    ) -> None:
        consulta = self._db.table("concesiones").delete().eq("usuario_id", usuario_id)
        if competicion_id is None:
            consulta = consulta.is_("competicion_id", "null")
        else:
            consulta = consulta.eq("competicion_id", competicion_id)
        consulta.execute()


def _es_uuid(valor: str) -> bool:
    try:
        _uuid.UUID(str(valor))
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def _concesion_desde_fila(fila: dict) -> Concesion:
    return Concesion(
        usuario_id=str(fila["usuario_id"]),
        rol=Rol(fila["rol"]),
        competicion_id=fila.get("competicion_id"),
    )
