"""Aplica el alfabeto de alfabeto.json a todo el sitio.

Uso:  python scripts/set_alphabet.py

- Crea lexico/<clave>.json vacío para cada letra nueva (no toca las existentes).
- Reescribe LETTER_FILES en editor.js y el índice alfabético + LETTERS de lexico.html.
- Regenera lexico/index.json.
Avisa (sin borrar) si quedan archivos de letra que ya no están en el alfabeto.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LEX = ROOT / 'lexico'
letters = [tuple(x) for x in json.loads((ROOT / 'alfabeto.json').read_text(encoding='utf-8'))['letras']]

keys = [k for _, k in letters]
if len(set(keys)) != len(keys):
    sys.exit('alfabeto.json: claves repetidas')
for _, k in letters:
    if not re.fullmatch(r'[a-z0-9-]+', k):
        sys.exit(f'alfabeto.json: la clave «{k}» debe ser ascii en minúsculas (a-z, 0-9, -)')

LEX.mkdir(exist_ok=True)
for letter, key in letters:
    p = LEX / f'{key}.json'
    if not p.exists():
        p.write_text(json.dumps({'schema_version': 1, 'letter': letter, 'key': key, 'entries': []},
                                ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('creado', p.relative_to(ROOT))

if not (LEX / 'morphemes.json').exists():
    (LEX / 'morphemes.json').write_text('{\n  "schema_version": 1,\n  "morphemes": []\n}\n', encoding='utf-8')

generated = {'index.json', 'morphemes.json', 'history.json', 'history-items.json'}
for p in sorted(LEX.glob('*.json')):
    if p.name not in generated and p.stem not in keys:
        print(f'AVISO: {p.relative_to(ROOT)} no corresponde a ninguna letra del alfabeto')

# editor.js
js = ROOT / 'editor.js'
s = js.read_text(encoding='utf-8')
arr = 'var LETTER_FILES = [' + ','.join(f"['{l}','{k}']" for l, k in letters) + '];'
s, n = re.subn(r'var LETTER_FILES = \[.*?\];', lambda m: arr, s, count=1, flags=re.S)
assert n == 1, 'no se encontró LETTER_FILES en editor.js'
js.write_text(s, encoding='utf-8')

# lexico.html
html = ROOT / 'lexico.html'
s = html.read_text(encoding='utf-8')
links = ''.join(f'<a href="#sec-{k}" data-key="{k}">{l}</a>' for l, k in letters)
s, n1 = re.subn(r'(<nav class="alphabet"[^>]*>).*?(<a href="#lex-all")', lambda m: m.group(1) + links + m.group(2), s, count=1, flags=re.S)
data = json.dumps([{'letter': l, 'key': k, 'file': f'lexico/{k}.json'} for l, k in letters], ensure_ascii=False)
s, n2 = re.subn(r'const LETTERS=\[.*?\];', lambda m: f'const LETTERS={data};', s, count=1, flags=re.S)
first = letters[0]
s = re.sub(r"activeKey='[^']*'", f"activeKey='{first[1]}'", s, count=1)
s = re.sub(r'Cargando [^<…]*…', f'Cargando {first[0]}…', s, count=1)
assert n1 == 1 and n2 == 1, 'no se encontró el índice alfabético en lexico.html'
html.write_text(s, encoding='utf-8')

subprocess.run([sys.executable, str(ROOT / 'scripts' / 'build_lexicon_index.py')], check=True)
print(f'Alfabeto aplicado: {len(letters)} letras ({" ".join(l for l, _ in letters)})')
