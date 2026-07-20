"""Los identificadores del dominio, reunidos.

Estaban repartidos por el módulo donde nació cada entidad, lo que impedía que
dos entidades se referenciaran sin crear un ciclo de imports. Aquí no dependen
de nada, así que cualquiera puede usarlos.

Son `NewType` sobre `str`: en tiempo de ejecución no cuestan nada, pero un
verificador de tipos distingue un `ParticipanteId` de un `FaseId` y no deja
pasarlos cambiados.
"""

from __future__ import annotations

from typing import NewType

CompeticionId = NewType("CompeticionId", str)
DivisionId = NewType("DivisionId", str)
EnfrentamientoId = NewType("EnfrentamientoId", str)
FaseId = NewType("FaseId", str)
GrupoId = NewType("GrupoId", str)
MiembroId = NewType("MiembroId", str)
ParticipanteId = NewType("ParticipanteId", str)
