"""Barrera explícita para el futuro empaquetado público; no impide compilar vistas locales."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
payload = json.loads((root/'web/public/data/observatory.json').read_text(encoding='utf-8'))
if payload.get('mode') == 'local_preview' or payload.get('release_approved') is not True:
    raise SystemExit('PUBLICACIÓN BLOQUEADA: vista local, licencia/privacidad de redistribución pendientes. No subir web/dist.')
print('Control de datos aprobado; aún se requiere autorización explícita del propietario para desplegar.')
