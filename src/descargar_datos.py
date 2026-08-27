import zipfile
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    data_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("Descargando dataset...")
    api = KaggleApi()
    api.authenticate()
    
    api.competition_download_files("nlp-getting-started", path=str(data_dir))
    
    zip_path = data_dir / "nlp-getting-started.zip"
    if zip_path.exists():
        print("Extrayendo...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        zip_path.unlink()
        print("Listo.")

if __name__ == "__main__":
    main()
