# Repository Organization

This repo is the analysis side of the COBOL RAG project.

Use this file when the repo feels crowded. It explains what each folder is for, where to put new files, and which folders are generated.

## Daily Working Locations

### Put COBOL Program Inputs Here

```text
input/
```

This is the most important folder for normal work. Each program gets one folder:

```text
input/
  <PROGRAM>/
    <PROGRAM>.CBL
    <PROGRAM>_result.txt or <PROGRAM>_result.csv
    <PROGRAM>_controlflow.json
    copybooks/
    jcl/                  optional
    knowledge-base_rag/   optional for combined mode
```

There is a template here:

```text
input/_PROGRAM_TEMPLATE/
```

Loose shared JCL files that are not used by the current PDCBVC run were moved here:

```text
unused/input_samples/_shared/jcl/
```

Scratch COBOL/copybook files that are not packaged as active inputs were moved here:

```text
unused/input_samples/_scratch/
```

### Unused / Non-Pipeline Material

```text
unused/
```

This keeps old, generated, or non-pipeline material out of the active workflow:

```text
unused/input_samples/                  old/sample inputs, shared JCL, scratch files
unused/generated_artifacts/            old outputs, reports, experiments, pycache
unused/legacy_artifacts/combined/      old manual combined-output snapshot
unused/reference_docs/                 old notes, images, docx/txt references
unused/anonymization/                  PII/anonymizer work
unused/external_repos/                 local external clones not used by this repo
```

### Main Pipeline Scripts

```text
scripts/pipeline/
```

Important scripts:

```text
scripts/pipeline/run_fixed_input.py
scripts/pipeline/build_rag_index.py
scripts/pipeline/build_global_rag_maps.py
scripts/pipeline/import_cobol_rekt_rag_bundle.py
```

### Project Handoff And Roadmap

```text
PROJECT_HANDOFF_ROADMAP.md
PROJECT_STAGE_TRACKER.md
```

Use these to continue the project in a new chat.

### Generated Output

```text
artifacts/final/final_scripts/output/
```

This contains generated final_scripts artifacts, validation reports, and RAG JSONL.

Main Hamza-only JSONL:

```text
artifacts/final/final_scripts/output/rag_index/rag_documents.jsonl
```

Main combined JSONL:

```text
artifacts/final/final_scripts/output/combined/rag_index/<PROGRAM>_combined.jsonl
```

Do not manually edit generated output. Fix the input or script, then rerun the pipeline.

Generated working packages are here:

```text
artifacts/final/final_scripts/work/
```

### Combined Output

The active combined output is:

```text
artifacts/final/final_scripts/output/combined/
```

The older legacy/manual combined snapshot was moved here:

```text
unused/legacy_artifacts/combined/
```

Keep it only as reference until we explicitly decide to delete it.

## Folder Map

```text
input/                           COBOL/MAPA/control-flow inputs
artifacts/                       generated and working analysis artifacts
artifacts/final/final_scripts/   active final_scripts pipeline
docs/                            active reports and notes
scripts/pipeline/                main analysis and RAG document builders
scripts/utils/                   general utility scripts
tests/                           tests or sample checks
unused/                          non-active files kept for reference/recovery
```

## Generated Folders To Ignore

These are generated or local scratch folders:

```text
artifacts/final/final_scripts/work/
artifacts/final/final_scripts/output*/
artifacts/intermediate/
artifacts/experiments/
artifacts/share/
unused/generated_artifacts/
unused/input_samples/_scratch/
unused/anonymization/artifacts/
unused/anonymization/cobol-code-anonymizer/
unused/external_repos/
```

They are now ignored by `.gitignore` unless files were already tracked.

## Safe Cleanup Rule

Do not delete files just because they look random. This repo has generated outputs, local experiments, and input packages mixed together.

Safe cleanup order:

```text
1. Confirm what is tracked vs untracked with git status.
2. Keep program input folders under input/<PROGRAM>/.
3. Keep scripts and docs.
4. Treat output/intermediate/temp folders as regenerable.
5. Only delete generated folders after the user confirms.
```

## Current Machine Role

This PC is the development machine.

Use it for:

```text
code edits
pipeline generation
deterministic checks
compile checks
metadata/index work
```

The friend PC is used for:

```text
Ollama
embeddings
Chroma sync/runtime checks
RAG UI model answers
combined mode with real knowledge-base_rag bundle
```
