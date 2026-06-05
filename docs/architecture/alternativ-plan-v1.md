# Alternativ-plan (konsoliderad): AI-stödd evidensextraktion ur forskningsartiklar

> Alternativ lösningsskiss utifrån `Uppgift_alternativ_beskrivning.txt` — bortser
> från den befintliga pipelinen. Konsoliderad version som väver in det bästa från
> Codex-planen (`alternativ-plan--20260604--Codex.md`). Datum: 2026-06-04.

## Context

Uppgiften är att tänka om lösningen för att gå igenom forskningsartiklar, plocka
ut deras delar, och svara på frågeställningar — där **både artiklarna och
frågorna kan bytas ut över tid**.

Empirisk grund från korpusen (46 PDF:er i `Forskning/`, ämne: mild
intellektuell funktionsnedsättning / skola→arbete):

- **Strukturen är genomgående IMRaD** (Abstract → Introduktion → Metod →
  Resultat → Diskussion → Referenser). 39/46 öppnades rent och visar denna
  uppdelning. Tillräckligt likt för att utnyttja — men inte garanterat.
- **Verkligheten är stökig och måste hanteras:** 1 inskannad PDF utan textlager
  (`2005_Neurodevelopmental_outcome_at.PDF`, 0 tecken → kräver OCR), 7 filer
  failade pga filnamn med dubbla mellanslag/OneDrive-unicode (→ robust ingest),
  längd 5–195 sidor (median 13; 195-sidorsfilen är sannolikt en avhandling, inte
  en artikel), ~hälften har strukturerade abstracts.
- `Frågeställningar.xlsx` är en **extraktionsmatris** (8 frågor i header, inga
  ifyllda rader): filnamn, inklusionskriterium ("svag begåvning"), titel,
  författare, år, syfte, datakälla (enkät/intervju/annat), huvudresultat.

**Kärnidé (det som löser "byts ut över tid"):** *Frikoppla dokument från frågor.*
Processa varje artikel **en gång** till en rik, återanvändbar representation.
Kör sedan vilken frågeuppsättning som helst billigt och upprepat mot den. Ny
artikel = en inkrementell ingest. Ny frågeuppsättning = ett nytt pass över
befintliga data — ingen omprocessning.

**Valda ramar (från avstämning):** hybrid (lokal GROBID + öppna API:er, Azure
vid behov), pragmatisk kärna som växer till plattform, citeringsanalys med från
start. Skala 10–100 artiklar. Första leveransen är en körbar kärna, inte ett
färdigt produktionssystem.

---

## Övergripande arkitektur

```
PDF → [0 Ingest] → [1 Parse+Enrich] → [2 Bygg lager] → [3 Frågemotor] → [4 Output+QA]
                                          │
              ┌───────────────────────────┼───────────────────────────┐
        Kanonisk record              Relationsindex              AI-lager / vektor
        (JSON per artikel)           + citeringsgraf             (RAG) — fas 2
        = källa till sanning         (SQLite/DuckDB)             defererad men förberedd
```

Tre representationer per artikel, alla nycklade på ett **stabilt doc_id =
sha256 av filinnehållet** (inte filnamnet — filnamnen är opålitliga):

1. **Kanonisk record (JSON)** — källa till sanning. Identitet, bibliografi,
   sektioner (best-effort), referenser, normaliserad fulltext + sidkarta,
   provenance (sid/offset) för allt.
2. **Relationsindex (SQLite/DuckDB)** — en rad per artikel + `article_references`-
   kantabell (citing→cited) + `authors`-tabell. Driver de *deterministiska*
   frågorna (år, antal, citeringsnätverk, delade författare) — låt SQL göra det
   SQL gör bäst, inte LLM.
3. **AI-lager / vektorindex (fas 2)** — sektionsmedvetna chunkar + embeddings
   för ad-hoc semantiska frågor tvärs korpusen. Designas in nu, byggs senare.
   **Hybrid retrieval** (metadatafilter + semantisk + keyword) ger bäst precision.
   Två vägar beroende på stack:
   - **Azure-väg (matchar repot):** Azure AI Search (vektor + keyword + filter)
     med Azure OpenAI embeddings.
   - **OpenAI-väg (snabb genväg):** OpenAI Vector Stores / File Search — tar PDF
     direkt, semantisk + keyword-sökning med metadatafilter, minimal egen drift.

---

## Datamodell (entiteter)

Konkret schema för den kanoniska recorden + relationsindexet (Pydantic →
SQLite/DuckDB). Minsta uppsättning objekt:

