"""Ajusta las dos pruebas de interfaz existentes a la nueva portada.

Antes la aplicación abría directamente en la competición. Ahora abre en la
portada, así que esas pruebas tienen que pedir la vista `intercursos`.

Uso, desde la raíz del repositorio:    python parche_tests.py
Es seguro correrlo dos veces: si ya está aplicado, no cambia nada.
"""
from pathlib import Path

ARRANQUE = '    app = AppTest.from_file("app.py", default_timeout=60).run()\n'
NUEVO = (
    '    app = AppTest.from_file("app.py", default_timeout=60)\n'
    '    app.session_state["vista"] = "intercursos"\n'
    "    app = app.run()\n"
)
ARCHIVOS = {
    "tests/ui/test_app.py": ARRANQUE + "    if papel:\n",
    "tests/ui/test_administracion.py": ARRANQUE + "    if como is None:\n",
}

for ruta, viejo in ARCHIVOS.items():
    archivo = Path(ruta)
    texto = archivo.read_text(encoding="utf-8")
    if 'session_state["vista"]' in texto:
        print(f"= {ruta}: ya estaba aplicado")
        continue
    if viejo not in texto:
        raise SystemExit(f"No encontré el bloque esperado en {ruta}. Edítalo a mano (ver instrucciones).")
    archivo.write_text(texto.replace(viejo, viejo.replace(ARRANQUE, NUEVO)), encoding="utf-8")
    print(f"✔ {ruta}: parcheado")
