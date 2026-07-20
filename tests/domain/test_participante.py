from __future__ import annotations

import pytest

from itc_deporte.domain.errores import ErrorDeDominio
from itc_deporte.domain.participante import Miembro, Participante


def participante(**cambios) -> Participante:
    base = dict(id="p1", nombre="Los Tigres", division_id="601")
    return Participante(**{**base, **cambios})


class TestIdentidad:
    def test_dos_participantes_con_el_mismo_id_son_el_mismo(self):
        assert participante(nombre="Los Tigres") == participante(nombre="Las Panteras")

    def test_dos_participantes_con_distinto_id_son_distintos(self):
        assert participante(id="p1") != participante(id="p2")

    def test_renombrar_no_cambia_la_identidad(self):
        original = participante()
        assert original.renombrado("Otro Nombre") == original

    def test_cambiar_de_division_no_cambia_la_identidad(self):
        original = participante(division_id="601")
        assert participante(division_id="702") == original

    def test_el_hash_depende_solo_del_id(self):
        """Permite usar participantes como clave sin componer strings."""
        indice = {participante(nombre="Los Tigres"): "tabla"}
        assert indice[participante(nombre="Las Panteras")] == "tabla"

    def test_un_nombre_con_parentesis_no_rompe_nada(self):
        """El nombre ya no se parsea: es un dato opaco."""
        raro = participante(nombre="Real (Madrid) vs Nadie")
        assert raro.nombre == "Real (Madrid) vs Nadie"
        assert raro == participante()

    def test_no_se_compara_con_otros_tipos(self):
        assert participante() != "p1"


class TestInvariantes:
    def test_rechaza_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            participante(id="")

    @pytest.mark.parametrize("nombre", ["", "   "])
    def test_rechaza_nombre_vacio(self, nombre):
        with pytest.raises(ErrorDeDominio):
            participante(nombre=nombre)

    def test_rechaza_miembros_con_id_repetido(self):
        repetido = (Miembro("m1", "Ana"), Miembro("m1", "Luis"))
        with pytest.raises(ErrorDeDominio):
            participante(miembros=repetido)

    def test_es_inmutable(self):
        with pytest.raises(AttributeError):
            participante().nombre = "otro"


class TestMiembros:
    def test_un_participante_sin_miembros_es_individual(self):
        """Atletismo o ajedrez: el participante es la persona."""
        assert participante().es_individual

    def test_un_participante_con_un_miembro_es_individual(self):
        assert participante(miembros=(Miembro("m1", "Ana"),)).es_individual

    def test_un_participante_con_dos_miembros_no_es_individual(self):
        equipo = participante(miembros=(Miembro("m1", "Ana"), Miembro("m2", "Luis")))
        assert not equipo.es_individual

    def test_con_miembro_devuelve_una_instancia_nueva(self):
        original = participante()
        ampliado = original.con_miembro(Miembro("m1", "Ana"))
        assert original.miembros == ()
        assert ampliado.miembros == (Miembro("m1", "Ana"),)

    def test_con_miembro_rechaza_un_id_ya_inscrito(self):
        equipo = participante(miembros=(Miembro("m1", "Ana"),))
        with pytest.raises(ErrorDeDominio):
            equipo.con_miembro(Miembro("m1", "Luis"))

    def test_sin_miembro_lo_retira(self):
        equipo = participante(miembros=(Miembro("m1", "Ana"), Miembro("m2", "Luis")))
        assert equipo.sin_miembro("m1").miembros == (Miembro("m2", "Luis"),)

    def test_sin_miembro_rechaza_a_quien_no_esta_inscrito(self):
        with pytest.raises(ErrorDeDominio):
            participante().sin_miembro("m9")

    def test_miembro_devuelve_none_si_no_existe(self):
        assert participante().miembro("m9") is None


class TestMiembro:
    def test_rechaza_nombre_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Miembro("m1", "  ")

    def test_rechaza_id_vacio(self):
        with pytest.raises(ErrorDeDominio):
            Miembro("", "Ana")

    def test_rechaza_dorsal_negativo(self):
        with pytest.raises(ErrorDeDominio):
            Miembro("m1", "Ana", dorsal=-1)

    def test_el_dorsal_es_opcional(self):
        assert Miembro("m1", "Ana").dorsal is None


class TestPertenenciaACompeticion:
    def test_un_participante_puede_no_estar_inscrito_todavia(self):
        assert participante().competicion_id is None

    def test_lleva_la_competicion_a_la_que_pertenece(self):
        inscrito = participante(competicion_id="c1")
        assert inscrito.competicion_id == "c1"

    def test_la_competicion_no_cambia_la_identidad(self):
        assert participante(competicion_id="c1") == participante(competicion_id="c2")

    def test_el_mismo_nombre_en_dos_competiciones_son_participantes_distintos(self):
        una = Participante(id="p1", nombre="Los Tigres", competicion_id="c1")
        otra = Participante(id="p2", nombre="Los Tigres", competicion_id="c2")
        assert una != otra
