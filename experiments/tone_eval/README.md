# Evaluacija analize tona (`experiments/tone_eval`)

Formalna evaluacija LLM analize tona na rucno oznacenom skupu srpskih vesti.
Prati primedbu 6 iz recenzije diplomskog rada.

## Postupak

1. **Dopuna analiza.** Vecina clanaka u bazi ima `provider='random'`
   (razvojna strategija). Za evaluaciju su potrebni clanci sa stvarnom LLM
   analizom, pa se ona dopunjuje:

   ```powershell
   $env:TONE_ANALYSIS_PROVIDER="groq"
   .\.venv\Scripts\python.exe -m experiments.tone_eval.backfill_model_analyses --limit 500 --concurrency 3
   ```

   Neuspele pozive (ogranicenje broja zahteva kod dobavljaca) skripta preskace;
   ponovnim pokretanjem se obradjuju u sledecem prolazu.

2. **Izgradnja skupa.** Stratifikovan uzorak po predvidjenoj klasi modela,
   determinisan `--seed`:

   ```powershell
   .\.venv\Scripts\python.exe -m experiments.tone_eval.build_dataset --per-class 30
   ```

   Nastaju dve datoteke:
   - `datasets/tone_items.jsonl` — naslov, sazetak, izvor i kategorija,
     **bez oznake modela** (to vidi ocenjivac);
   - `datasets/tone_model_labels.jsonl` — skrivene oznake i procenti modela.

3. **Rucno oznacavanje.** Svaki ocenjivac radi nezavisno, na svom portu:

   ```powershell
   .\.venv\Scripts\python.exe -m experiments.tone_eval.serve_annotation --annotator ocenjivac_a --port 8777
   .\.venv\Scripts\python.exe -m experiments.tone_eval.serve_annotation --annotator ocenjivac_b --port 8778
   ```

   Oznake se upisuju u `datasets/tone_labels_<ocenjivac>.jsonl` posle svakog
   odgovora, pa se rad moze prekidati i nastavljati.

4. **Evaluacija.**

   ```powershell
   .\.venv\Scripts\python.exe -m experiments.tone_eval.evaluate --first ocenjivac_a --second ocenjivac_b
   ```

   Ispisuje i upisuje u `results/tone_eval.json`:
   - posmatrano slaganje i **Koenov kapa** izmedju ocenjivaca,
   - matricu slaganja ocenjivaca,
   - sastav referentnog skupa,
   - tacnost, **preciznost / odziv / F1 po klasi**, macro-F1 i matricu
     konfuzije modela u odnosu na konsenzusne oznake.

## Metodoloske napomene

- **Dominantan ton.** Model vraca tri procenta. Za poredjenje sa ljudskom
  oznakom uzima se klasa sa najvecim procentom. Procenti se ne tumace kao
  kalibrisane verovatnoce.
- **Konsenzus.** Referentni skup cine samo stavke na kojima su se oba
  ocenjivaca nezavisno slozila; sporne se iskljucuju i njihov broj se izvestava.
- **Stratifikacija.** Uzorak je izjednacen po klasama modela, pa izmerena
  tacnost **nije** procena tacnosti na celom korpusu, u kome neutralna klasa
  ubedljivo preovladjuje. Stratifikacija je izabrana da pozitivna klasa, koja
  je u korpusu retka, uopste bude merljiva.

## Struktura

```
models/       ToneLabel, EvaluationItem, ClassMetrics, AgreementReport, ConsensusResult
services/     ToneBackfillService, StratifiedSampleBuilder, AgreementCalculator,
              ClassificationMetricsCalculator, ConsensusBuilder
repositories/ ToneEvaluationRepository
annotation/   index.html (stranica za oznacavanje)
datasets/     ulazni skup i oznake ocenjivaca
results/      tone_eval.json
```
