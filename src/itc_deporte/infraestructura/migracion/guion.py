"""Guion de migración. Se ejecuta a mano, una vez.

    python -m itc_deporte.infraestructura.migracion.guion ensayo
    python -m itc_deporte.infraestructura.migracion.guion escribir

**`ensayo` no escribe nada.** Lee las tablas viejas, traduce y muestra el reporte
de conflictos. Se puede repetir cuantas veces haga falta, y hay que repetirlo
hasta que el reporte esté limpio o hasta que cada conflicto que quede sea uno que
se haya decidido conscientemente dejar atrás.

`escribir` hace lo mismo y además vuelca el resultado. Se niega a continuar si
hay conflictos, salvo que se le pase `--forzar`.

Antes de `escribir`: **respaldo completo de la base**. Este guion no lo hace por
ti y no puede deshacer lo que escribe.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from ..plantillas import cargar_semillas
from ..supabase.repositorios import (
    CompeticionesSupabase,
    EnfrentamientosSupabase,
    ParticipantesSupabase,
)
from .traductor import Reporte, traducir

TABLAS_LEGADO = ("equipos", "jugadores", "partidos", "llaves")


def conectar() -> Any:
    url, clave = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not clave:
        raise SystemExit(
            "Faltan SUPABASE_URL y SUPABASE_KEY en el entorno.\n"
            "No se leen de .streamlit/secrets.toml a propósito: esto se ejecuta "
            "a mano y conviene ser explícito sobre contra qué base."
        )
    import supabase

    return supabase.create_client(url, clave)


def leer_legado(cliente) -> dict[str, list[dict]]:
    datos = {}
    for tabla in TABLAS_LEGADO:
        respuesta = cliente.table(tabla).select("*").execute()
        datos[tabla] = list(getattr(respuesta, "data", None) or [])
        print(f"  {tabla}: {len(datos[tabla])} filas")
    return datos


def mostrar(reporte: Reporte) -> None:
    print()
    print(f"Traducción: {reporte.resumen()}")
    if not reporte.hay_conflictos:
        print("Sin conflictos.")
        return

    print()
    print(f"── {len(reporte.conflictos)} conflictos ──")
    por_motivo: dict[str, list] = {}
    for conflicto in reporte.conflictos:
        por_motivo.setdefault(conflicto.motivo, []).append(conflicto)
    for motivo, casos in sorted(por_motivo.items(), key=lambda x: -len(x[1])):
        print(f"\n{motivo} ({len(casos)}):")
        for conflicto in casos[:20]:
            print(f"  {conflicto}")
        if len(casos) > 20:
            print(f"  … y {len(casos) - 20} más")
    print()
    print("Estas filas NO se migran. Hay que resolverlas a mano o aceptarlas.")


def escribir(cliente, reporte: Reporte) -> None:
    competiciones = CompeticionesSupabase(cliente)
    participantes = ParticipantesSupabase(cliente)
    enfrentamientos = EnfrentamientosSupabase(cliente)

    print("\nSubiendo las plantillas semilla…")
    semillas = cargar_semillas()
    cliente.table("plantillas").upsert(
        [
            {
                "id": p.id,
                "nombre": p.nombre,
                "descripcion": p.descripcion,
                "definicion": {},  # se rellena al serializar plantillas completas
                "es_semilla": True,
            }
            for p in semillas
        ],
        on_conflict="id",
    ).execute()
    print(f"  {len(semillas)} plantillas")

    print("Escribiendo divisiones…")
    for competicion in reporte.competiciones:
        cliente.table("divisiones").upsert(
            [
                {
                    "id": d.id,
                    "competicion_id": competicion.id,
                    "nombre": d.nombre,
                    "padre_id": d.padre_id,
                }
                for d in reporte.divisiones
            ],
            on_conflict="competicion_id,id",
        ).execute()

    print("Escribiendo competiciones…")
    for competicion in reporte.competiciones:
        competiciones.guardar(competicion)
    print(f"  {len(reporte.competiciones)}")

    print("Escribiendo participantes…")
    for participante in reporte.participantes:
        participantes.guardar(participante)
    print(f"  {len(reporte.participantes)}")

    print("Escribiendo enfrentamientos…")
    enfrentamientos.guardar_muchos(reporte.enfrentamientos)
    print(f"  {len(reporte.enfrentamientos)}")

    print("\nHecho. Las tablas viejas siguen intactas: compruébalo todo antes de")
    print("borrarlas, y no las borres hasta que la aplicación funcione sobre las")
    print("nuevas.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modo", choices=["ensayo", "escribir"])
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="escribir aunque haya conflictos (las filas en conflicto se pierden)",
    )
    args = parser.parse_args(argv)

    cliente = conectar()
    print("Leyendo las tablas heredadas…")
    datos = leer_legado(cliente)

    reporte = traducir(
        equipos=datos["equipos"],
        jugadores=datos["jugadores"],
        partidos=datos["partidos"],
        llaves=datos["llaves"],
    )
    mostrar(reporte)

    if args.modo == "ensayo":
        print("\nEnsayo: no se ha escrito nada.")
        return 0

    if reporte.hay_conflictos and not args.forzar:
        print(
            "\nNo se escribe nada porque hay conflictos sin resolver.\n"
            "Resuélvelos en las tablas viejas y repite el ensayo, o vuelve a\n"
            "ejecutar con --forzar si aceptas perder esas filas."
        )
        return 1

    if reporte.hay_conflictos:
        print(f"\n--forzar: se pierden {len(reporte.conflictos)} filas.")

    respuesta = input("\n¿Respaldo hecho? Escribe 'si' para continuar: ")
    if respuesta.strip().lower() != "si":
        print("Cancelado.")
        return 1

    escribir(cliente, reporte)
    return 0


if __name__ == "__main__":
    sys.exit(main())
