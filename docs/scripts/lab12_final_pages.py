from copy import deepcopy

from docs.scripts.build_lab12_report import (
    GROUP, LINE, PAGE, RANKING, YEAR, SCHEMA,
    categorical_filter, color, field, literal, projection, visual,
)

HOME = "lab12_inicio"
SEASONAL = "lab12_estacionalidad"
MODELS = "lab12_predicciones"
DETAIL = "lab12_detalle"
V3 = "lab12_v3_matriz"
V4 = "lab12_v4_anios"
V5 = "lab12_v5_variacion"
DATES = "lab12_fechas_v5"
PAGES = {
    HOME: "Inicio",
    PAGE: "Datos observados",
    SEASONAL: "Estacionalidad y años",
    MODELS: "Predicciones y modelos",
    DETAIL: "Detalle de serie",
}


def textbox(name, text, position, size=12, foreground="#1B2733"):
    item = visual(name, "textbox", text, position)
    item["visual"]["visualContainerObjects"]["title"][0]["properties"]["show"] = literal(False)
    item["visual"]["objects"] = {"general": [{"properties": {"paragraphs": [{
        "textRuns": [{"value": text, "textStyle": {
            "fontFamily": "Arial", "fontSize": f"{size}pt", "color": foreground,
        }}],
    }]}}]}
    return item


def button(name, text, position, action, target=None, active=False):
    item = visual(name, "actionButton", text, position)
    containers = item["visual"]["visualContainerObjects"]
    containers["title"][0]["properties"]["show"] = literal(False)
    properties = {"show": literal(True), "type": literal(action)}
    if target is not None:
        properties["bookmark" if action == "Bookmark" else "navigationSection"] = literal(target)
    containers["visualLink"] = [{"properties": properties}]
    item["visual"]["objects"] = {
        "text": [{"properties": {
            "show": literal(True), "text": literal(text), "fontSize": literal(11),
            "fontFamily": literal("Arial"),
            "fontColor": color("#FFFFFF" if active else "#1B2733"),
        }}],
        "fill": [{"properties": {
            "show": literal(True), "fillColor": color("#20745A" if active else "#FFFFFF"),
        }}],
        "outline": [{"properties": {"show": literal(True), "lineColor": color("#DDE3E9")}}],
    }
    for entries in item["visual"]["objects"].values():
        properties = entries[0]["properties"]
        entries[:] = [{"properties": {"show": literal(True)}}] + [
            {"selector": {"id": state}, "properties": {
                key: value for key, value in properties.items() if key != "show"
            }}
            for state in ["default", "hover", "pressed"]
        ]
    return item


def measure_card(name, measure, position, warning=False):
    item = visual(name, "card", measure, position, {
        "Values": [projection("Medidas", measure, "Measure")],
    })
    item["visual"]["visualContainerObjects"]["title"][0]["properties"]["show"] = literal(False)
    item["visual"]["visualContainerObjects"]["padding"] = [{
        "properties": {side: literal(4) for side in ["top", "bottom", "left", "right"]},
    }]
    item["visual"]["objects"] = {
        "categoryLabels": [{"properties": {"show": literal(False)}}],
        "labels": [{"properties": {
            "fontSize": literal(12 if warning else 10), "fontFamily": literal("Arial"),
            "color": color("#B3261E" if warning else "#1B2733"),
            "labelDisplayUnits": literal(1),
        }}],
        "wordWrap": [{"properties": {"show": literal(True)}}],
    }
    return item


def slicer(name, title, table, column, position, values=None, mode="Dropdown", single=True):
    item = visual(name, "slicer", title, position, {"Values": [projection(table, column)]})
    item["visual"]["objects"] = {
        "data": [{"properties": {"mode": literal(mode)}}],
        "selection": [{"properties": {
            "singleSelect": literal(single), "selectAllCheckboxEnabled": literal(False),
        }}],
    }
    if values is not None:
        item["visual"]["objects"]["general"] = [{"properties": {"filter": {
            "filter": categorical_filter(name + "_inicial", table, column, values)["filter"],
        }}}]
    return item


