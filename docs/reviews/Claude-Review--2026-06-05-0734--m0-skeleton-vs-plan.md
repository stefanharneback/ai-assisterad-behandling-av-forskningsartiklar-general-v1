# Claude-Review — M0-skelett vs alternativ-plan-v1

- **Datum:** 2026-06-05 07:34 (lokal tid)
- **Repo:** `ai-assisterad-behandling-av-forskningsartiklar-general-v1`
- **Mot:** [docs/architecture/alternativ-plan-v1.md](../architecture/alternativ-plan-v1.md)
- **Git-läge:** inga commits ännu på `main` — granskningen sker *före* första commit.
- **Tester:** `python -m unittest discover -s tests` → **7/7 OK**.
- **Scope:** repo-struktur, M0-avgränsning, ev. arv från gamla repot, datamodeller,
  `doc_id`, roadmap, och ändringar inför första commit.

## Helhetsomdöme

Skelettet är välbyggt och troget planen: modulträd 1:1 mot planens filstruktur,
rena milstolpsmärkta stubbar, innehållsbaserat `doc_id` med test, rigorösa
Pydantic-modeller, inget kopierat från gamla repot, grön testsvit. **Klart för en
första commit efter att F1 åtgärdats och F3–F5 minst fått ett dokumenterat
beslut** (de rör "kontraktet" som commit:en låser in).

> **Rättelse 2026-06-05 (efter online-koll):** F2 nedan är *tillbakadragen*.
> OpenAlex kräver sedan **2026-02-13** en gratis API-nyckel; polite pool +
> `mailto` är borttagna och prismodellen är kreditbaserad. Plan-doc:184 och
> `OPENALEX_API_KEY` är alltså **korrekta**. Granskarens tidigare påstående var
> fel (kunskap t.o.m. jan 2026, precis före ändringen).

---

## Findings (prioriterat)

