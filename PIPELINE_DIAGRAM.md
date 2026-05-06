# Combined COBOL RAG Pipeline Diagram

```mermaid
flowchart LR
  input["Input files<br/>COBOL, copybooks, MAPA result, control-flow JSON"]

  subgraph first["First approach: Hamza / MAPA analysis"]
    my1["Fixed input package<br/>artifacts/final/final_scripts/input/PDCBVC"]
    my2["MAPA + final_scripts pipeline"]
    my3["Generated analysis artifacts<br/>program_artifacts/.../PDCBVC/artifacts"]
    my4["Hamza RAG documents<br/>output/rag_index/rag_documents.jsonl"]
  end

  subgraph second["Second approach: Ermin / cobol-rekt"]
    er1["cobol-rekt repo<br/>github.com/erminlilaj/cobol-rekt"]
    er2["cobol-rekt analysis"]
    er3["Ermin RAG bundle<br/>input/PDCBVC/knowledge-base_rag"]
  end

  subgraph combined["Combined RAG path"]
    c1["Integration importer<br/>preserve source labels"]
    c2["Combined final_scripts artifacts<br/>output/combined/final_scripts/PDCBVC"]
    c3["Combined RAG JSONL<br/>output/combined/rag_index/PDCBVC_combined.jsonl"]
    c4["RAG sync/index<br/>cobol-combined-pdcbvc"]
    c5["RAG UI<br/>answers from combined evidence"]
  end

  input --> my1 --> my2 --> my3 --> my4
  input --> er1 --> er2 --> er3

  my3 --> c1
  my4 --> c1
  er3 --> c1

  c1 --> c2
  c1 --> c3
  c3 --> c4 --> c5
  c2 --> c5
```

## Independent Test Modes

```mermaid
flowchart LR
  my["Hamza-only mode<br/>--mode my"]
  my_jsonl["rag_documents.jsonl"]
  my_index["cobol-fixed-pdcbvc<br/>data/chroma-fixed-pdcbvc"]
  my_ui["RAG UI<br/>my results only"]

  combined["Combined mode<br/>--mode combined"]
  combined_jsonl["PDCBVC_combined.jsonl"]
  combined_index["cobol-combined-pdcbvc<br/>data/chroma-combined-pdcbvc"]
  combined_ui["RAG UI<br/>Hamza + Ermin evidence"]

  my --> my_jsonl --> my_index --> my_ui
  combined --> combined_jsonl --> combined_index --> combined_ui
```

## Meaning

- First approach, Hamza/MAPA, creates the stable `final_scripts` artifacts and `rag_documents.jsonl`.
- Second approach, Ermin/cobol-rekt, creates the exported `knowledge-base_rag` bundle.
- Combined mode does not overwrite either source. It imports both, labels their provenance, creates integration artifacts, then indexes `PDCBVC_combined.jsonl`.
- Hamza-only and combined tests use separate inbox files, Chroma directories, and collections.
