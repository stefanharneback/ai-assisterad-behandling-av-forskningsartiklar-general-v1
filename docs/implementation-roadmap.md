# Implementation Roadmap

## M0 - Rent repo och kontrakt

- Skapa modulstruktur enligt alternativplanen.
- Lägg in arkitekturplanen som `docs/architecture/alternativ-plan-v1.md`.
- Definiera kärnmodeller: `Article`, `Section`, `Chunk`, `Reference`, `ExternalWork`, `Question`, `Answer`, `Evidence`.
- Implementera PDF-discovery och innehållsbaserat `doc_id`.
- Lägg till CLI (Command Line Interface) och första tester.

## M1 - Ingest och kanoniska artikelrecords

- Skanna `Forskning/` rekursivt.
- Deduplicera byte-identiska PDF:er till en `Article` med flera `ArticleSource`-poster.
- Skriv en JSON-record per artikel under en körningsmapp.
- Registrera källdatabas, filnamn, relativ sökväg, filhash, textlagerstatus och extraktionsstatus.
- Använd PyMuPDF i M1 för att avgöra `text_layer` (`text`, `scanned`, `unknown`) utan att ännu göra full artikelstrukturering.
- Lägg grunden för run manifest.
- Lägg grunden för usage- och kostnadsledger så modell-anrop inte införs utan spårning.
- Skriv en enkel inventory-output som gör resultatkontraktet synligt tidigt.

## M2 - Artikelmedveten parsing

- Bygg vidare på PyMuPDF och lägg till PyMuPDF4LLM som lokal text/layout-baseline.
- Lägg till GROBID-adapter för TEI, sektioner, metadata och referenser.
- Lägg till fallback-modul för svåra PDF:er.
- Lägg per-fil-diagnostik för text_layer som skiljer "öppnades men obestämd" från "kunde inte öppnas" (idag faller båda till `unknown`).
- Spara `Section` och `Chunk` med sid-/offset-provenance.
- Skriv minimal `Resultat.xlsx` med bibliografiska kolumner när parsing ger titel, författare och år.

## M3 - Referenser och metadata

- Extrahera referenser via GROBID.
- Lägg till Crossref för DOI (Digital Object Identifier)-resolution.
- Lägg till OpenAlex som huvudkälla för citeringsgraf och författardisambiguering.
- Lägg till Unpaywall för OA-fulltextlänkar.

## M4 - Relationsindex och SQL (Structured Query Language)-frågor

- Skapa SQLite/DuckDB-schema för artiklar, sektioner, `article_references`, externa verk, författare och svar.
- Implementera frågor för delade referenser, delade författare, citerade verk och citeringsrelationer.

## M5 - Frågemotor

- Inför `questions.yaml` med explicit method routing.
- Implementera `sql`, `long-context` och senare `rag` som separata metoder.
- Använd structured output och evidenskrav för alla svar från LLM (Large Language Model).

## M6 - Output, QA (Quality Assurance) och kostnader

- Skriv `Resultat.xlsx`, `results.jsonl`, `run.sqlite` och `manifest.json`.
- Lägg provenance per cell i separat blad eller kommentar.
- Lägg review-flaggor, confidence och kostnadsrapportering från befintlig ledger.

## M7 - Hybrid retrieval

- Lägg till vektorindex via Azure AI Search eller OpenAI File Search.
- Kombinera metadatafilter, keyword och semantisk sökning.
- Använd detta för korpusbreda ad-hoc-frågor.
