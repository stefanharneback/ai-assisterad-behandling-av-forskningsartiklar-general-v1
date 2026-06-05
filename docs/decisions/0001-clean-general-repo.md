# ADR 0001 - Ren generell omstart

## Beslut

Detta repo byggs från grunden enligt den konsoliderade alternativplanen. Det gamla repot kopieras inte som kodbas.

## Motivering

Den tidigare implementationen är optimerad för en specifik Excel-matris och en M1-M3-pipeline. Den nya målbilden kräver en annan kärna: kanoniska artikelrecords, artikelstruktur, referensgraf, relationsindex och datadriven frågemetodik.

## Konsekvenser

- Modulerna namnges efter den nya arkitekturen: `ingest`, `parse`, `enrich`, `store`, `questions`, `query`, `output`, `llm`, `cost`.
- Befintliga idéer kan återanvändas, men kod flyttas bara in när den passar den nya datamodellen.
- Första implementationen fokuserar på kontrakt och verifierbara små steg.