| # | Sev | Fil / rad | Problem | Risk | Åtgärd |
|---|-----|-----------|---------|------|--------|
| F1 | **Med** | [query/sql.py:5-15](../../src/article_analysis_general/query/sql.py) | M0-stub innehåller redan konkret M4-SQL, och tabellnamnet `references` är ett **reserverat SQL-ord**. Verifierat: `create table references ...` ger `OperationalError: syntax error` i SQLite (citerat `"references"` funkar). | SQL:en kommer att krascha när M4 byggs; schemakonventionen låses fel redan i första commit. | Antingen reducera till stub (`raise NotImplementedError("M4")`) **eller** byt tabellnamn nu till `article_references` (rekommenderas) / citera identifieraren. Sätt konventionen innan M4. |
| ~~F2~~ | ~~Med~~ → **Tillbakadragen / Low** | [.env.example:19](../../.env.example), [openalex.py](../../src/article_analysis_general/enrich/openalex.py) | **Rättat:** OpenAlex kräver sedan 2026-02-13 en gratis API-nyckel; polite pool + `mailto` är borttagna, modellen är kreditbaserad. Plan-doc:184 och `OPENALEX_API_KEY` är **korrekta**. Kvarvarande, mindre: `OPENALEX_EMAIL` är nu **obsolet** för OpenAlex, och `OpenAlexClient`-stubben tar `email` men bör i M3 skicka **nyckeln**. | Liten — obsolet env-var + kreditbudget att planera för. | Ta bort `OPENALEX_EMAIL`; låt `OpenAlexClient` ta `api_key` som primär (header/param); notera kreditkostnad i M3-kostnadslogg (list=10 credits, 100k credits/dag gratis). |
| F3 | **Med** | [store/record.py:23-90](../../src/article_analysis_general/store/record.py) | Ingen förstklassig `Author`-entitet trots att planen upprepat lyfter författar-disambiguering och en `authors`-tabell för "delade författare". Författare lagras som `list[str]` på Article/Reference/ExternalWork. | Fritextnamn går inte att joina tillförlitligt → "samma författare?"-frågorna (kärnmål) blir opålitliga. | Lägg `Author` (namn, `openalex_id`, `orcid`) + koppling artikel↔författare, eller fatta uttryckligt beslut att skjuta till M3/M4 och notera i roadmapen. Påverkar kontraktet → besluta före commit. |
| F4 | **Med** | [ingest/discovery.py:23-37](../../src/article_analysis_general/ingest/discovery.py) | `doc_id == sha256(bytes)`. Två byte-identiska PDF:er i olika databasmappar (samma artikel indexerad i SCOPUS *och* ERIC — sannolikt i denna korpus) ger två `Article` med **samma `doc_id`** men olika `relative_path`/`source_database`. | Vid doc_id-nycklad lagring (M1+) krockar/skrivs poster över; en av källorna tappas. | Detektera dubbletter i discovery (varna/dedup), och låt `Article` representera flera källor (t.ex. `sources: list[...]`) eller medvetet "first-wins + logg". Besluta före M1. |
| F5 | **Med** | [store/record.py:23-38](../../src/article_analysis_general/store/record.py) vs [roadmap M1](../implementation-roadmap.md) | `Article` saknar `text_layer`/`is_scanned` och `topics`. Roadmap M1 lovar registrera "textlagerstatus", men fältet finns inte och PyMuPDF (som behövs för att avgöra det) införs först i M2. | M1 kan inte uppfylla sitt eget kontrakt; planens Fas 0 "flagga inskannad" tappas; 2005-filen (känd scanned) fångas inte. | Lägg `text_layer: Literal["text","scanned","unknown"]` på Article och flytta PyMuPDF-textextraktion till M1 (eller flytta textlagerstatus till M2). |
| F6 | Low | [roadmap M5-M6](../implementation-roadmap.md) | Första användbara `Resultat.xlsx` kommer först i M6; ingen tidig tunn vertikal som ger de rent bibliografiska kolumnerna (filnamn/titel/författare/år) utan LLM. | Lång väg innan verktyget producerar det användaren faktiskt vill ha; output-kontraktet valideras sent. | Dra fram en minimal output redan vid M1/M2 (bib-kolumner från discovery+parse). |
| F7 | Low | [README.md:30](../../README.md), [docs/operations/local-dev.md](../operations/local-dev.md) | Aktiveringssökväg renderas med dubbla backslash: `.\\.venv\\Scripts\\Activate.ps1`. | Kopiera-klistra ger fel sökväg. | Byt till enkel backslash `.\.venv\Scripts\Activate.ps1`. |
| F8 | Low | [store/record.py:41-63](../../src/article_analysis_general/store/record.py) | `Section` har inline `start_offset/end_offset/page_*`, medan `Chunk`/`Evidence` använder `Provenance`. | Inkonsekvent provenance-modell → dubbla kodvägar senare. | Överväg att låta `Section` också bära `Provenance` (eller motivera skillnaden). |
| F9 | Low | [questions/schema.py](../../src/article_analysis_general/questions/schema.py) | `validate_question_set` är enda beteendelogiken utöver discovery/modeller utan test. | Regressionsrisk när M5 bygger vidare. | Lägg ett litet test (unik/dubbel `question_id`). |
| F10 | Low | [pyproject.toml](../../pyproject.toml) | `pytest` hittar inte `src` utan `PYTHONPATH`; README använder unittest-workaround. | DX-friktion; `python -m pytest` "bara funkar" inte utan editable install. | Lägg `[tool.pytest.ini_options] pythonpath = ["src"]` (eller dokumentera att `pip install -e` krävs först). |
| F11 | Info | plan "Filstruktur" vs träd | `src/ingest/extract.py` (PyMuPDF-text + scanned-detektering) saknas. | Ingen — medveten M2-deferral. | Spårad avvikelse; inget krav nu (kopplad till F5). |

---

## Bedömning per fråga