- **`Article`** — `doc_id` (sha256), fil, källdatabas (ERIC/SCOPUS/PSYCH INFO),
  titel, författare, år, DOI, venue, abstract, extraktionsstatus, confidence.
- **`Section`** — originalrubrik, normaliserad typ (abstract/intro/metod/
  resultat/diskussion/slutsats/övrigt), rubriknivå, sidintervall, text, offsets.
- **`Chunk`** — sektionsmedvetet textstycke + metadata (doc_id, section, sida)
  för embeddings/RAG.
- **`Reference`** — rå referenstext, parserade fält, upplöst id (DOI/PMID/
  OpenAlex/Semantic Scholar), matchnings-confidence, relation till citerande artikel.
- **`ExternalWork`** — externt verk (citerat/citerande) med författare,
  institutioner, år — noder i citeringsgrafen.
- **`Question`** — frågetext, metod (sql/long-context/rag), svarsschema, version.
- **`Answer`** — `value`, koppling till Question + Article, modell, confidence/not_found.
- **`Evidence`** — citat + sida/sektion/offset som backar varje Answer.

`Reference` + `ExternalWork` är det som ger citeringsnätverket (vem citerar vem,
delade författare, co-citation) via SQL.

---

## Pipeline-faser

### Fas 0 — Ingest & normalisering
- Robust fildiscovery som tål dubbla mellanslag/unicode (`os.walk` + `Path`,
  normalisera NFC). Logga filer som inte går att öppna istället för att krascha.
- `doc_id = sha256(file_bytes)`. Bevara originalfilnamn + källdatabas som metadata.
- Textextraktion med **PyMuPDF**. Om utvunnen text < tröskel (t.ex. < 1500
  tecken eller < 100 tecken/sida) → flagga som inskannad → OCR-väg.

### Fas 1 — Parse & enrich
- **Sektionering:** GROBID lokalt (Docker) → TEI-XML med titel/författare/
  abstract/sektioner/referenser/citation contexts. Fallback för svåra PDF:er
  (tabeller, tvåspalt, layoutbrus): **Docling** eller **PyMuPDF4LLM**
  (markdown-medveten), sist heuristisk IMRaD-split på rå PyMuPDF-text.
- **OCR (endast vid behov):** se beslutsguide nedan.
- **DOI-resolution:** ur PDF-metadata/text, annars Crossref-titelsökning.
- **Citeringsberikning (med från start):** slå upp artikeln i **OpenAlex** via
  DOI → hämta `referenced_works` (utgående), `cited_by` (inkommande),
  disambiguerade författare (ORCID/institution), topics. Ger nätverksfrågorna
  (vem citerar vem, samförfattare, co-citation) nästan gratis.
- **Open access-länkar:** **Unpaywall** (gratis, e-postparameter) ger laglig
  OA-fulltextlänk per DOI — användbart när ett citerat verk saknas som PDF lokalt.

### Fas 2 — Bygg lager
- Skriv kanonisk record (JSON) per artikel.
- Fyll relationsindex + citeringskanter + författartabell.
- (Fas 2-tillägg) chunk + embed → vektorindex/AI-lager (hybrid retrieval).

### Fas 3 — Frågemotor (method routing)
Ladda frågeuppsättningen från `Frågeställningar.xlsx` (eller en `questions.yaml`).
Varje fråga taggas med en **metod**, så rätt verktyg används:

| Frågetyp | Metod | Exempel ur matrisen |
|---|---|---|
| Bibliografisk/strukturell | direkt ur record/SQL | filnamn, titel, författare, år |
| Innehållsextraktion (per artikel) | **long-context + structured output** | syfte, datakälla, huvudresultat |
| Screening (ja/nej + motivering) | long-context + structured output | inklusionskriterium "svag begåvning" |
| Aggregat/nätverk (tvärs korpus) | SQL över relationsindex | "vilka delar referenser?", "samma författare?" |
| Öppen semantisk (ad-hoc) | RAG / hybrid retrieval (fas 2) | framtida fritextfrågor |

- **Per-artikel-extraktion: long-context, inte chunkad RAG.** Median 13 sidor
  ryms i ett modernt long-context-fönster → enklare och högre kvalitet än
  chunkning för enskild-dokument-extraktion. RAG/hybrid reserveras för korpus-
  breda ad-hoc-frågor.
- **Structured output (JSON-schema)** per fråga. Varje svar returnerar
  `value` + `evidence` (citat + sid/sektion) + `confidence`/`not_found`. Styr
  hallucinationer och ger spårbarhet.
