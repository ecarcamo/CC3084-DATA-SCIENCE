import pandas as pd
import yaml

from pipeline.config import ROOT


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


def write_config(folder, frame=None):
    config = yaml.safe_load((ROOT / "config/pipeline.yaml").read_text(encoding="utf-8"))
    config["source"]["path"] = str(folder / "source.xlsx")
    for key in ("candidates_dir", "approved_dir", "history_dir", "run_log_dir"):
        config["outputs"][key] = str(folder / key)
    config["mlflow"]["tracking_uri"] = f"sqlite:///{(folder / 'mlflow.db').as_posix()}"
    config["mlflow"]["artifact_root"] = str(folder / "mlflow_artifacts")
    config_path = folder / "pipeline.yaml"
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    if frame is not None:
        frame.to_excel(config["source"]["path"], sheet_name=config["source"]["sheet"], index=False)
    return config_path, config
