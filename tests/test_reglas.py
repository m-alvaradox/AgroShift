"""Pruebas del catálogo, las estrategias y las reglas de P4."""

import csv
import tempfile
import unittest
from pathlib import Path

from src.reglas import (
    cargar_catalogo,
    cargar_reglas,
    evaluar_reglas,
    obtener_estrategias,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOGO_PATH = ROOT / "data" / "cultivos.csv"


class TestCatalogoCultivos(unittest.TestCase):
    def test_carga_los_tres_cultivos_y_tipos(self):
        catalogo = cargar_catalogo(CATALOGO_PATH)

        self.assertEqual(
            set(catalogo),
            {"arroz", "soya", "maiz_duro_amarillo"},
        )
        self.assertEqual(catalogo["arroz"]["ciclo_dias"], 115)
        self.assertIs(catalogo["arroz"]["tolera_inundacion"], True)
        self.assertIs(catalogo["soya"]["tolera_inundacion"], False)

    def test_prefiere_etc_y_conserva_alias_agua(self):
        catalogo = cargar_catalogo(CATALOGO_PATH)

        self.assertEqual(catalogo["soya"]["etc_min_mm"], 450)
        self.assertEqual(catalogo["soya"]["etc_max_mm"], 700)
        self.assertEqual(catalogo["soya"]["agua_min_mm"], 450)
        self.assertEqual(catalogo["soya"]["agua_max_mm"], 700)

    def test_rechaza_identificador_duplicado(self):
        contenido = (
            "cultivo,ciclo_dias,kc_ini,kc_med,kc_fin,"
            "tolera_inundacion,etc_min_mm,etc_max_mm\n"
            "arroz,115,1.05,1.20,0.75,true,450,700\n"
            "arroz,115,1.05,1.20,0.75,true,450,700\n"
        )
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "cultivos.csv"
            ruta.write_text(contenido, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "duplicado"):
                cargar_catalogo(ruta)

    def test_rechaza_alias_agua_distintos_de_etc(self):
        contenido = (
            "cultivo,ciclo_dias,kc_ini,kc_med,kc_fin,"
            "agua_min_mm,agua_max_mm,tolera_inundacion,etc_min_mm,etc_max_mm\n"
            "arroz,115,1.05,1.20,0.75,1000,1500,true,450,700\n"
        )
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "cultivos.csv"
            ruta.write_text(contenido, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "deben coincidir"):
                cargar_catalogo(ruta)

    def test_admite_contrato_antiguo_con_alias_agua(self):
        contenido = (
            "cultivo,ciclo_dias,kc_ini,kc_med,kc_fin,"
            "agua_min_mm,agua_max_mm,tolera_inundacion\n"
            "arroz,115,1.05,1.20,0.75,450,700,true\n"
        )
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "cultivos.csv"
            ruta.write_text(contenido, encoding="utf-8")
            catalogo = cargar_catalogo(ruta)

        self.assertEqual(catalogo["arroz"]["etc_min_mm"], 450)
        self.assertEqual(catalogo["arroz"]["etc_max_mm"], 700)


class TestEstrategias(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = cargar_catalogo(CATALOGO_PATH)

    def test_define_las_tres_estrategias_en_orden(self):
        estrategias = obtener_estrategias(self.catalogo)

        self.assertEqual([item["id"] for item in estrategias], ["A", "B", "C"])
        self.assertEqual(
            [paso["cultivo"] for paso in estrategias[0]["secuencia"]],
            ["arroz", "arroz"],
        )
        self.assertEqual(
            [paso["cultivo"] for paso in estrategias[1]["secuencia"]],
            ["arroz", "soya"],
        )
        self.assertEqual(
            [paso["cultivo"] for paso in estrategias[2]["secuencia"]],
            ["arroz", "soya", "maiz_duro_amarillo", "soya"],
        )

    def test_resumen_suma_dias_y_etc_por_ciclos(self):
        estrategias = {
            item["id"]: item
            for item in obtener_estrategias(self.catalogo)
        }

        self.assertEqual(estrategias["A"]["dias_totales_referencia"], 230)
        self.assertEqual(estrategias["B"]["dias_totales_referencia"], 223)
        self.assertEqual(estrategias["C"]["dias_totales_referencia"], 451)
        self.assertEqual(
            estrategias["B"]["etc_acumulada_referencia_mm"],
            {"min": 900.0, "max": 1400.0},
        )
        self.assertEqual(
            estrategias["C"]["etc_acumulada_referencia_mm"],
            {"min": 1850.0, "max": 2700.0},
        )

    def test_rechaza_estrategia_desconocida(self):
        with self.assertRaisesRegex(ValueError, "Estrategia desconocida"):
            evaluar_reglas("D", catalogo=self.catalogo, reglas=[])


class TestReglasAgronomicas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogo = cargar_catalogo(CATALOGO_PATH)
        cls.reglas = cargar_reglas()

    @staticmethod
    def por_id(resultados):
        return {resultado["id"]: resultado for resultado in resultados}

    def test_estrategia_a_advierte_repeticion_de_arroz(self):
        resultados = self.por_id(
            evaluar_reglas(
                "A",
                catalogo=self.catalogo,
                reglas=self.reglas,
            )
        )

        self.assertEqual(resultados["AGR-001"]["estado"], "advertencia")
        self.assertEqual(resultados["AGR-005"]["estado"], "nota_tecnica")

    def test_estrategia_b_sin_datos_de_zona_pide_validacion(self):
        resultados = self.por_id(
            evaluar_reglas(
                "B",
                catalogo=self.catalogo,
                reglas=self.reglas,
            )
        )

        self.assertEqual(resultados["AGR-002"]["estado"], "informacion")
        self.assertEqual(resultados["AGR-003"]["estado"], "pendiente_validacion")
        self.assertEqual(resultados["AGR-004"]["estado"], "pendiente_validacion")

    def test_estrategia_b_con_drenaje_apto_y_bajo_anegamiento(self):
        resultados = self.por_id(
            evaluar_reglas(
                "B",
                contexto={
                    "drenaje": "bien_drenado",
                    "riesgo_anegamiento": False,
                },
                catalogo=self.catalogo,
                reglas=self.reglas,
            )
        )

        self.assertEqual(resultados["AGR-003"]["estado"], "condicion_favorable")
        self.assertEqual(resultados["AGR-004"]["estado"], "condicion_favorable")

    def test_estrategia_c_con_drenaje_deficiente_genera_alertas(self):
        resultados = self.por_id(
            evaluar_reglas(
                "C",
                contexto={
                    "drenaje": "deficiente",
                    "riesgo_anegamiento": True,
                },
                catalogo=self.catalogo,
                reglas=self.reglas,
            )
        )

        self.assertEqual(resultados["AGR-003"]["estado"], "alerta")
        self.assertEqual(resultados["AGR-004"]["estado"], "alerta")

    def test_categorias_desconocidas_no_se_consideran_aptas(self):
        resultados = self.por_id(
            evaluar_reglas(
                "B",
                contexto={
                    "drenaje": "intermedio",
                    "riesgo_anegamiento": "moderado",
                },
                catalogo=self.catalogo,
                reglas=self.reglas,
            )
        )

        self.assertEqual(resultados["AGR-003"]["estado"], "pendiente_validacion")
        self.assertEqual(resultados["AGR-004"]["estado"], "pendiente_validacion")

    def test_regla_especifica_solo_se_aplica_a_su_zona(self):
        regla = {
            "id": "TEST-ZONA",
            "texto_campo": "Regla exclusiva de Z-1.",
            "condicion": {
                "tipo": "cultivo_incluido",
                "cultivos": ["arroz"],
                "estado": "informacion",
            },
            "evidencia": "Prueba unitaria.",
            "zona_id": "Z-1",
        }

        fuera_de_zona = evaluar_reglas(
            "A",
            contexto={"zona_id": "Z-2"},
            catalogo=self.catalogo,
            reglas=[regla],
        )
        dentro_de_zona = evaluar_reglas(
            "A",
            contexto={"zona_id": "Z-1"},
            catalogo=self.catalogo,
            reglas=[regla],
        )

        self.assertEqual(fuera_de_zona, [])
        self.assertEqual([item["id"] for item in dentro_de_zona], ["TEST-ZONA"])


if __name__ == "__main__":
    unittest.main()
