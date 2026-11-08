"""Valores de referencia del Lab 12, calculados directamente de los CSV de insumos/.

Uso, desde la raíz del repositorio:
    python -m docs.scripts.lab12_valores_referencia

Las comprobaciones `assert` fallan si los insumos cambian; los valores impresos
son los que Hugo y Diego deben obtener en Power BI para V3–V8, T1–T3 y 5.5.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SERIES_DIR = ROOT / "insumos" / "series"
RESULTS_DIR = ROOT / "insumos" / "resultados"
SERIES = ["total", "via_aerea", "via_terrestre", "via_maritima",
          "pais_el_salvador", "pais_estados_unidos", "pais_honduras"]
MODELS = ["sarima", "holt_winters", "ses", "seasonal_naive", "prophet"]
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def load():
    observed = pd.concat(
        pd.read_csv(SERIES_DIR / f"serie_{key}.csv", parse_dates=["fecha"]).assign(serie=key) for key in SERIES
    )
    predicted = pd.concat(
        pd.read_csv(RESULTS_DIR / "predicciones" / f"{serie}_{model}.csv", parse_dates=["fecha"]).assign(serie=serie, modelo=model)
        for serie in SERIES for model in MODELS
    )
    metrics = pd.read_csv(RESULTS_DIR / "metricas_modelos.csv")
    return observed, predicted, metrics


def check_structure(observed, predicted, metrics):
    assert len(observed) == 7 * 210 == 1470, len(observed)
    assert len(predicted) == 35 * 63 == 2205, len(predicted)
    assert len(metrics) == 35, len(metrics)
    assert not observed.duplicated(["serie", "fecha"]).any()
    assert not predicted.duplicated(["serie", "modelo", "fecha"]).any()
    assert not metrics.duplicated(["serie", "modelo"]).any()
    assert set(metrics["serie"]) == set(SERIES) and set(metrics["modelo"]) == set(MODELS)
    assert observed["fecha"].dt.is_month_start.all() and predicted["fecha"].dt.is_month_start.all()
    assert observed["viajeros"].notna().all() and (observed["viajeros"] >= 0).all()
    assert predicted["prediccion"].notna().all()
    for key, group in observed.groupby("serie"):
        assert (group["fecha"].min(), group["fecha"].max()) == (pd.Timestamp("2009-01-01"), pd.Timestamp("2026-06-01")), key
    for key, group in predicted.groupby(["serie", "modelo"]):
        assert (group["fecha"].min(), group["fecha"].max()) == (pd.Timestamp("2021-04-01"), pd.Timestamp("2026-06-01")), key


def paired(observed, predicted):
    return predicted.merge(observed, on=["serie", "fecha"], how="inner", validate="many_to_one").assign(
        diferencia=lambda frame: frame["viajeros"] - frame["prediccion"]
    )


def recompute_metrics(pairs):
    records = []
    for (serie, modelo), group in pairs.groupby(["serie", "modelo"]):
        error = group["diferencia"]
        valid = group["viajeros"] != 0
        records.append({
            "serie": serie, "modelo": modelo, "meses": len(group),
            "mae": error.abs().mean(),
            "rmse": np.sqrt(np.mean(np.square(error))),
            "mape": (error[valid] / group.loc[valid, "viajeros"]).abs().mean() * 100,
            "mape_excluidos": int((~valid).sum()),
        })
    return pd.DataFrame(records)


def check_metrics(recomputed, metrics):
    merged = recomputed.merge(metrics, on=["serie", "modelo"], suffixes=("_calc", "_csv"), validate="one_to_one")
    assert len(merged) == 35 and (merged["meses"] == 63).all()
    for column in ["mae", "rmse", "mape"]:
        assert np.allclose(merged[f"{column}_calc"], merged[f"{column}_csv"], rtol=1e-9, atol=0), column
    assert (merged["mape_excluidos_calc"] == merged["mape_excluidos_csv"]).all()


def fmt(value, decimals=0):
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def series_of(observed, key):
    return observed.loc[observed["serie"] == key].set_index("fecha")["viajeros"].sort_index()


def yoy(series, date):
    current, previous = series[pd.Timestamp(date)], series[pd.Timestamp(date) - pd.DateOffset(years=1)]
    return (current / previous - 1) * 100


def report(observed, pairs, metrics):
    total = series_of(observed, "total")
    yearly = observed.assign(anio=observed["fecha"].dt.year).groupby(["serie", "anio"])["viajeros"]
    sums, counts = yearly.sum(), yearly.count()
    lines = [("Conteos Observaciones / Predicciones / Metricas", "1.470 / 2.205 / 35")]

    lines += [(f"2025 · {key}", fmt(sums[key, 2025])) for key in SERIES]
    quarters = total["2020"].groupby(total["2020"].index.quarter).sum()
    lines.append(("Total 2020 (T1 · T2 · T3 · T4)", f"{fmt(quarters.sum())} ({' · '.join(fmt(v) for v in quarters)})"))

    dic_2025 = total["2025-12-01"]
    year_2025 = total["2025"]
    peak = year_2025.idxmax()
    lines.append(("V3 · Total dic-2025", fmt(dic_2025)))
    lines.append(("V3 · Total, mes de mayor valor en 2025", f"{MONTHS[peak.month - 1]}-2025 = {fmt(year_2025.max())}"))

    complete = counts.loc["total"][counts.loc["total"] == 12]
    excluded = counts.loc["total"][counts.loc["total"] < 12]
    lines.append(("V4 · Total 2024 / 2025 (años completos)", f"{fmt(sums['total', 2024])} / {fmt(sums['total', 2025])}"))
    lines.append(("V4 · Años completos mostrados", f"{len(complete)} ({complete.index.min()}–{complete.index.max()})"))
    lines.append(("V4 · Años excluidos", "; ".join(f"{year}: {count} de 12 meses" for year, count in excluded.items())))

    lines.append(("V5 · Total ene-2025 vs ene-2024", f"{fmt(yoy(total, '2025-01-01'), 2)} %"))
    lines.append(("V5 · Total jun-2026 vs jun-2025", f"{fmt(yoy(total, '2026-06-01'), 2)} %"))
    lines.append(("V5 · Total abr-2021 vs abr-2020", f"{fmt(yoy(total, '2021-04-01'), 2)} %"))

    ses = pairs.loc[(pairs["serie"] == "total") & (pairs["modelo"] == "ses")].set_index("fecha")
    for date in ["2021-04-01", "2025-12-01"]:
        row = ses.loc[date]
        lines.append((f"V6 · Total/SES {date[:7]} observado · estimado",
                      f"{fmt(row['viajeros'], 2)} · {fmt(row['prediccion'], 2)}"))

    for _, row in metrics.loc[metrics["serie"] == "total"].sort_values("mae").iterrows():
        lines.append((f"V7 · Total · {row['modelo']} (MAE · RMSE · MAPE %)",
                      f"{fmt(row['mae'], 2)} · {fmt(row['rmse'], 2)} · {fmt(row['mape'], 2)}"))

    worst = ses["diferencia"].abs().idxmax()
    lines.append(("V8 · Total/SES abr-2021 diferencia", fmt(ses.loc["2021-04-01", "diferencia"], 2)))
    lines.append(("V8 · Total/SES mayor |diferencia|",
                  f"{MONTHS[worst.month - 1]}-{worst.year} = {fmt(ses.loc[worst, 'diferencia'], 2)}"))
    lines.append(("V8 · Total/SES meses con observado > estimado", f"{int((ses['diferencia'] > 0).sum())} de {len(ses)}"))
    sarima = pairs.loc[(pairs["serie"] == "total") & (pairs["modelo"] == "sarima")].set_index("fecha")
    worst = sarima["diferencia"].abs().idxmax()
    lines.append(("V8 · Total/SARIMA abr-2021 diferencia (vista inicial)", fmt(sarima.loc["2021-04-01", "diferencia"], 2)))
    lines.append(("V8 · Total/SARIMA mayor |diferencia|",
                  f"{MONTHS[worst.month - 1]}-{worst.year} = {fmt(sarima.loc[worst, 'diferencia'], 2)}"))

    vias = {key: sums[key, 2025] for key in ["via_aerea", "via_terrestre", "via_maritima"]}
    leader = max(vias, key=vias.get)
    best = metrics.loc[(metrics["serie"] == "total") & metrics["modelo"].isin(["sarima", "holt_winters", "ses"])].nsmallest(1, "mae").iloc[0]
    lines.append(("T1 · Vía con más viajeros en 2025", f"{leader} = {fmt(vias[leader])}"))
    lines.append(("T2 · Total 2020 · T2 2020", f"{fmt(quarters.sum())} · {fmt(quarters[2])}"))
    lines.append(("T3 · Menor MAE (SARIMA, HW, SES) en Total", f"{best['modelo']} = {fmt(best['mae'], 2)}"))
    lines.append(("5.5 · Total 2025 · MAE Total SES", f"{fmt(sums['total', 2025])} · {fmt(best['mae'], 2)}"))

    # Sumas de control de los mismos indicadores con reglas de agregación explícitas.
    assert round(sums["total", 2025]) == 3_597_238
    assert round(sum(vias.values())) == 3_597_238
    assert round(quarters.sum()) == 1_266_340 and round(quarters[2]) == 31_635
    assert round(yoy(total, "2025-01-01"), 2) == -8.06
    assert leader == "via_terrestre" and best["modelo"] == "ses"
    assert round(ses.loc["2021-04-01", "diferencia"], 2) == -23_077.18
    assert list(excluded.index) == [2026] and excluded[2026] == 6

    width = max(len(label) for label, _ in lines)
    for label, value in lines:
        print(f"{label:<{width}}  {value}")


def main():
    observed, predicted, metrics = load()
    check_structure(observed, predicted, metrics)
    pairs = paired(observed, predicted)
    check_metrics(recompute_metrics(pairs), metrics)
    print("Comprobaciones superadas: estructura, duplicados, cobertura y 35 métricas recalculadas (rtol=1e-9).\n")
    report(observed, pairs, metrics)


if __name__ == "__main__":
    main()
