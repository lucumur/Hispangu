# Hispangu

🌐 **Página web:** <https://lucumur.github.io/Hispangu/>

- [Raíces](https://lucumur.github.io/Hispangu/lexico.html)
- [Vocablos](https://lucumur.github.io/Hispangu/vocablos.html)
- [Morfemas](https://lucumur.github.io/Hispangu/morfemas.html)
- [Semántica](https://lucumur.github.io/Hispangu/semantica.html)
- [Pronombres](https://lucumur.github.io/Hispangu/pronombres.html)
- [Gramática](https://lucumur.github.io/Hispangu/gramatica.html)
- [Fonología](https://lucumur.github.io/Hispangu/fonologia.html)
- [Historia](https://lucumur.github.io/Hispangu/historia.html)

## Modo edición

Botón **✎ Editar** en la barra de navegación. Pide un token *fine-grained* de GitHub
(solo el repo `Hispangu`, permiso **Contents: Read and write**), que se guarda únicamente
en tu navegador. Con el modo activo puedes añadir y editar raíces, vocablos y morfemas
desde la propia página; cada guardado es un commit en `main` que ya incluye
`lexico/index.json` regenerado.

## Alfabeto

El orden alfabético vive en `alfabeto.json` (pares `[letra, clave]`). Para cambiarlo:

```
python scripts/set_alphabet.py
```

Crea los `lexico/<clave>.json` que falten y actualiza `editor.js`, `lexico.html` e `index.json`.

## Estructura

- `lexico/<letra>.json` — raíces por letra, cada una con sus vocablos.
- `lexico/morphemes.json` — morfemas.
- `lexico/index.json`, `history*.json` — generados por los workflows; no editar a mano.
- `textos/index.json` — textos y traducciones (ver `textos/README.md`).
- `scripts/validate_lexicon.py` — validación (corre en cada push).
