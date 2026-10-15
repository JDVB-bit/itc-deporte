"""Añade el campo `torneo` (Intercursos / Intercolegiados) a las competiciones.

Uso, desde la raíz del repositorio (donde está app.py):

    venv\\Scripts\\python aplicar_torneo.py        (Windows)
    python aplicar_torneo.py                        (otros)

Cambia 5 archivos con reemplazos exactos. Si alguno no encaja tal cual —porque
el archivo cambió— no toca NINGUNO y dice cuál falló. Es seguro correrlo dos
veces: lo que ya está aplicado se salta.
"""

from pathlib import Path
import sys

SQL_COLUMNA = (
    "               check (estado in ('Borrador', 'En curso', 'Finalizada')),\n"
)
SQL_COLUMNA_NUEVA = SQL_COLUMNA + (
    "    -- Qué torneo es: Intercursos (entre los cursos de la escuela) o\n"
    "    -- Intercolegiados (la escuela contra otros colegios).\n"
    "    torneo     text not null default 'intercursos'\n"
    "               check (torneo in ('intercursos', 'intercolegiados')),\n"
)

CAMBIOS = {
    "src/itc_deporte/domain/competicion.py": [
        (
            'class EstadoCompeticion(Enum):\n'
            '    BORRADOR = "Borrador"\n'
            '    EN_CURSO = "En curso"\n'
            '    FINALIZADA = "Finalizada"\n',
            'class EstadoCompeticion(Enum):\n'
            '    BORRADOR = "Borrador"\n'
            '    EN_CURSO = "En curso"\n'
            '    FINALIZADA = "Finalizada"\n'
            '\n\n'
            'class Torneo(Enum):\n'
            '    """A qué torneo pertenece una competición.\n'
            '\n'
            '    Intercursos es entre los cursos de la escuela; Intercolegiados, la\n'
            '    escuela contra otros colegios. Los valores son los que se guardan en\n'
            '    la base y los que usa la interfaz como nombre de vista.\n'
            '    """\n'
            '\n'
            '    INTERCURSOS = "intercursos"\n'
            '    INTERCOLEGIADOS = "intercolegiados"\n',
        ),
        (
            "    calendario: Calendario = Calendario()\n",
            "    calendario: Calendario = Calendario()\n"
            "    #: Va al final y con valor por defecto para no romper a quien construye\n"
            "    #: una competición sin él: todo lo que ya existía era de Intercursos.\n"
            "    torneo: Torneo = Torneo.INTERCURSOS\n",
        ),
    ],
    "src/itc_deporte/infraestructura/supabase/mapeadores.py": [
        (
            "    ReglasDeCompeticion,\n)\nfrom ...domain.division import Division",
            "    ReglasDeCompeticion,\n    Torneo,\n)\nfrom ...domain.division import Division",
        ),
        (
            '        "estado": competicion.estado.value,\n        "reglas": {',
            '        "estado": competicion.estado.value,\n'
            '        "torneo": competicion.torneo.value,\n        "reglas": {',
        ),
        (
            '        estado=EstadoCompeticion(fila.get("estado") or "Borrador"),\n'
            "        fases=fases,",
            '        estado=EstadoCompeticion(fila.get("estado") or "Borrador"),\n'
            '        torneo=Torneo(fila.get("torneo") or "intercursos"),\n'
            "        fases=fases,",
        ),
    ],
    "src/itc_deporte/infraestructura/supabase/esquema.sql": [(SQL_COLUMNA, SQL_COLUMNA_NUEVA)],
    "docs/PASO_2.sql": [(SQL_COLUMNA, SQL_COLUMNA_NUEVA)],
    "src/itc_deporte/ui/vistas.py": [
        (
            "    FaseEliminatoria,\n)\nfrom ..domain.reglas.catalogo import (",
            "    FaseEliminatoria,\n    Torneo,\n)\nfrom ..domain.reglas.catalogo import (",
        ),
        (
            '        temporada = st.text_input("Temporada", value=str(dt.date.today().year))\n',
            '        temporada = st.text_input("Temporada", value=str(dt.date.today().year))\n'
            "        # Por defecto, el torneo que se está mirando: quien crea desde\n"
            "        # Intercolegiados casi seguro quiere una de Intercolegiados.\n"
            "        torneo = st.selectbox(\n"
            '            "Torneo",\n'
            "            list(Torneo),\n"
            '            index=1 if st.session_state.get("vista") == "intercolegiados" else 0,\n'
            "            format_func=lambda t: {\n"
            '                Torneo.INTERCURSOS: "Intercursos",\n'
            '                Torneo.INTERCOLEGIADOS: "Intercolegiados",\n'
            "            }[t],\n"
            "        )\n",
        ),
        (
            "                    calendario=Calendario(dia_de_la_semana=int(dia), hora=hora),\n",
            "                    calendario=Calendario(dia_de_la_semana=int(dia), hora=hora),\n"
            "                    torneo=torneo,\n",
        ),
    ],
}


def leer(ruta: Path) -> tuple[str, bool]:
    """Texto con saltos `\\n` y si el archivo usaba `\\r\\n` (Windows)."""
    crudo = ruta.read_bytes().decode("utf-8")
    return crudo.replace("\r\n", "\n"), "\r\n" in crudo


def main() -> int:
    raiz = Path.cwd()
    nuevos: dict[Path, tuple[str, bool]] = {}
    problemas: list[str] = []

    for relativa, reemplazos in CAMBIOS.items():
        ruta = raiz / relativa
        if not ruta.is_file():
            problemas.append(f"No encuentro {relativa}. ¿Estás en la raíz del repositorio?")
            continue
        texto, crlf = leer(ruta)
        for viejo, nuevo in reemplazos:
            if nuevo in texto:
                continue  # ya aplicado
            veces = texto.count(viejo)
            if veces != 1:
                problemas.append(
                    f"{relativa}: esperaba encontrar este bloque 1 vez y lo encontré "
                    f"{veces}:\n{viejo}"
                )
                continue
            texto = texto.replace(viejo, nuevo)
        nuevos[ruta] = (texto, crlf)

    if problemas:
        print("NO SE CAMBIÓ NINGÚN ARCHIVO.\n")
        print("\n".join(problemas))
        return 1

    for ruta, (texto, crlf) in nuevos.items():
        salida = texto.replace("\n", "\r\n") if crlf else texto
        ruta.write_bytes(salida.encode("utf-8"))
        print(f"OK {ruta.relative_to(raiz)}")
    print("\nListo. Ahora sube esos archivos a GitHub (ver INSTRUCCIONES.txt).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
