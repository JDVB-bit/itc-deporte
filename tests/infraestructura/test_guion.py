"""El guion de migración, en lo que se puede probar sin base.

La conexión y la escritura necesitan Supabase. Lo que sí se comprueba aquí es lo
que más importa que no falle: que `ensayo` no escriba, que `escribir` se plante
ante un reporte con conflictos, y que el resumen de conflictos sea legible.
"""

from __future__ import annotations

import pytest

from itc_deporte.infraestructura.migracion import guion
from itc_deporte.infraestructura.migracion.traductor import Conflicto, Reporte


class ClienteFalso:
    def __init__(self, datos=None):
        self.datos = datos or {t: [] for t in guion.TABLAS_LEGADO}
        self.escrituras = []

    def table(self, nombre):
        return _Tabla(self, nombre)


class _Tabla:
    def __init__(self, cliente, nombre):
        self.cliente, self.nombre = cliente, nombre

    def select(self, *_):
        return self

    def upsert(self, filas, **_):
        self.cliente.escrituras.append((self.nombre, filas))
        return self

    def execute(self):
        return type("R", (), {"data": self.cliente.datos.get(self.nombre, [])})()


@pytest.fixture
def credenciales(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://falso.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "clave-falsa")


@pytest.fixture
def cliente(monkeypatch, credenciales):
    falso = ClienteFalso(
        {
            "equipos": [
                dict(id=1, categoria="PRIMERA", deporte="Microfutbol",
                     curso="601", nombre="Los Tigres"),
                dict(id=2, categoria="PRIMERA", deporte="Microfutbol",
                     curso="602", nombre="Las Panteras"),
            ],
            "jugadores": [],
            "partidos": [],
            "llaves": [],
        }
    )
    monkeypatch.setattr(guion, "conectar", lambda: falso)
    return falso


class TestConectar:
    def test_sin_credenciales_se_planta_con_un_mensaje_util(self, monkeypatch):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)
        with pytest.raises(SystemExit, match="SUPABASE_URL"):
            guion.conectar()


class TestEnsayo:
    def test_no_escribe_nada(self, cliente, capsys):
        assert guion.main(["ensayo"]) == 0
        assert cliente.escrituras == []

    def test_dice_que_no_escribio(self, cliente, capsys):
        guion.main(["ensayo"])
        assert "no se ha escrito nada" in capsys.readouterr().out

    def test_muestra_el_resumen(self, cliente, capsys):
        guion.main(["ensayo"])
        assert "2 participantes" in capsys.readouterr().out


class TestEscribirSeNiegaConConflictos:
    @pytest.fixture
    def con_conflictos(self, monkeypatch, credenciales):
        falso = ClienteFalso(
            {
                "equipos": [
                    dict(id=1, categoria="PRIMERA", deporte="Microfutbol",
                         curso="999", nombre="Curso malo"),
                ],
                "jugadores": [], "partidos": [], "llaves": [],
            }
        )
        monkeypatch.setattr(guion, "conectar", lambda: falso)
        return falso

    def test_no_escribe(self, con_conflictos, capsys):
        assert guion.main(["escribir"]) == 1
        assert con_conflictos.escrituras == []

    def test_explica_por_qué(self, con_conflictos, capsys):
        guion.main(["escribir"])
        salida = capsys.readouterr().out
        assert "conflictos sin resolver" in salida
        assert "--forzar" in salida


class TestReporteLegible:
    def test_agrupa_los_conflictos_por_motivo(self, capsys):
        reporte = Reporte()
        reporte.conflictos = [
            Conflicto("equipos", 1, "curso inválido", "A (999)"),
            Conflicto("equipos", 2, "curso inválido", "B (998)"),
            Conflicto("partidos", 3, "no se pudo parsear", "basura"),
        ]
        guion.mostrar(reporte)
        salida = capsys.readouterr().out
        assert "curso inválido (2)" in salida
        assert "no se pudo parsear (1)" in salida

    def test_recorta_las_listas_largas(self, capsys):
        reporte = Reporte()
        reporte.conflictos = [
            Conflicto("equipos", i, "curso inválido", f"E{i}") for i in range(30)
        ]
        guion.mostrar(reporte)
        assert "y 10 más" in capsys.readouterr().out

    def test_un_reporte_limpio_lo_dice(self, capsys):
        guion.mostrar(Reporte())
        assert "Sin conflictos" in capsys.readouterr().out
