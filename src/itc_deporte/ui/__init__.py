"""Streamlit como adaptador delgado.

Aquí no se decide nada: se pide. Cada acción es una llamada a un servicio de
`aplicacion/`, que es quien comprueba permisos y aplica reglas. Si esta capa
desapareciera, el sistema seguiría siendo el mismo.
"""

from .composicion import Servicios, construir, ensamblar

__all__ = ["Servicios", "construir", "ensamblar"]
