# Résumé (LaTeX source)

Two-page, single-column (ATS-friendly) résumé, built with the [AltaCV](https://github.com/liantze/AltaCV) class.

## Build

```bash
pdflatex -interaction=nonstopmode main.tex
```

Built PDFs live in `pdf/` (Montreal and Vancouver versions; only the header location differs). The site serves `../Alireza_Toghiani_Resume.pdf` (Montreal) for the "Download Résumé" button.

## Structure

- `main.tex`: layout and section order
- `sections/`: summary, skills, one file per role, and `extras.tex` (awards, education, volunteer)
- `backup/two-column-2025/`: previous two-column version, kept for reference