**1. Stödjer repo-strukturen planen?** Ja. `ingest / parse(grobid_client, fallback,
ocr) / enrich(openalex, crossref, unpaywall) / store(record, index) /
questions(schema, extract) / query(sql, rag) / output(matrix) / llm / cost` mappar
1:1 mot planens "Filstruktur att skapa". Korrekt `src`-layout, konsolerat CLI-entry,
`questions.yaml` och `store/vectors.py` korrekt frånvarande (senare milstolpar).
Enda strukturgapet: `ingest/extract.py` (F11, avsiktligt).

**2. Är M0-skelettet rätt avgränsat?** Mestadels ja — stubbar kastar
`NotImplementedError` med milstolpsnummer, och M0-leverablerna (modulträd,
Pydantic-modeller, discovery+`doc_id`, CLI, tester) finns och är gröna. **Undantag:
F1** — `query/sql.py` läcker konkret M4-logik (med latent bugg) in i M0.

**3. Har något följt med olämpligt från gamla repot?** Nej. ADR
[0001](../decisions/0001-clean-general-repo.md) dokumenterar ren omstart; stubbarna
är nyskrivna, `llm/` och `cost/` är tomma platshållare (ingen kopierad klient).
Det enda återanvända är *konventioner* (reasoning-effort, pris-JSON, runs-manifest i
`.env.example`) vilket planen uttryckligen tillåter — lämpligt. (`OPENALEX_API_KEY`
är korrekt — se rättelsen i F2.)

**4. Matchar datamodellerna planens mål?** I hög grad — alla åtta entiteter
(Article, Section, Chunk, Reference, ExternalWork, Question, Answer, Evidence) +
`Provenance` finns, med `extra="forbid"`, `validate_assignment` och `confidence`
∈ [0,1]. Luckorna rör citeringsmålen och Fas 0: ingen `Author`-entitet (F3), ingen
textlagerstatus/topics på Article (F5), och `cited_by`/lokal återkoppling av
`external_work_id`→`doc_id` är inte modellerad (täcks rimligen i M4, men värt en rad i schemat).

**5. Är `doc_id` verkligen innehållsbaserat?** Ja. [discovery.py:40-45](../../src/article_analysis_general/ingest/discovery.py)
strömmar `sha256` över filens bytes; `test_doc_id_is_based_on_file_bytes_not_path`
bevisar att olika sökväg + samma bytes ⇒ samma id. Enda nyansen är dedup-krocken i F4.

**6. Är roadmapen rimlig?** Ja — M0→M7 är en logisk, inkrementell sekvens
(skelett → ingest/records → parsing → referenser/metadata → relationsindex →
frågemotor → output/QA → hybrid retrieval). Justeringar: tidig tunn output-slice
(F6) och sekvenskrocken textlagerstatus M1 vs PyMuPDF M2 (F5).

**7. Ändringar före första commit:** se F1–F2 (åtgärda), F3–F5 (minst dokumentera
beslut — de låser kontraktet), F7/F10 (snabba). F6/F8/F9 kan tas som uppföljning.

---

## Rekommenderad ordning före commit

1. **F1** — gör `query/sql.py` till ren stub *eller* döp om tabellen till `article_references`.
2. **F2 (tillbakadragen)** — inget nyckelkrav att rätta (repo korrekt); ta bort obsolet `OPENALEX_EMAIL`.
3. **F3–F5** — fatta och notera beslut om `Author`-entitet, `doc_id`-dedup och
   `Article.text_layer`/`topics` (lägg fälten nu om ni vill undvika en tidig modellbrytande ändring).
4. **F7, F10** — trivial doc-/DX-fix.
5. Commit M0 (allt är untracked; `.gitignore` täcker `__pycache__/`, `*.pyc`,
   `.env`, `Forskning/`, `runs/`, `data/` — verifierat).

## Verifiering som kördes

- `python -m unittest discover -s tests -v` → 7 passerade.
- SQLite-prov: `create table references (...)` → syntaxfel; `"references"` → OK (underlag för F1).
- `git status` → inga commits; inga spårade `.pyc`/`.env`/PDF:er.