def date_slicer():
    item = slicer(DATES, "Periodo de V5 · no cambia V1 ni V2", "Calendario", "Date",
                  (840, 560, 416, 96, 30), mode="Between", single=False)
    expression = field("Calendario", "Date")
    expression["Column"]["Expression"]["SourceRef"] = {"Source": "s"}
    conditions = [
        {"Comparison": {"ComparisonKind": kind, "Left": expression,
                        "Right": {"Literal": {"Value": f"datetime'{value}T00:00:00'"}}}}
        for kind, value in [(2, "2010-01-01"), (4, "2026-06-30")]
    ]
    item["visual"]["objects"]["general"] = [{"properties": {"filter": {"filter": {
        "Version": 2, "From": [{"Name": "s", "Entity": "Calendario", "Type": 0}],
        "Where": [{"Condition": {"And": {"Left": conditions[0], "Right": conditions[1]}}}],
    }}}}]
    item["visual"]["objects"]["data"][0]["properties"].update({
        key: {"expr": {"Literal": {"Value": f"datetime'{value}T00:00:00'"}}}
        for key, value in [("startDate", "2010-01-01"), ("endDate", "2026-06-30")]
    })
    return item


def chart(name, title, measure, category, position, visual_type="clusteredColumnChart"):
    item = visual(name, visual_type, title, position, {
        "Category": [projection("Calendario", category)],
        "Y": [projection("Medidas", measure, "Measure")],
    })
    item["visual"]["objects"] = {
        "dataPoint": [{"properties": {"defaultColor": color("#1F4E79")}}],
        "categoryAxis": [{"properties": {"fontSize": literal(10), "axisType": literal("Categorical")}}],
        "valueAxis": [{"properties": {"fontSize": literal(10), "start": literal(0)}}],
    }
    item["visual"]["query"]["sortDefinition"] = {
        "sort": [{"field": field("Calendario", category), "direction": "Ascending"}],
    }
    return item


def bookmark(page, items):
    states = {}
    for item in items:
        config = item["visual"]
        state = {
            "filters": {"byExpr": [
                {
                    "name": entry["name"], "type": entry["type"],
                    "expression": deepcopy(entry["field"]), "filter": deepcopy(entry["filter"]),
                    "howCreated": 1,
                }
                for entry in item.get("filterConfig", {}).get("filters", [])
                if "filter" in entry
            ]},
            "singleVisual": {
                "visualType": config["visualType"],
                "objects": {"merge": deepcopy(config.get("objects", {}))},
            },
            "highlight": {"selection": []},
        }
        query = config.get("query", {}).get("queryState", {})
        if query:
            state["singleVisual"]["activeProjections"] = {
                role: [p["field"] for p in value["projections"] if p.get("active", True)]
                for role, value in query.items()
            }
        sort = config.get("query", {}).get("sortDefinition", {}).get("sort", [])
        if sort:
            state["singleVisual"]["orderBy"] = [
                {"Expression": deepcopy(item["field"]),
                 "Direction": 2 if item["direction"] == "Descending" else 1}
                for item in sort
            ]
        if item["name"] == V5:
            state["singleVisual"]["isDrillDisabled"] = True
        states[item["name"]] = state
    return {
        "$schema": SCHEMA + "bookmark/1.4.0/schema.json",
        "name": "inicial_" + page, "displayName": "Inicial – " + PAGES[page],
        "options": {
            "suppressData": False, "suppressDisplay": False,
            "suppressActiveSection": False, "applyOnlyToTargetVisuals": False,
        },
        "explorationState": {
            "version": "1.3", "activeSection": page,
            "sections": {page: {"visualContainers": states, "filters": {"byName": {}}}},
        },
    }


