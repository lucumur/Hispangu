"""Valida la integridad del léxico. Sale con código 1 si encuentra errores.

Comprueba:
  - que cada lexico/*.json sea JSON válido;
  - que no haya ids duplicados entre raíces, vocablos y morfemas;
  - que cada raíz esté en el archivo de su letra;
  - que cada referencia (refs y enlaces morph-link del análisis) apunte a un id existente;
  - que index.json coincida con lo que generaría scripts/build_lexicon_index.py.
"""
from pathlib import Path
import json
import re
import subprocess
import sys
import tempfile
import shutil

ROOT = Path(__file__).resolve().parents[1]
LEX = ROOT / 'lexico'
errors = []


def load(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:  # JSON roto
        errors.append(f'{path.relative_to(ROOT)}: JSON inválido ({exc})')
        return None


files = {p.name: load(p) for p in sorted(LEX.glob('*.json'))}
if errors:
    print('\n'.join(errors))
    sys.exit(1)

LETTER_FILES = [tuple(x) for x in json.loads((ROOT / 'alfabeto.json').read_text(encoding='utf-8'))['letras']]

ids = {}
def claim(i, where):
    if not i:
        errors.append(f'{where}: entrada sin id')
    elif i in ids:
        errors.append(f'id duplicado «{i}»: {ids[i]} y {where}')
    else:
        ids[i] = where

words = []
for letter, key in LETTER_FILES:
    name = f'{key}.json'
    data = files.get(name)
    if data is None:
        errors.append(f'falta lexico/{name}')
        continue
    for e in data.get('entries', []):
        claim(e.get('id'), f'{name} raíz {e.get("form")}')
        for w in e.get('words', []) or []:
            claim(w.get('id'), f'{name} vocablo {w.get("form")}')
            words.append((name, w))

for m in files['morphemes.json'].get('morphemes', []):
    claim(m.get('id'), f'morphemes.json morfema {m.get("form")}')

href = re.compile(r'href="#([^"]+)"')
for name, w in words:
    targets = [r.get('id') for r in w.get('refs', []) or [] if r.get('id')]
    targets += href.findall(w.get('analysis_html', '') or '')
    for t in dict.fromkeys(targets):
        if t not in ids:
            errors.append(f'{name} vocablo {w.get("form")}: referencia a «{t}», que no existe')

word_ids = {w.get('id') for _, w in words}
for name, w in words:
    for p in w.get('proviene_de', []) or []:
        pid = p.get('id')
        if pid == w.get('id'):
            errors.append(f'{name} vocablo {w.get("form")}: proviene de sí mismo')
        elif pid not in word_ids:
            errors.append(f'{name} vocablo {w.get("form")}: proviene_de «{pid}», que no es un vocablo existente')

def check_paradigmas(name, w):
    ps = w.get('paradigmas')
    if ps is None:
        return
    where = f'{name} vocablo {w.get("form")}'
    if not isinstance(ps, list) or not ps:
        errors.append(f'{where}: paradigmas debe ser una lista no vacía, o no estar')
        return
    for i, p in enumerate(ps, 1):
        loc = f'{where} paradigma {i}'
        if not isinstance(p, dict):
            errors.append(f'{loc}: no es un objeto')
            continue
        if not isinstance(p.get('tipo'), str) or not p['tipo'].strip():
            errors.append(f'{loc}: falta tipo (conjugación, declinación u otro)')
        if 'titulo' in p and (not isinstance(p['titulo'], str) or not p['titulo'].strip()):
            errors.append(f'{loc}: titulo vacío; omítelo si no hace falta')
        cols = p.get('columnas')
        if not isinstance(cols, list) or not cols or not all(isinstance(c, str) and c.strip() for c in cols):
            errors.append(f'{loc}: columnas inválidas')
            cols = []
        filas = p.get('filas')
        if not isinstance(filas, list) or not filas:
            errors.append(f'{loc}: sin filas')
            continue
        extra = set(p) - {'tipo', 'titulo', 'columnas', 'filas'}
        if extra:
            errors.append(f'{loc}: campos no previstos: {", ".join(sorted(extra))}')
        for j, f in enumerate(filas, 1):
            if not isinstance(f, dict) or set(f) - {'etiqueta', 'celdas'}:
                errors.append(f'{loc} fila {j}: se esperaba etiqueta y celdas')
                continue
            if not isinstance(f.get('etiqueta', ''), str):
                errors.append(f'{loc} fila {j}: etiqueta no es texto')
            cells = f.get('celdas')
            if not isinstance(cells, list) or len(cells) != len(cols) or not all(isinstance(c, str) for c in cells):
                errors.append(f'{loc} fila {j}: las celdas no coinciden con las columnas')

for name, w in words:
    check_paradigmas(name, w)

# index.json debe ser idéntico al que genera el script oficial
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    shutil.copytree(LEX, tmp / 'lexico')
    (tmp / 'scripts').mkdir()
    shutil.copy(ROOT / 'scripts' / 'build_lexicon_index.py', tmp / 'scripts')
    shutil.copy(ROOT / 'alfabeto.json', tmp)
    subprocess.run([sys.executable, str(tmp / 'scripts' / 'build_lexicon_index.py')], check=True, capture_output=True)
    if json.loads((tmp / 'lexico' / 'index.json').read_text(encoding='utf-8')) != files['index.json']:
        errors.append('index.json no coincide con lo que genera build_lexicon_index.py')

if errors:
    print(f'{len(errors)} problema(s) en el léxico:')
    print('\n'.join('  - ' + e for e in errors))
    sys.exit(1)
print(f'Léxico válido: {len(ids)} ids, {len(words)} vocablos.')
