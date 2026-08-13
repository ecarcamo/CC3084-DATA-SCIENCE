from getpass import getpass

from sentinelhub import SHConfig

from src.config import PERFIL_SH, SH_BASE_URL, SH_TOKEN_URL


def registrar_credenciales() -> None:
    print(f"Registrando credenciales en el perfil '{PERFIL_SH}' de sentinelhub-py.")
    print("Client ID y Client secret se obtienen en:")
    print("  https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings")
    print("(sección 'OAuth clients' -> 'Create new')\n")

    client_id = getpass("SH_CLIENT_ID: ").strip()
    client_secret = getpass("SH_CLIENT_SECRET: ").strip()

    if not client_id or not client_secret:
        raise ValueError("Client ID y Client secret no pueden estar vacíos.")

    config = SHConfig(PERFIL_SH)
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.sh_base_url = SH_BASE_URL
    config.sh_token_url = SH_TOKEN_URL
    config.save(PERFIL_SH)

    print(f"\nCredenciales guardadas en: {SHConfig.get_config_location()}")
    print(f"Perfil '{PERFIL_SH}' listo. Verifica la conexión desde el notebook 01.")


if __name__ == "__main__":
    registrar_credenciales()
