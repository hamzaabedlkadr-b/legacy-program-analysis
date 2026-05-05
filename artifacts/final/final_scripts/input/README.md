# Fixed Final Scripts Input

Put each COBOL program in its own folder here:

```text
artifacts/final/final_scripts/input/
  PDHASI06/
    PDHASI06.CBL
    PDHASI06_result.csv
    PDHASI06_controlflow.json
    copybooks/
      COPY1.cpy
      COPY2.cpy
    jcl/                  optional
    knowledge-base_rag/   optional, for combined mode
```

Required for Hamza analysis:

- one `.CBL`, `.COB`, or `.COBOL` file
- one MAPA `.csv` or `.txt` result file
- one controlflow `.json` file
- `copybooks/` folder

Optional:

- `jcl/` folder
- `knowledge-base_rag/` folder from cobol-rekt, for combined mode

Run one program:

```bash
python scripts/pipeline/run_fixed_input.py --program PDHASI06 --mode my
```

Run every program folder:

```bash
python scripts/pipeline/run_fixed_input.py --mode my
```

Run Hamza analysis and combined analysis when `knowledge-base_rag/` exists:

```bash
python scripts/pipeline/run_fixed_input.py --program PDHASI06 --mode both
```

Main output:

```text
artifacts/final/final_scripts/output/rag_index/rag_documents.jsonl
```

This is the file copied into the RAG repo as:

```text
data/inbox/control_flow_rag_documents.jsonl
```