- **Prompt caching:** cachea artikelns text en gång, variera frågan → billigt
  att köra många frågor mot samma artikel (matrisens 8+ kolumner).
- Frågorna lever i data (yaml/xlsx), inte i kod → ändra en fråga = ändra en rad.

### Fas 4 — Output & QA
- Skriv matrisen tillbaka till `Resultat.xlsx` (en rad/artikel) **med
  per-cell-provenance** (sid/sektion) i kommentar eller separat blad.
- Review-steg: flagga låg `confidence`/`not_found` för mänsklig granskning
  istället för att dölja osäkra extraktioner.
- **Run-manifest:** modell, prompt-version, frågeuppsättnings-version, kostnad,
  tidsstämpel (samma mönster som befintliga `runs/<timestamp>--<label>/`).

---

## Beslutsguide: lokal extraktion vs Azure

"Behöver vi Azure för detta?" — **Nej, inte för grundfallet.** Lokalt räcker för
~39/46. Azure tillför mest värde i specifika lägen:

| Situation | Bäst val | Varför |
|---|---|---|
| Vanlig digital artikel med textlager (majoriteten) | **PyMuPDF + GROBID lokalt** | Gratis, snabbt, ingen datadelning, hög kvalitet |
| Inskannad/bild-PDF (t.ex. 2005-filen) | **Azure Document Intelligence** (`prebuilt-layout`) *eller* lokalt `ocrmypdf`/Tesseract | Behöver OCR; Azure ger OCR+layout i ett |
| Komplexa layouter (flerkolumn, tabeller) | **Docling/PyMuPDF4LLM** lokalt, annars Azure Document Intelligence | Docling hanterar tabeller/layout väl lokalt; Azure när det krävs ännu bättre |
| Vill undvika egen drift helt | Azure för parsing+OCR | Slipper hosta GROBID |
| Integritetskänsligt / offline-krav | Allt lokalt | Inget lämnar maskinen |

Rekommendation: **lokal väg som default, Azure Document Intelligence som
selektiv fallback** när text-tröskeln i Fas 0 säger "inskannad" eller
GROBID/Docling ger dålig struktur. LLM-extraktionen (Fas 3) kör ändå på Azure OpenAI.

---

## Referens-/citeringsdata: API-jämförelse (fråga 2c)

Parsa **inte** enbart PDF:ens referenslista (stökigt). Resolva till DOI och hämta
ren strukturerad data:

| Tjänst | Kostnad | Vad man får | Not |
|---|---|---|---|
| **OpenAlex** (ryggrad) | Gratis nyckel krävs (sedan feb 2026); $1/dag fri användning ≈ 100k credits — single-lookups gratis, list=10 / search=100 / PDF=1000 credits; förbetald överanvändning. `mailto`/polite pool borttaget | Metadata, disambiguerade författare (ORCID/institution), `referenced_works` **och** `cited_by`, topics; hela DB nedladdningsbar | Bästa default — citeringsgraf i båda riktningar |
| **Crossref** | Gratis, ingen nyckel (betald **Metadata Plus** för hög volym/SLA) | Bibliografisk metadata + referenser *där förlaget deponerat dem* (ofullständig täckning) | Bra för DOI-resolution |
| **Semantic Scholar** | Gratis; många endpoints är publika men rate-limitade, API-nyckel rekommenderas och ger andra gränser | Citeringar + **citeringskontext/-intent**, SPECTER2-embeddings, TLDR | Bra för citeringskontext + färdiga embeddings |
| **OpenCitations** | Gratis, öppet | Endast citeringslänkar | Komplement |
| **Unpaywall** | Gratis (e-postparameter) | OA-fulltextlänk per DOI | Hämta lagliga PDF:er för citerade verk |
| **Scopus/Elsevier** | Kräver institutionsprenumeration + nyckel | Rik men licensierad, omdistribution begränsad | Korpusen speglar Scopus-sökningar men undvik beroendet i ett återanvändbart verktyg |
| **Dimensions / Lens.org** | Kommersiell/freemium | Rik citeringsdata | Betalt vid skala |

**Val:** OpenAlex som ryggrad (löser fråga 2c helt), Crossref för DOI-fallback,
Semantic Scholar valfritt för citeringskontext/embeddings, Unpaywall för OA-PDF:er.

