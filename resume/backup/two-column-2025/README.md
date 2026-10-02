# Résumé (LaTeX source)

Two-page résumé for Alireza Toghiani, built with the [AltaCV](https://github.com/liantze/AltaCV) class.

## Build

```bash
pdflatex -interaction=nonstopmode main.tex
```

Output: `main.pdf`. A pre-built copy is committed as `Alireza_Toghiani_Resume.pdf` (also served at the site root for the "Download Résumé" button).

## Structure

- `main.tex` — document entry point and page layout
- `altacv.cls` — résumé class
- `sections/` — summary and one file per experience entry
- `sidebars/` — skills, education, achievements, volunteer, projects (split across page 1 / page 2)
