import pandas as pd


def build_source(config):
    periods = pd.period_range(
        config["periods"]["source_start"], config["periods"]["expected_last_period"], freq="M"
    )
    optional = {column: "valor" for column in config["source"]["optional_columns"]}
    return pd.DataFrame([
        {
            "Año": period.year,
            "Mes cod": period.month,
            "Vía": "Aérea",
            "Frontera": "Aeropuerto Internacional La Aurora",
            "País": "México",
            "Agrupación Residencia": "Extranjeros",
            "Tipo de Viajero": visitor_type,
            config["source"]["value_column"]: 100 + index,
            **optional,
        }
        for index, period in enumerate(periods)
        for visitor_type in config["target"]["visitor_types"]
    ])
