# Program Input Template

Copy this folder and rename it to the COBOL program name, for example:

```text
PDCBVC
PDB305
PDHASI06
```

Required files:

```text
<PROGRAM>.CBL
<PROGRAM>_result.txt or <PROGRAM>_result.csv
<PROGRAM>_controlflow.json
copybooks/
```

Optional folders:

```text
jcl/
knowledge-base_rag/
```

`knowledge-base_rag/` is only needed for combined Hamza + cobol-rekt mode. It should contain:

```text
manifest.json
chunks/
```

Run from the repo root:

```bash
python scripts/pipeline/run_fixed_input.py --program <PROGRAM> --mode my
python scripts/pipeline/run_fixed_input.py --program <PROGRAM> --mode both
```

