"""Descarga originales enlazados por el catálogo público OCISEVI, sin sobrescribir."""
import csv
import gzip
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://ocisevi.org.mx/ocisevi-nl/'


def main():
    catalog_path = ROOT / 'data/external/ocisevi-open_metadata.json'
    if not catalog_path.exists():
        with urlopen(BASE + 'open_metadata.json', timeout=90) as response:
            catalog_path.write_bytes(response.read())
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    destinations = [(item['filename'], ROOT / 'data/raw/ocisevi', item.get('year')) for item in catalog]
    destinations += [(name, ROOT / 'data/external/ocisevi', None) for name in ['Catalogo-Codigos.pdf', 'Diccionario_de_datos_RATIV.pdf']]

    def download(task):
        name, folder, year = task
        if Path(name).name != name:
            raise ValueError('Nombre de archivo no permitido')
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / name
        url = BASE + name
        if not target.exists():
            temporary = target.with_suffix(target.suffix + '.part')
            with urlopen(Request(url, headers={'User-Agent': 'OSV-NL data acquisition'}), timeout=180) as response, temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.rename(target)
        checksum = hashlib.file_digest(target.open('rb'), 'sha256').hexdigest()
        record = {'file': target.relative_to(ROOT).as_posix(), 'url': url, 'year': year,
                  'bytes': target.stat().st_size, 'sha256': checksum, 'downloaded_at': datetime.now(timezone.utc).isoformat()}
        if name.endswith('.csv.gz'):
            # Lectura completa comprueba también CRC/truncamiento gzip. No extrae ni altera originales.
            with gzip.open(target, 'rt', encoding='utf-8-sig', newline='') as stream:
                reader = csv.reader(stream)
                header = next(reader)
                record['columns'] = header
                record['column_count'] = len(header)
                record['rows'] = sum(1 for _ in reader)
            record['gzip_validated'] = True
        else:
            with target.open('rb') as stream:
                if stream.read(5) != b'%PDF-':
                    raise ValueError(f'{name}: respuesta no es PDF')
        print(json.dumps({k:v for k,v in record.items() if k != 'columns'}, ensure_ascii=True), flush=True)
        return record

    records = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        records = list(executor.map(download, destinations))
    manifest = {'source_page': BASE + 'datos-abiertos', 'catalog_url': BASE + 'open_metadata.json',
                'retrieved_at': datetime.now(timezone.utc).isoformat(), 'files': records,
                'license_status': 'Pautas de uso en aplicación: citar fuente y mantener integridad. Licencia específica pendiente de revisión; no autoriza publicación automática.'}
    (ROOT / 'data/external/ocisevi-download-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'OK: {len(records)} archivos verificados; {sum(r.get("rows", 0) for r in records):,} filas CSV.')


if __name__ == '__main__':
    main()
