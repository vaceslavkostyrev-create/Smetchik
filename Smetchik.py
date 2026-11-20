# -*- coding: utf-8 -*-
"""Сметчик: веб-версия на Streamlit.

Запуск: streamlit run app.py
"""

import math
import streamlit as st

# ─────────────────────────────────────────────────────────────
# ЛОГИКА РАСЧЕТА (взята из вашего Tkinter-приложения без изменений)
# ─────────────────────────────────────────────────────────────

class MaterialCalculator:
    """Расчёт материалов и стоимости по видам работ."""

    PLASTER_KG_PER_M2_PER_MM = 1.3
    PUTTY_START_KG_PER_M2_PER_MM = 1.2
    PUTTY_FINISH_KG_PER_M2_PER_MM = 0.8
    PUTTY_START_LAYER_MM = 3.0
    PUTTY_FINISH_LAYER_MM = 1.0
    PAINT_L_PER_M2_PER_COAT = 0.15
    STRETCH_CEIL_WASTE = 1.07
    PROFILE_DOWEL_PER_M = 1 / 0.35
    TILE_WASTE = 1.10
    TILE_GLUE_KG_PER_M2 = 4.5

    PLASTER_BAG_KG = 30.0
    PUTTY_BAG_KG = 20.0
    PAINT_CAN_L = 5.0
    TILE_GLUE_BAG_KG = 25.0

    DEFAULT_PRICES = {
        "plaster_bag": 450.0,
        "putty_bag": 500.0,
        "paint_liter": 350.0,
        "stretch_m2": 400.0,
        "profile_pm": 150.0,
        "tile_m2": 800.0,
        "tile_glue_bag": 400.0,
        "spot_light": 600.0,
    }

    def __init__(self, prices: dict = None):
        self.prices = dict(self.DEFAULT_PRICES)
        if prices:
            self.prices.update(prices)

    def base_areas(self, length, width, height, openings_area=0.0):
        perimeter = 2.0 * (length + width)
        wall_area = max(0.0, perimeter * height - openings_area)
        ceiling_area = length * width
        return {
            "perimeter": round(perimeter, 1),
            "wall_area": round(wall_area, 1),
            "ceiling_area": round(ceiling_area, 1),
            "floor_area": round(ceiling_area, 1),
        }

    @staticmethod
    def _fmt_kg(quantity, bag_kg, price_per_bag, pack_label, name):
        packs = math.ceil(round(quantity / bag_kg, 4))
        return {
            "name": name, "qty": round(quantity, 1), "unit": "кг",
            "packs": packs, "pack_label": pack_label,
            "price": round(packs * price_per_bag, 0),
        }

    def calc_plaster(self, area, thickness_mm):
        kg = area * thickness_mm * self.PLASTER_KG_PER_M2_PER_MM
        mat = self._fmt_kg(kg, self.PLASTER_BAG_KG, self.prices["plaster_bag"], "меш. 30 кг", "Смесь штукатурная")
        return {"work": "Штукатурка стен", "area": round(area, 1), "detail": f"слой {thickness_mm:g} мм", "materials": [mat], "total": mat["price"]}

    def calc_putty(self, area, kind):
        if kind == "Стартовая":
            layer, rate, name = self.PUTTY_START_LAYER_MM, self.PUTTY_START_KG_PER_M2_PER_MM, "Шпаклёвка стартовая"
        else:
            layer, rate, name = self.PUTTY_FINISH_LAYER_MM, self.PUTTY_FINISH_KG_PER_M2_PER_MM, "Шпаклёвка финишная"
        kg = area * layer * rate
        mat = self._fmt_kg(kg, self.PUTTY_BAG_KG, self.prices["putty_bag"], "меш. 20 кг", name)
        return {"work": f"Шпаклёвка стен ({kind.lower()})", "area": round(area, 1), "detail": f"слой {layer:g} мм", "materials": [mat], "total": mat["price"]}

    def calc_painting(self, wall_area, ceiling_area, surfaces, coats):
        if surfaces == "Стены": area = wall_area
        elif surfaces == "Потолок": area = ceiling_area
        else: area = wall_area + ceiling_area
        liters = area * coats * self.PAINT_L_PER_M2_PER_COAT
        cans = math.ceil(round(liters / self.PAINT_CAN_L, 4))
        mat = {"name": "Краска", "qty": round(liters, 1), "unit": "л", "packs": cans, "pack_label": "банк. 5 л", "price": round(cans * self.prices["paint_liter"] * self.PAINT_CAN_L, 0)}
        return {"work": f"Покраска ({surfaces.lower()}, {coats} слоя)", "area": round(area, 1), "detail": f"{coats} слоя", "materials": [mat], "total": mat["price"]}

    def calc_stretch_ceiling(self, ceiling_area, perimeter, spot_count):
        cloth_m2 = round(ceiling_area * self.STRETCH_CEIL_WASTE, 1)
        price_cloth = round(cloth_m2 * self.prices["stretch_m2"], 0)
        profile_pm = math.ceil(perimeter)
        price_profile = round(profile_pm * self.prices["profile_pm"], 0)
        dowels = math.ceil(perimeter * self.PROFILE_DOWEL_PER_M)
        materials = [
            {"name": "Полотно натяжное", "qty": cloth_m2, "unit": "м²", "packs": None, "pack_label": "", "price": price_cloth},
            {"name": "Профиль ПВХ", "qty": float(profile_pm), "unit": "п.м", "packs": None, "pack_label": "", "price": price_profile},
            {"name": "Дюбели для профиля", "qty": float(dowels), "unit": "шт", "packs": None, "pack_label": "", "price": 0.0},
        ]
        if spot_count > 0:
            materials.append({"name": "Светильник (точечный)", "qty": float(spot_count), "unit": "шт", "packs": spot_count, "pack_label": "шт", "price": round(spot_count * self.prices["spot_light"], 0)})
        return {"work": "Натяжной потолок", "area": round(ceiling_area, 1), "detail": f"запас полотна 7 %, периметр {perimeter:g} м", "materials": materials, "total": round(sum(m["price"] for m in materials), 0)}

    def calc_tiling(self, wall_area, floor_area, surfaces):
        if surfaces == "Стены": area = wall_area
        elif surfaces == "Пол": area = floor_area
        else: area = wall_area + floor_area
        tile_m2 = round(area * self.TILE_WASTE, 1)
        price_tile = round(tile_m2 * self.prices["tile_m2"], 0)
        glue_kg = area * self.TILE_GLUE_KG_PER_M2
        glue_packs = math.ceil(round(glue_kg / self.TILE_GLUE_BAG_KG, 4))
        price_glue = round(glue_packs * self.prices["tile_glue_bag"], 0)
        materials = [
            {"name": "Плитка", "qty": tile_m2, "unit": "м²", "packs": None, "pack_label": "", "price": price_tile},
            {"name": "Клей плиточный", "qty": round(glue_kg, 1), "unit": "кг", "packs": glue_packs, "pack_label": "меш. 25 кг", "price": price_glue},
        ]
        return {"work": f"Укладка плитки ({surfaces.lower()})", "area": round(area, 1), "detail": "запас на подрезку 10 %", "materials": materials, "total": round(price_tile + price_glue, 0)}

    def full_estimate(self, params):
        areas = self.base_areas(params["length"], params["width"], params["height"], params["openings_area"])
        results = []
        wa, ca, fa, pm = areas["wall_area"], areas["ceiling_area"], areas["floor_area"], areas["perimeter"]
        if params.get("plaster") is not None: results.append(self.calc_plaster(wa, params["plaster"]))
        if params.get("putty") is not None: results.append(self.calc_putty(wa, params["putty"]))
        if params.get("paint") is not None: results.append(self.calc_painting(wa, ca, *params["paint"]))
        if params.get("stretch") is not None: results.append(self.calc_stretch_ceiling(ca, pm, params["stretch"]))
        if params.get("tiling") is not None: results.append(self.calc_tiling(wa, fa, params["tiling"]))
        return areas, results

    @staticmethod
    def format_estimate(areas, results):
        lines = ["=" * 40, "  СМЕТА", "=" * 40]
        lines.append(f"Периметр комнаты: {areas['perimeter']:g} м")
        lines.append(f"Площадь стен: {areas['wall_area']:g} м²")
        lines.append(f"Площадь потолка: {areas['ceiling_area']:g} м²")
        lines.append(f"Площадь пола: {areas['floor_area']:g} м²\n")

        grand_total = 0.0
        for res in results:
            lines.append(f"── {res['work']} ──")
            detail = f", {res['detail']}" if res.get("detail") else ""
            lines.append(f"Площадь: {res['area']:g} м²{detail}")
            for mat in res["materials"]:
                qty = f"{mat['qty']:g} {mat['unit']}"
                if mat.get("packs"):
                    pack = f"{mat['packs']} {mat['pack_label']} × {mat['price'] / mat['packs']:g} ₽"
                    lines.append(f"  {mat['name']}: {qty} → {pack} = {mat['price']:g} ₽")
                else:
                    lines.append(f"  {mat['name']}: {qty} = {mat['price']:g} ₽")
            lines.append(f"Итого по работе: {res['total']:g} ₽\n")
            grand_total += res["total"]

        grand_total = int(round(grand_total))
        lines.append("-" * 40)
        lines.append(f"ИТОГО: {grand_total:,} ₽".replace(",", " "))
        lines.append("-" * 40)
        lines.append("⚠ Расчёт ориентировочный. Фактический")
        lines.append("расход зависит от кривизны поверхностей")
        lines.append("и квалификации мастера.")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# ВЕБ-ИНТЕРФЕЙС НА STREAMLIT
# ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="Сметчик", page_icon="🏗️", layout="centered")

st.title("🏗️ Сметчик: калькулятор ремонта")
st.markdown("Введите размеры комнаты и выберите виды работ. Приложение посчитает материалы и стоимость.")

# 1. Габариты комнаты
st.header("1. Габариты комнаты")
col1, col2, col3 = st.columns(3)
with col1:
    length = st.number_input("Длина, м", value=2.40, step=0.1, format="%.2f")
with col2:
    width = st.number_input("Ширина, м", value=3.00, step=0.1, format="%.2f")
with col3:
    height = st.number_input("Высота потолков, м", value=2.70, step=0.1, format="%.2f")

openings_on = st.checkbox("Вычитать проёмы (окна и двери)")
openings_area = 0.0
if openings_on:
    col_w, col_d = st.columns(2)
    with col_w:
        win_area = st.number_input("Площадь окон, м²", value=0.0, step=0.5)
    with col_d:
        door_area = st.number_input("Площадь дверей, м²", value=0.0, step=0.5)
    openings_area = win_area + door_area

# 2. Виды работ
st.header("2. Виды работ")
params = {"length": length, "width": width, "height": height, "openings_area": openings_area}

# Штукатурка
if st.checkbox("Штукатурка стен"):
    plaster_thick = st.selectbox("Толщина слоя штукатурки, мм", (5.0, 10.0, 15.0, 20.0), index=1)
    params["plaster"] = plaster_thick
