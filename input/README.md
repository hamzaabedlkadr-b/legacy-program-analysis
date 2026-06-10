# Root Input Folder

This is the main place where you put COBOL program inputs:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\input
```

Use one folder per program. The folder name should match the program name.

```text
input/
  PDCBVC/
    PDCBVC.CBL
    PDCBVC_result.txt
    PDCBVC_controlflow.json
    copybooks/
      PD1VOCI.cpy
      PDRTWA2.cpy
    jcl/
      optional
    knowledge-base_rag/
      optional for combined mode
```

## Quick Checklist

Required for Hamza-only analysis:

```text
<PROGRAM>.CBL or <PROGRAM>.COB or <PROGRAM>.COBOL
<PROGRAM>_result.txt or <PROGRAM>_result.csv
<PROGRAM>_controlflow.json
copybooks/
```

Optional:

```text
jcl/
knowledge-base_rag/
```

`knowledge-base_rag/` is only for combined mode with Ermin/cobol-rekt evidence. It should contain:

```text
manifest.json
chunks/
```

## Template

Copy this folder when adding a new program:

```text
_PROGRAM_TEMPLATE/
```

Then rename the copy to your program name and add the real files.

## Do Not Edit Generated Folders

Generated working folders are created outside `input/`:

```text
artifacts/final/final_scripts/work/program_packages/
artifacts/final/final_scripts/work/normalized_controlflow/
```

If they are wrong, fix the source program folder and rerun the pipeline.

## Non-Active Inputs

Loose shared JCL files not used by the current PDCBVC run were moved here:

```text
unused/input_samples/_shared/jcl/
```

Scratch COBOL/copybook files that are not packaged as active inputs were moved here:

```text
unused/input_samples/_scratch/
```

## Run Commands

From the repo root:

```bash
cd C:/Users/Lenovo/Desktop/Camera/control_flow
```

Run one program, Hamza-only:

```bash
python scripts/pipeline/run_fixed_input.py --program PDCBVC --mode my
```

Run one program, combined Hamza + cobol-rekt:

```bash
python scripts/pipeline/run_fixed_input.py --program PDCBVC --mode combined
```

Run one program and generate both Hamza-only and combined outputs:

```bash
python scripts/pipeline/run_fixed_input.py --program PDCBVC --mode both
```

Run every program folder:

```bash
python scripts/pipeline/run_fixed_input.py --mode my
```

## Main Outputs

Hamza-only RAG JSONL:

```text
artifacts/final/final_scripts/output/rag_index/rag_documents.jsonl
```

Combined RAG JSONL:

```text
artifacts/final/final_scripts/output/combined/rag_index/<PROGRAM>_combined.jsonl
```

Final scripts artifacts:

```text
artifacts/final/final_scripts/output/program_artifacts/programs/<PROGRAM>/artifacts/
```

