# AI-assisterad behandling av forskningsartiklar general v1

Detta repo är en ren omstart för en generell, återanvändbar pipeline för AI-stödd evidensextraktion ur forskningsartiklar.

Utgångspunkten är arkitekturen i [docs/architecture/alternativ-plan-v1.md](docs/architecture/alternativ-plan-v1.md). Det gamla repot används inte som kodbas. Endast etablerade arbetssätt återanvänds: körningsmanifest, evidensspårbarhet, kostnadstänk, strukturerade AI-svar och testdisciplin.

## Grundprinciper

- Processa varje artikel en gång till en kanonisk, återanvändbar representation.
- Identifiera artiklar med `doc_id = sha256(file_bytes)`, inte filnamn eller sökväg.
- Lagra artikelstruktur, referenser, frågor, svar och evidens som separata dataobjekt.
- Använd SQL (Structured Query Language)/relationer för deterministiska frågor och LLM (Large Language Model) för texttolkning.
- Håll frågor i data (`questions.yaml` eller Excel-import), inte hårdkodat i pipeline.
- Spara alla svar med provenance: artikel, sektion, sida och citat.

## Nuvarande målbild

Repo:t har gått förbi det första M0-skelettet. Nuvarande kärna omfattar:

- modulstruktur enligt den nya planen
- Pydantic-modeller för kärnobjekten
- ingest/discovery med stabilt innehållsbaserat `doc_id`
- deduplicering av byte-identiska PDF:er till en artikel med flera källor
- `text_layer`-detektion med PyMuPDF
- run manifest, JSON-records och `inventory.csv`
- lokal M2-baseline som kan extrahera text, sektioner och chunks med provenance
- tester som verifierar kontrakten

## Lokal utveckling

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

Utan installerat paket kan de initiala testerna också köras med standardbiblioteket:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests
```

## Command Line Interface (CLI)

```powershell
article-analysis-general doctor
article-analysis-general discover --corpus Forskning
article-analysis-general ingest --corpus Forskning --out runs
article-analysis-general ingest --corpus Forskning --out runs --parse-local
```

## Repo-status

M0 är klart och M1 är implementerat som körbar ingest-kärna. M2 har en lokal PyMuPDF-baseline för text, sektioner och chunks via `--parse-local`; GROBID, PyMuPDF4LLM/Docling och OCR (Optical Character Recognition) är fortfarande nästa parsersteg. OpenAlex, Crossref, Unpaywall, SQLite/DuckDB-index och frågemotor implementeras i efterföljande milestones enligt [docs/implementation-roadmap.md](docs/implementation-roadmap.md).
