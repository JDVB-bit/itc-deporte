"""El torneo al que pertenece una competición: Intercursos o Intercolegiados."""

from __future__ import annotations

from itc_deporte.domain.competicion import Competicion, Deporte, Torneo
from itc_deporte.infraestructura.supabase import ESQUEMA
from itc_deporte.infraestructura.supabase import mapeadores as m

FUTBOL = Deporte("microfutbol", "Microfútbol", "⚽")


def competicion(**cambios) -> Competicion:
    return Competicion(id="c1", nombre="Prueba", deporte=FUTBOL, **cambios)


def test_por_defecto_es_intercursos():
    """Todo lo que existía antes de este campo era de Intercursos."""
    assert competicion().torneo is Torneo.INTERCURSOS


def test_ida_y_vuelta_de_intercolegiados():
    fila = m.competicion_a_fila(competicion(torneo=Torneo.INTERCOLEGIADOS))
    assert fila["torneo"] == "intercolegiados"
    assert m.competicion_desde_fila(fila, FUTBOL).torneo is Torneo.INTERCOLEGIADOS


def test_una_fila_sin_torneo_se_lee_como_intercursos():
    """Filas guardadas antes de que existiera la columna."""
    fila = m.competicion_a_fila(competicion())
    del fila["torneo"]
    assert m.competicion_desde_fila(fila, FUTBOL).torneo is Torneo.INTERCURSOS


def test_los_valores_coinciden_con_el_esquema():
    sql = ESQUEMA.read_text(encoding="utf-8")
    assert all(f"'{t.value}'" in sql for t in Torneo)
