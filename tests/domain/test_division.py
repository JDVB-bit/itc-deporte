from __future__ import annotations

import pytest

from itc_deporte.domain.division import CatalogoDeDivisiones, Division
from itc_deporte.domain.errores import ErrorDeDominio


@pytest.fixture
def catalogo_itc() -> CatalogoDeDivisiones:
    """Un recorte de la configuración real del ITC: categorías con cursos."""
    return CatalogoDeDivisiones(
        [
            Division("PRIMERA", "Primera"),
            Division("601", "601", padre_id="PRIMERA"),
            Division("602", "602", padre_id="PRIMERA"),
            Division("SEGUNDA", "Segunda"),
            Division("801", "801", padre_id="SEGUNDA"),
        ]
    )


class TestDivision:
    def test_una_division_sin_padre_es_raiz(self):
        assert Division("PRIMERA", "Primera").es_raiz

    def test_una_division_con_padre_no_es_raiz(self):
        assert not Division("601", "601", padre_id="PRIMERA").es_raiz

    def test_la_identidad_es_el_id(self):
        assert Division("601", "Sexto Uno") == Division("601", "601")
        assert Division("601", "601") != Division("602", "602")

    def test_rechaza_ser_su_propio_padre(self):
        with pytest.raises(ErrorDeDominio):
            Division("601", "601", padre_id="601")

    def test_rechaza_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Division("", "601")

    def test_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Division("601", "   ")

    def test_no_se_compara_con_otros_tipos(self):
        assert Division("601", "601") != "601"


class TestConstruccionDelCatalogo:
    def test_un_catalogo_vacio_es_valido(self):
        """Una competición nueva todavía no tiene divisiones."""
        assert len(CatalogoDeDivisiones()) == 0

    def test_rechaza_divisiones_duplicadas(self):
        with pytest.raises(ErrorDeDominio):
            CatalogoDeDivisiones([Division("601", "601"), Division("601", "601 bis")])

    def test_rechaza_un_padre_inexistente(self):
        with pytest.raises(ErrorDeDominio):
            CatalogoDeDivisiones([Division("601", "601", padre_id="PRIMERA")])

    def test_rechaza_un_ciclo(self):
        with pytest.raises(ErrorDeDominio):
            CatalogoDeDivisiones(
                [
                    Division("a", "A", padre_id="b"),
                    Division("b", "B", padre_id="a"),
                ]
            )

    def test_rechaza_un_ciclo_largo(self):
        with pytest.raises(ErrorDeDominio):
            CatalogoDeDivisiones(
                [
                    Division("a", "A", padre_id="c"),
                    Division("b", "B", padre_id="a"),
                    Division("c", "C", padre_id="b"),
                ]
            )


class TestConsultas:
    def test_longitud_e_iteracion(self, catalogo_itc):
        assert len(catalogo_itc) == 5
        assert {d.id for d in catalogo_itc} == {
            "PRIMERA",
            "601",
            "602",
            "SEGUNDA",
            "801",
        }

    def test_contiene(self, catalogo_itc):
        assert "601" in catalogo_itc
        assert "999" not in catalogo_itc

    def test_obtener(self, catalogo_itc):
        assert catalogo_itc.obtener("601").nombre == "601"
        assert catalogo_itc.obtener("999") is None

    def test_raices_son_las_categorias(self, catalogo_itc):
        assert {d.id for d in catalogo_itc.raices()} == {"PRIMERA", "SEGUNDA"}

    def test_hojas_son_los_cursos(self, catalogo_itc):
        """Donde de hecho se inscribe a los participantes."""
        assert {d.id for d in catalogo_itc.hojas()} == {"601", "602", "801"}

    def test_hijas(self, catalogo_itc):
        assert {d.id for d in catalogo_itc.hijas("PRIMERA")} == {"601", "602"}

    def test_hijas_de_una_hoja_es_vacio(self, catalogo_itc):
        assert catalogo_itc.hijas("601") == ()

    def test_ancestros(self, catalogo_itc):
        assert [d.id for d in catalogo_itc.ancestros("601")] == ["PRIMERA"]

    def test_ancestros_de_una_raiz_es_vacio(self, catalogo_itc):
        assert catalogo_itc.ancestros("PRIMERA") == ()

    def test_ancestros_de_una_division_inexistente_es_vacio(self, catalogo_itc):
        assert catalogo_itc.ancestros("999") == ()

    def test_descendientes(self, catalogo_itc):
        assert {d.id for d in catalogo_itc.descendientes("PRIMERA")} == {"601", "602"}

    def test_es_descendiente_de(self, catalogo_itc):
        assert catalogo_itc.es_descendiente_de("601", "PRIMERA")
        assert not catalogo_itc.es_descendiente_de("601", "SEGUNDA")

    def test_una_division_no_es_descendiente_de_si_misma(self, catalogo_itc):
        assert not catalogo_itc.es_descendiente_de("601", "601")


class TestJerarquiaProfunda:
    """La jerarquía no está limitada a dos niveles: sede > categoría > curso."""

    @pytest.fixture
    def catalogo(self) -> CatalogoDeDivisiones:
        return CatalogoDeDivisiones(
            [
                Division("NORTE", "Sede Norte"),
                Division("PRIMERA", "Primera", padre_id="NORTE"),
                Division("601", "601", padre_id="PRIMERA"),
            ]
        )

    def test_ancestros_recorre_toda_la_cadena(self, catalogo):
        assert [d.id for d in catalogo.ancestros("601")] == ["PRIMERA", "NORTE"]

    def test_descendientes_baja_todos_los_niveles(self, catalogo):
        assert {d.id for d in catalogo.descendientes("NORTE")} == {"PRIMERA", "601"}

    def test_es_descendiente_de_un_ancestro_lejano(self, catalogo):
        assert catalogo.es_descendiente_de("601", "NORTE")

    def test_la_unica_hoja_es_el_curso(self, catalogo):
        assert [d.id for d in catalogo.hojas()] == ["601"]


class TestIdentidadIndexable:
    def test_las_divisiones_se_pueden_usar_como_clave(self):
        indice = {Division("601", "601"): "PRIMERA"}
        assert indice[Division("601", "Sexto Uno", padre_id="PRIMERA")] == "PRIMERA"