def complete_definitions(original):
    result = deepcopy(original)
    prefix = f"Report/definition/pages/{PAGE}"
    observed = [
        result[f"{prefix}/visuals/{name}/visual.json"]
        for name in [LINE, RANKING, GROUP, YEAR]
    ]
    for item, y, height in [
        (observed[0], 232, 300), (observed[1], 232, 300),
        (observed[2], 112, 96), (observed[3], 112, 96),
    ]:
        item["position"].update(y=y, height=height)
    yoy = chart(V5, "V5 · ¿Cuánto cambió cada mes frente al mismo mes del año anterior?",
                "Variación interanual %", "Date", (24, 682, 1232, 300, 4))
    yoy["visual"]["query"]["queryState"]["Category"]["projections"] = [
        projection("Calendario", "Año", active=True),
        projection("Calendario", "Mes", active=True),
    ]
    yoy["visual"]["query"]["sortDefinition"]["sort"] = [
        {"field": field("Calendario", column), "direction": "Ascending"}
        for column in ["Año", "Mes"]
    ]
    yoy["visual"]["objects"]["valueAxis"][0]["properties"].pop("start")
    yoy["visual"]["objects"]["categoryAxis"][0]["properties"].update({
        "concatenateLabels": literal(False),
    })
    yoy["visual"]["visualContainerObjects"]["visualHeader"] = [{
        "properties": {name: literal(False) for name in [
            "showDrillRoleSelector", "showDrillUpButton", "showDrillToggleButton",
            "showDrillDownLevelButton", "showDrillDownExpandButton",
        ]},
    }]
    yoy["visual"]["objects"]["y1AxisReferenceLine"] = [{
        "selector": {"id": "cero"},
        "properties": {
            "show": literal(True), "value": literal(0),
            "lineColor": color("#5B6B7A"), "style": literal("dashed"),
            "transparency": literal(0),
        },
    }]
    yoy["visual"]["query"]["queryState"]["Y"]["projections"][0]["format"] = "0.0 %"
    observed += [
        yoy, date_slicer(),
        measure_card("nota_v5", "Nota V5", (24, 994, 1232, 104, 5)),
        measure_card("mensaje_v5", "Mensaje V5", (24, 616, 790, 56, 6), warning=True),
    ]
    series = slicer("serie_estacional", "Serie · selección única", "DimSerie", "nombre",
                    (24, 112, 500, 96, 0), ["Total"])
    years = slicer("anios_estacional", "Años · 2009–2026", "Calendario", "Año",
                   (548, 112, 708, 96, 1), mode="Between", single=False)
    matrix = visual(V3, "pivotTable", "V3 · ¿En qué meses se concentra el ingreso de viajeros?",
                    (24, 264, 1232, 460, 2), {
                        "Rows": [projection("Calendario", "Año")],
                        "Columns": [projection("Calendario", "Mes")],
                        "Values": [projection("Medidas", "Viajeros serie", "Measure", format="#,0")],
                    })
    matrix["visual"]["objects"] = {
        "subTotals": [{"properties": {"rowSubtotals": literal(False), "columnSubtotals": literal(False)}}],
        "rowHeaders": [{"properties": {"fontSize": literal(10)}}],
        "columnHeaders": [{"properties": {"fontSize": literal(10)}}],
        "values": [{"properties": {
            "fontSize": literal(10),
            "backColor": {"solid": {"color": {"expr": {"FillRule": {
                "Input": field("Medidas", "Viajeros serie", "Measure"),
                "FillRule": {"linearGradient2": {
                    "min": {"color": {"Literal": {"Value": "'#E7EFF6'"}}},
                    "max": {"color": {"Literal": {"Value": "'#1F4E79'"}}},
                }},
            }}}}},
            "fontColor": {"solid": {"color": {"expr": field("Medidas", "Color texto V3", "Measure")}}},
        }, "selector": {
            "data": [{"dataViewWildcard": {"matchingOption": 1}}],
            "metadata": "Medidas.Viajeros serie",
        }}],
    }
    for item in [matrix, yoy]:
        item["visual"]["visualContainerObjects"]["subTitle"] = [{"properties": {
            "show": literal(True), "text": {"expr": field("Medidas", "Serie elegida", "Measure")},
            "fontFamily": literal("Arial"), "fontSize": literal(11), "fontColor": color("#1B2733"),
        }}]
    annual = chart(V4, "V4 · ¿Cómo cambia el total de viajeros entre años completos?",
                   "Total año completo", "Año", (24, 846, 1232, 300, 3))
    seasonal = [
        series, years, matrix, annual,
        measure_card("mensaje_v3", "Mensaje V3", (24, 212, 1232, 44, 4), True),
        measure_card("nota_v3", "Nota V3", (24, 730, 1232, 72, 5)),
        measure_card("mensaje_v4", "Mensaje V4", (24, 802, 1232, 44, 6), True),
        measure_card("nota_v4", "Nota V4", (24, 1154, 1232, 94, 7)),
    ]
    home = [
        textbox("proposito", "Observatorio de turismo de Guatemala\n"
                "Permite explorar el ingreso de viajeros, comparar años completos y revisar estimaciones existentes.",
                (48, 132, 1184, 128, 0), 20),
        textbox("cobertura", "Datos registrados: enero de 2009 a junio de 2026.\n"
                "Estimaciones: abril de 2021 a junio de 2026, 63 meses ya registrados.\n"
                "Las estimaciones no son pronósticos futuros y no incluyen intervalos de confianza.",
                (48, 280, 1184, 136, 1), 16),
        textbox("leyenda_azul", "Azul · viajeros observados", (48, 440, 560, 48, 2), 16, "#1F4E79"),
        textbox("leyenda_naranja", "Naranja · estimaciones de modelos", (640, 440, 592, 48, 3), 16, "#A65E16"),
        textbox("leyenda_verde", "Verde · página activa", (48, 500, 560, 48, 4), 16, "#20745A"),
        textbox("leyenda_roja", "Rojo · alertas y ausencia de datos", (640, 500, 592, 48, 5), 16, "#B3261E"),
        textbox("alcance", "Las vías de ingreso suman el total. Los tres países no representan todos los mercados.\n"
                "No se suman vías, países y total entre sí.", (48, 580, 1184, 90, 6), 14),
        *[
            button("pregunta_" + target, question, (48, 720 + index * 100, 1184, 76, 10 + index),
                   "PageNavigation", target)
            for index, (target, question) in enumerate([
                (PAGE, "¿Cómo evoluciona el ingreso y qué vías o países predominan?"),
                (SEASONAL, "¿En qué meses se concentra y cómo cambian los años completos?"),
                (MODELS, "¿Qué estimaron los modelos y cuánto se equivocaron?"),
            ])
        ],
    ]
    models = [textbox("pendiente_modelos",
                      "Predicciones y modelos\nPágina preparada para V6, V7 y V8 de Diego.\n"
                      "Evaluación: abril de 2021 a junio de 2026. MAE y RMSE en viajeros; MAPE en porcentaje.",
                      (48, 150, 1184, 240, 0), 20)]
    history = chart("detalle_evolucion", "Evolución de la serie · Año > Trimestre > Mes",
                    "Viajeros serie", "Año", (24, 420, 1232, 620, 2), "lineChart")
    history["visual"]["query"]["queryState"]["Category"]["projections"] = [
        projection("Calendario", name, active=index == 0)
        for index, name in enumerate(["Año", "Trimestre", "Mes"])
    ]
    detail = [
        measure_card("detalle_titulo", "Título detalle", (24, 140, 1232, 72, 0)),
        visual("detalle_total", "card", "Viajeros · último año completo",
               (24, 240, 1232, 100, 1), {"Values": [
                   projection("Medidas", "Total último año completo", "Measure", format="#,0"),
               ]}),
        measure_card("detalle_nota", "Nota detalle", (24, 350, 1232, 60, 3)),
        history, button("atras_detalle", "Atrás · volver al origen", (24, 1080, 360, 64, 4), "Back"),
    ]
    detail[1]["visual"]["objects"] = {
        "labels": [{"properties": {"labelDisplayUnits": literal(1), "fontSize": literal(28)}}],
        "categoryLabels": [{"properties": {"show": literal(False)}}],
    }
    content = {HOME: home, PAGE: observed, SEASONAL: seasonal, MODELS: models, DETAIL: detail}
    for page, items in content.items():
        for item in items:
            for entry in item.get("filterConfig", {}).get("filters", []):
                if "filter" in entry:
                    entry["howCreated"] = "User"
        items += [
            button("nav_" + target, name, (24 + index * 248, 16, 240, 60, 100 + index),
                   "PageNavigation", target, active=page == target)
            for index, (target, name) in enumerate(PAGES.items())
        ]
        items.append(button("reset_" + page, "Restablecer vista", (936, 1268, 320, 60, 110),
                            "Bookmark", "inicial_" + page))
        items.append(textbox("ayuda_" + page,
                             "Desktop: Ctrl + clic en botones. Clic en barra: seleccionar. "
                             "Clic derecho en V2: Detalle de serie.",
                             (24, 1274, 880, 54, 111), 10))
        definition = {
            "$schema": SCHEMA + "page/2.1.0/schema.json",
            "name": page, "displayName": PAGES[page], "displayOption": "FitToWidth",
            "height": 1350, "width": 1280,
            "objects": {"background": [{"properties": {
                "color": color("#F4F6F8"), "transparency": literal(0),
            }}]},
        }
        if page == PAGE:
            targets = [LINE, V5, "nota_v5", "mensaje_v5"]
            allowed = {(RANKING, target) for target in targets}
            allowed |= {(GROUP, RANKING), (YEAR, RANKING)}
            allowed |= {(DATES, target) for target in [V5, "nota_v5", "mensaje_v5"]}
        elif page == SEASONAL:
            allowed = {(source, target) for source in ["serie_estacional", "anios_estacional"]
                       for target in [V3, V4, "nota_v3", "nota_v4", "mensaje_v3", "mensaje_v4"]}
        else:
            allowed = set()
        data_items = [item["name"] for item in items if item["visual"].get("query")]
        definition["visualInteractions"] = [
            {"source": source, "target": target,
             "type": "DataFilter" if (source, target) in allowed else "NoFilter"}
            for source in data_items for target in data_items if source != target
        ]
        if page == DETAIL:
            definition["type"] = "Drillthrough"
            definition["filterConfig"] = {"filters": [{
                "name": "detalle_serie", "field": field("DimSerie", "nombre"),
                "type": "Categorical", "howCreated": "Drillthrough",
            }]}
            definition["pageBinding"] = {
                "name": "detalle_por_serie", "type": "Drillthrough", "acceptsFilterContext": "Default",
                "parameters": [{"name": "serie", "boundFilter": "detalle_serie",
                                "fieldExpr": field("DimSerie", "nombre")}],
            }
        page_prefix = f"Report/definition/pages/{page}"
        result[f"{page_prefix}/page.json"] = definition
        for item in items:
            result[f"{page_prefix}/visuals/{item['name']}/visual.json"] = item
        result[f"Report/definition/bookmarks/inicial_{page}.bookmark.json"] = bookmark(page, items)
    result["Report/definition/bookmarks/bookmarks.json"] = {
        "$schema": SCHEMA + "bookmarksMetadata/1.0.0/schema.json",
        "items": [{"name": "inicial_" + page} for page in PAGES],
    }
    from docs.scripts.lab12_model_pages import definitions as model_definitions

    return model_definitions(result)
