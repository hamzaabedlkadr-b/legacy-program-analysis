# COBOL Control Flow Analysis

This repository contains the inputs, scripts, intermediate JSON artifacts, and final generated outputs used to analyze the `PDCBVC` COBOL program.

## Start Here

- Repo map and cleanup rules: [REPO_ORGANIZATION.md](REPO_ORGANIZATION.md)
- Full project handoff for a new AI/chat: [PROJECT_HANDOFF_ROADMAP.md](PROJECT_HANDOFF_ROADMAP.md)
- Current roadmap stage tracker: [PROJECT_STAGE_TRACKER.md](PROJECT_STAGE_TRACKER.md)
- Put new COBOL inputs here: [input](input/README.md)
- Non-active material lives here: [unused](unused/README.md)

## Current Layout

```text
input/                                  main place for COBOL inputs
artifacts/final/final_scripts/output/   generated analysis and RAG outputs
artifacts/final/final_scripts/work/     generated working packages
unused/                                 archived non-pipeline material
scripts/pipeline/                       main pipeline and RAG builders
scripts/utils/                          helper scripts
docs/                                   active reports and notes
tests/                                  checks and sample tests
```

The old `inputs/` folder and the old deep `artifacts/final/final_scripts/input/` location are historical. For current work, use root `input/`.

## Add A Program

Copy the template:

```text
input/_PROGRAM_TEMPLATE/
```

Rename the copy to the program name and add:

```text
<PROGRAM>.CBL
<PROGRAM>_result.txt or <PROGRAM>_result.csv
<PROGRAM>_controlflow.json
copybooks/
jcl/                  optional
knowledge-base_rag/   optional, only for combined mode
```

## Common Commands

Run Hamza-only analysis for one program:

```powershell
python scripts\pipeline\run_fixed_input.py --program PDCBVC --mode my
```

Run combined Hamza + cobol-rekt analysis for one program:

```powershell
python scripts\pipeline\run_fixed_input.py --program PDCBVC --mode combined
```

Run both outputs:

```powershell
python scripts\pipeline\run_fixed_input.py --program PDCBVC --mode both
```

Prepare fixed-input program folders from separate source folders:

```powershell
python scripts\pipeline\prepare_fixed_input_layout.py `
  --cbl-dir C:\path\to\cbl_folder `
  --controlflow-dir C:\path\to\controlflow_json_folder `
  --result-path C:\path\to\result_files_folder `
  --copybooks-dir C:\path\to\copybooks_folder `
  --output-root input
```

Use this PC for deterministic pipeline/code checks. Run Ollama, embeddings, Chroma sync, and model-answer tests on the friend PC.
