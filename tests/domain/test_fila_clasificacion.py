from __future__ import annotations

import pytest

from itc_deporte.domain.clasificacion import FilaClasificacion
from itc_deporte.domain.errores import ErrorDeDominio


class TestFilaClasificacion:
    def test_una_fila_nueva_esta_en_cero(self):
        fila = FilaClasificacion("p1")
        assert (fila.jugados, fila.puntos, fila.diferencia) == (0, 0, 0)

    def test_la_diferencia_se_deriva(self):
        fila = FilaClasificacion("p1", jugados=1, ganados=1, a_favor=3, en_contra=1)
        assert fila.diferencia == 2

    def test_la_diferencia_puede_ser_negativa(self):
        fila = FilaClasificacion("p1", jugados=1, perdidos=1, a_favor=0, en_contra=3)
        assert fila.diferencia == -3

    def test_rechaza_un_participante_vacio(self):
        with pytest.raises(ErrorDeDominio):
            FilaClasificacion("")

    def test_rechaza_valores_negativos(self):
        with pytest.raises(ErrorDeDominio):
            FilaClasificacion("p1", a_favor=-1)

    def test_rechaza_resultados_que_no_cuadran_con_los_jugados(self):
        """Una fila con 3 jugados y 1 ganado no dice qué pasó con los otros dos."""
        with pytest.raises(ErrorDeDominio):
            FilaClasificacion("p1", jugados=3, ganados=1)

    def test_acepta_resultados_que_cuadran(self):
        fila = FilaClasificacion("p1", jugados=3, ganados=1, empatados=1, perdidos=1)
        assert fila.jugados == 3

    def test_es_inmutable(self):
        with pytest.raises(AttributeError):
            FilaClasificacion("p1").puntos = 9
