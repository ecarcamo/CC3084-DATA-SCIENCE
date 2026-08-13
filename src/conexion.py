import os
from datetime import datetime, timezone

import pandas as pd
from sentinelhub import BBox, CRS, DataCollection, SentinelHubCatalog, SentinelHubSession, SHConfig

from src.config import (
    COLECCION_S2,
    FECHAS_OFICIALES,
    LAGOS,
    NUBOSIDAD_OFICIAL,
    PERFIL_SH,
    SH_BASE_URL,
    SH_TOKEN_URL,
)


def crear_config(perfil: str = PERFIL_SH) -> SHConfig:
    config = SHConfig(perfil)

    if not config.sh_client_id or not config.sh_client_secret:
        config.sh_client_id = os.environ.get("SH_CLIENT_ID", "")
        config.sh_client_secret = os.environ.get("SH_CLIENT_SECRET", "")

    if not config.sh_client_id or not config.sh_client_secret:
        raise RuntimeError(
            f"No hay credenciales en el perfil '{perfil}' ni en las variables de entorno "
            "SH_CLIENT_ID / SH_CLIENT_SECRET. Ejecuta: python -m src.credenciales"
        )

    config.sh_base_url = config.sh_base_url or SH_BASE_URL
    config.sh_token_url = config.sh_token_url or SH_TOKEN_URL
    return config


def verificar_conexion(config: SHConfig) -> dict:
    sesion = SentinelHubSession(config=config)
    token = sesion.token
    expira = datetime.fromtimestamp(token["expires_at"], tz=timezone.utc)
    return {
        "autenticado": True,
        "endpoint": config.sh_base_url,
        "expira_utc": expira.isoformat(),
    }


def coleccion_cdse(config: SHConfig) -> DataCollection:
    return DataCollection.SENTINEL2_L1C.define_from(
        "SENTINEL2_L1C_CDSE", service_url=config.sh_base_url
    )


def consultar_catalogo(config: SHConfig, lago: str) -> pd.DataFrame:
    catalogo = SentinelHubCatalog(config=config)
    coleccion = coleccion_cdse(config)
    bbox = BBox(LAGOS[lago]["bbox"], crs=CRS.WGS84)

    filas = []
    for fecha in FECHAS_OFICIALES[lago]:
        resultados = list(
            catalogo.search(
                coleccion,
                bbox=bbox,
                time=(fecha, fecha),
                fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover", "properties.platform"], "exclude": []},
            )
        )
        nubosidad_oficial, satelite_oficial = NUBOSIDAD_OFICIAL[lago].get(fecha, (None, None))

        if not resultados:
            filas.append(
                {
                    "lago": lago,
                    "fecha": fecha,
                    "id_producto": None,
                    "plataforma": None,
                    "nubosidad_catalogo_pct": None,
                    "nubosidad_oficial_pct": nubosidad_oficial,
                    "satelite_oficial": satelite_oficial,
                }
            )
            continue

        item = resultados[0]
        filas.append(
            {
                "lago": lago,
                "fecha": fecha,
                "id_producto": item.get("id"),
                "plataforma": item.get("properties", {}).get("platform"),
                "nubosidad_catalogo_pct": item.get("properties", {}).get("eo:cloud_cover"),
                "nubosidad_oficial_pct": nubosidad_oficial,
                "satelite_oficial": satelite_oficial,
            }
        )

    return pd.DataFrame(filas)


def consultar_catalogo_todos(config: SHConfig) -> pd.DataFrame:
    tablas = [consultar_catalogo(config, lago) for lago in LAGOS]
    return pd.concat(tablas, ignore_index=True)