else:
    params["plaster"] = None

# Шпаклёвка
if st.checkbox("Шпаклёвка стен"):
    putty_kind = st.radio("Тип шпаклёвки", ("Стартовая", "Финишная"), horizontal=True)
    params["putty"] = putty_kind
else:
    params["putty"] = None

# Покраска
if st.checkbox("Покраска"):
    paint_surfaces = st.selectbox("Поверхность для покраски", ("Стены", "Потолок", "Стены + потолок"), index=2)
    paint_coats = st.slider("Количество слоев краски", 1, 3, 2)
    params["paint"] = (paint_surfaces, paint_coats)
else:
    params["paint"] = None

# Натяжной потолок
if st.checkbox("Натяжной потолок"):
    spots = st.number_input("Количество точечных светильников, шт.", value=0, step=1, min_value=0)
    params["stretch"] = int(spots)
else:
    params["stretch"] = None

# Плитка
if st.checkbox("Укладка плитки"):
    tile_surfaces = st.selectbox("Поверхность для плитки", ("Стены", "Пол", "Стены + пол"), index=2)
    params["tiling"] = tile_surfaces
else:
    params["tiling"] = None

# 3. Цены (в сайдбаре для экономии места на телефоне)
st.sidebar.header("Цены на материалы (₽)")
prices = {}
with st.sidebar.expander("Нажмите, чтобы изменить цены", expanded=False):
    for key, label in [
        ("plaster_bag", "Штукатурка (меш. 30 кг)"),
        ("putty_bag", "Шпаклёвка (меш. 20 кг)"),
        ("paint_liter", "Краска (1 л)"),
        ("stretch_m2", "Полотно натяжное (1 м²)"),
        ("profile_pm", "Профиль ПВХ (1 п.м.)"),
        ("tile_m2", "Плитка (1 м²)"),
        ("tile_glue_bag", "Клей плиточный (меш. 25 кг)"),
        ("spot_light", "Светильник точечный (шт.)"),
    ]:
        prices[key] = st.number_input(label, value=MaterialCalculator.DEFAULT_PRICES[key], step=10.0)

# 4. Расчёт
st.header("3. Результат")
if st.button("Рассчитать смету", use_container_width=True, type="primary"):
    if not any(params[k] is not None for k in ("plaster", "putty", "paint", "stretch", "tiling")):
        st.warning("Отметьте хотя бы один вид работ.")
    else:
        calc = MaterialCalculator(prices)
        areas, results = calc.full_estimate(params)
        estimate_text = MaterialCalculator.format_estimate(areas, results)
        
        # Вывод результата моноширинным шрифтом
        st.text_area("Смета", value=estimate_text, height=400, disabled=True)
        
        # Кнопка скачивания
        st.download_button(
            label="💾 Скачать смету в .txt",
            data=estimate_text,
            file_name="smeta.txt",
            mime="text/plain",
            use_container_width=True
        )
else:
    st.info("Заполните данные и нажмите «Рассчитать смету».")