**Roller i M3-kedjan:** **Crossref** = DOI + bibliografisk metadata (ankaret från
stökig PDF till DOI), **OpenAlex** = citeringsgrafen (`referenced_works`/`cited_by`
+ disambiguerade författare), **Unpaywall** = laglig OA-fulltext per DOI (mest för
citerade verk utanför den lokala korpusen). Nyckel/e-post: OpenAlex kräver nyckel;
Crossref `mailto` (frivilligt); Unpaywall e-post (krävs).

---

## Filstruktur att skapa (pragmatisk kärna)

Ny, fristående modulstruktur (återanvänder gärna befintlig Azure-klient +
kostnadsspårning + `runs/`-manifest, men arkitekturen är fri från gamla pipelinen):

- `src/ingest/discovery.py` — robust fildiscovery + doc_id (sha256) + källtagg
- `src/ingest/extract.py` — PyMuPDF text + inskannad-detektering
- `src/parse/grobid_client.py` — GROBID → TEI → sektioner/referenser
- `src/parse/fallback.py` — Docling / PyMuPDF4LLM för svåra layouter
- `src/parse/ocr.py` — Azure Document Intelligence / lokal OCR-väg
- `src/enrich/openalex.py` — DOI-resolution + referenser/cited_by/författare
- `src/enrich/unpaywall.py` — OA-fulltextlänkar per DOI
- `src/store/record.py` — kanonisk record (Pydantic: Article/Section/Chunk/
  Reference/ExternalWork/Question/Answer/Evidence)
- `src/store/index.py` — SQLite/DuckDB: artiklar + referenskanter + författare
- `src/questions/schema.py` — ladda frågeuppsättning + metod-routing
- `src/questions/extract.py` — long-context + structured output + provenance
- `src/query/sql.py` — aggregat/nätverksfrågor (citerar/delar/samförfattare)
- `src/output/matrix.py` — skriv `Resultat.xlsx` + provenance + run-manifest
- `questions.yaml` — frågeuppsättning (speglar `Frågeställningar.xlsx`)
- (fas 2) `src/store/vectors.py` (Azure AI Search / OpenAI File Search),
  `src/query/rag.py` (hybrid retrieval)

---

## Verifiering (end-to-end)

1. **Ingest-robusthet:** kör Fas 0 mot hela `Forskning/` → alla 46 får doc_id,
   de 7 filnamns-failade öppnas nu, 2005-filen flaggas som inskannad.
2. **Parse (täck de svåra fallen):** GROBID på representativa typer — kvantitativ
   register-, kvalitativ intervju-, **review/meta-analys** (avvikande struktur),
   **tvåspalt + tabeller**, och referenser **utan DOI / ofullständig metadata** →
   sektioner + referenslista korrekt avgränsade; inskannad fil ger text efter OCR.
   Mät: andel korrekt hittade sektioner, andel referenser extraherade, andel
   matchade mot externa API:er.
3. **Enrich:** OpenAlex returnerar DOI, ≥1 `cited_by` och `referenced_works` för
   minst de artiklar som har DOI; verifiera att två artiklar med känd gemensam
   författare länkas i `authors`-tabellen.
4. **Frågemotor:** kör `questions.yaml` (matrisens 8 frågor) mot ett urval →
   varje cell har `value` + `evidence` (sid/sektion) + `confidence`; manuell
   spot-check mot PDF för 2–3 artiklar.
5. **Aggregat:** SQL-fråga "vilka artiklar delar minst en referens / författare?"
   ger rimligt resultat.
6. **Output:** `Resultat.xlsx` öppnas, en rad/artikel, provenance närvarande,
   run-manifest skrivet med modell + kostnad.
7. **"Byts ut över tid"-test:** lägg till en ny fråga i `questions.yaml` och kör
   om utan att processa om PDF:erna; byt in 1 ny PDF och kör inkrementell ingest.

**Acceptanskriterium:** varje svar ska kunna spåras till artikel, sektion och
textstycke; osäkra extraktioner markeras som låg confidence — aldrig döljas.

---

## Källor

- [OpenAlex API](https://developers.openalex.org/) ·
  [Crossref REST API](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/) ·
  [Semantic Scholar API](https://www.semanticscholar.org/product/api) ·
  [Unpaywall API](https://unpaywall.org/products/api) ·
  [Forskningspaper-API:er 2026](https://intuitionlabs.ai/articles/research-paper-apis-scientific-literature)
- [GROBID (struktur + referenser, TEI)](https://grobid.readthedocs.io/en/latest/Introduction/) ·
  [Docling](https://docling.site/) ·
  [PyMuPDF4LLM](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) ·
  [OpenAI File Search](https://platform.openai.com/docs/guides/tools-file-search/)
