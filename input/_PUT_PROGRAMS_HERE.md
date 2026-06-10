# Put Program Inputs Here

This is the working input folder for the fixed final_scripts pipeline:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\input
```

Create one folder per COBOL program:

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
      optional cobol-rekt bundle for combined mode
```

Use `_PROGRAM_TEMPLATE/` as the shape to copy when adding a new program.

Generated working folders are outside `input/`:

```text
artifacts/final/final_scripts/work/program_packages/
artifacts/final/final_scripts/work/normalized_controlflow/
```

They are created by the pipeline.

