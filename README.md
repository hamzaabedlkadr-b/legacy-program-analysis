# COBOL Control Flow Analysis

This repository contains the inputs, scripts, intermediate JSON artifacts, and final generated outputs used to analyze the `PDCBVC` COBOL program.

## Layout

```text
inputs/
  cobol/        Source COBOL programs
  bms/          BMS maps
  copybooks/    Copybook files
  mapa/         MAPA sample inputs

scripts/
  pipeline/     Main transformation and generation scripts
  validation/   QA and inspection scripts
  utils/        Utility helpers

artifacts/
  intermediate/ Working JSON artifacts
  final/        Generated final outputs and builders
  reports/      Reports and report assets

docs/           Notes and reference material
archive/        Older snapshots and experimental leftovers
```

## Common Commands

Build semantic rules from the current enriched graph:

```powershell
python scripts\pipeline\extract_pdc_rules.py
```

Generate business-rule RAG documents:

```powershell
python scripts\pipeline\generate_rag_documents.py
```

Run the full batch pipeline with the repo's current sample inputs:

```powershell
python scripts\pipeline\run_batch_pipeline.py `
  --cobol-dir inputs\cobol `
  --copy-dir inputs\copybooks `
  --pdc-json-dir artifacts\intermediate\pdc.json `
  --mapa-result inputs\mapa\result.txt `
  --script3 scripts\pipeline\script3.py `
  --out-root artifacts\final\batch_output
```

Run the batch pipeline when all MAPA result files live in one folder:

```powershell
python scripts\pipeline\run_batch_pipeline.py `
  --cobol-dir C:\path\to\cobol `
  --copy-dir C:\path\to\copybooks `
  --pdc-json-dir C:\path\to\pdc_json_folder `
  --mapa-batch-dir C:\path\to\mapa_all_folder `
  --out-root artifacts\final\batch_output
```

Generate one `pdc.json`-style file per COBOL program without the control-flow extension:

```powershell
python scripts\pipeline\cbl_folder_to_pdc_no_extension.py `
  --cobol-dir C:\path\to\cobol `
  --out-dir C:\path\to\pdc_no_extension_folder
```

Compare two folders of PDC JSONs and write a structural report:

```powershell
python scripts\utils\compare_pdc_folders.py `
  --left C:\path\to\extension_pdc_folder `
  --right C:\path\to\pdc_no_extension_folder `
  --left-label extension `
  --right-label no_extension `
  --report artifacts\reports\compare_pdc_folders.txt
```

Compare two folders and write a log of exact matches vs differences:

```powershell
python scripts\utils\compare_folders.py `
  --left path\to\folder_a `
  --right path\to\folder_b `
  --log artifacts\reports\folder_compare.log
```

Compare two folders by line count and the text before the first comma on each line:

```powershell
python scripts\utils\compare_folders_line_prefix.py `
  --left path\to\folder_a `
  --right path\to\folder_b `
  --log artifacts\reports\folder_compare_line_prefix.log
```
