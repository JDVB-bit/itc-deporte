"""División: el eje por el que se agrupa a los participantes.

Generaliza el "curso" que el sistema anterior tenía cableado. La jerarquía es
explícita: la categoría PRIMERA es una división que contiene a 601, 602… En otra
institución las divisiones podrían ser sedes, edades o categorías de peso, y el
motor no necesita enterarse.

Esto sustituye a `CATEGORIAS_LOCAL` y `CURSOS_VALIDOS`, dos constantes de módulo
que ataban el software a un colegio concreto.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

from .errores import ErrorDeDominio
from .participante import DivisionId


@dataclass(frozen=True, slots=True, eq=False)
class Division:
    """Entidad: la igualdad se define por `id`."""

    id: DivisionId
    nombre: str
    padre_id: DivisionId | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ErrorDeDominio("Una división necesita un id.")
        if not self.nombre.strip():
            raise ErrorDeDominio("Una división necesita un nombre no vacío.")
        if self.padre_id == self.id:
            raise ErrorDeDominio(f"La división {self.id!r} no puede ser su propio padre.")

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Division):
            return NotImplemented
        return self.id == otro.id

    def __hash__(self) -> int:
        return hash(self.id)

    @property
    def es_raiz(self) -> bool:
        return self.padre_id is None


class CatalogoDeDivisiones:
    """Conjunto de divisiones con jerarquía validada.

    Se valida al construir —ids únicos, padres existentes, sin ciclos— para que
    ninguna consulta posterior tenga que defenderse de un árbol inconsistente.
    """

    def __init__(self, divisiones: Iterable[Division] = ()) -> None:
        self._por_id: dict[DivisionId, Division] = {}
        for division in divisiones:
            if division.id in self._por_id:
                raise ErrorDeDominio(f"División duplicada: {division.id!r}")
            self._por_id[division.id] = division
        self._validar_padres()
        self._validar_sin_ciclos()

    def _validar_padres(self) -> None:
        for division in self._por_id.values():
            if division.padre_id is not None and division.padre_id not in self._por_id:
                raise ErrorDeDominio(
                    f"La división {division.id!r} referencia un padre inexistente: "
                    f"{division.padre_id!r}"
                )

    def _validar_sin_ciclos(self) -> None:
        for division in self._por_id.values():
            visitados = {division.id}
            actual = division
            while actual.padre_id is not None:
                if actual.padre_id in visitados:
                    raise ErrorDeDominio(
                        f"Ciclo en la jerarquía de divisiones en {actual.padre_id!r}"
                    )
                visitados.add(actual.padre_id)
                actual = self._por_id[actual.padre_id]

    def __len__(self) -> int:
        return len(self._por_id)

    def __iter__(self) -> Iterator[Division]:
        return iter(self._por_id.values())

    def __contains__(self, division_id: object) -> bool:
        return division_id in self._por_id

    def obtener(self, division_id: DivisionId) -> Division | None:
        return self._por_id.get(division_id)

    def raices(self) -> tuple[Division, ...]:
        return tuple(d for d in self._por_id.values() if d.es_raiz)

    def hojas(self) -> tuple[Division, ...]:
        """Divisiones sin hijas: donde de hecho se inscribe a los participantes."""
        con_hijas = {d.padre_id for d in self._por_id.values() if d.padre_id}
        return tuple(d for d in self._por_id.values() if d.id not in con_hijas)

    def hijas(self, division_id: DivisionId) -> tuple[Division, ...]:
        return tuple(d for d in self._por_id.values() if d.padre_id == division_id)

    def ancestros(self, division_id: DivisionId) -> tuple[Division, ...]:
        """Del padre hacia la raíz. Vacío si la división es raíz o no existe."""
        division = self._por_id.get(division_id)
        if division is None:
            return ()
        cadena: list[Division] = []
        while division.padre_id is not None:
            division = self._por_id[division.padre_id]
            cadena.append(division)
        return tuple(cadena)

    def descendientes(self, division_id: DivisionId) -> tuple[Division, ...]:
        """Todas las divisiones por debajo, en recorrido primero en anchura."""
        encontrados: list[Division] = []
        pendientes = list(self.hijas(division_id))
        while pendientes:
            actual = pendientes.pop(0)
            encontrados.append(actual)
            pendientes.extend(self.hijas(actual.id))
        return tuple(encontrados)

    def es_descendiente_de(
        self, division_id: DivisionId, posible_ancestro: DivisionId
    ) -> bool:
        return any(a.id == posible_ancestro for a in self.ancestros(division_id))
