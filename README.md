# AI-assisterad behandling av forskningsartiklar general v1

Detta repo är en ren omstart för en generell, återanvändbar pipeline för AI-stödd evidensextraktion ur forskningsartiklar.

Utgångspunkten är arkitekturen i [docs/architecture/alternativ-plan-v1.md](docs/architecture/alternativ-plan-v1.md). Det gamla repot används inte som kodbas. Endast etablerade arbetssätt återanvänds: körningsmanifest, evidensspårbarhet, kostnadstänk, strukturerade AI-svar och testdisciplin.

## Grundprinciper

- Processa varje artikel en gång till en kanonisk, återanvändbar representation.
- Identifiera artiklar med `doc_id = sha256(file_bytes)`, inte filnamn eller sökväg.
- Lagra artikelstruktur, referenser, frågor, svar och evidens som separata dataobjekt.
- Använd SQL/relationer för deterministiska frågor och LLM för texttolkning.
- Håll frågor i data (`questions.yaml` eller Excel-import), inte hårdkodat i pipeline.
- Spara alla svar med provenance: artikel, sektion, sida och citat.

## Första målbild

M0 i detta repo är ett rent, testbart skelett:

- modulstruktur enligt den nya planen
- Pydantic-modeller för kärnobjekten
- ingest/discovery med stabilt innehållsbaserat `doc_id`
- CLI-bas
- tester som verifierar startkontrakten

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

## CLI

```powershell
article-analysis-general doctor
article-analysis-general discover --corpus Forskning
```

## Repo-status

Detta är ett M0-skelett. GROBID, Docling/PyMuPDF4LLM, OpenAlex, Crossref, Unpaywall, SQLite/DuckDB-index och frågemotor implementeras i efterföljande milestones enligt [docs/implementation-roadmap.md](docs/implementation-roadmap.md).
