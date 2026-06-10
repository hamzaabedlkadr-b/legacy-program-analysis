# COBOL-REKT Integration Report

Program: `PDCBVC`
Source bundle: `cobol-rekt/knowledge-base_rag/PDCBVC`
Imported at UTC: `2026-05-05T10:26:55.812978+00:00`

## What Was Imported

- Total cobol-rekt chunks: 647
- call_contract: 5
- cics.operation: 13
- cics.program_transfer: 4
- cics.resource: 7
- cics_operations: 1
- cobol_analysis_health: 1
- commented_out_code: 1
- comments: 1
- controlflow.cfg: 137
- copybook_fields: 34
- copybook_mentions: 2
- dataflow.variable: 275
- datasets_tables_resources: 1
- dead_code: 1
- dependencies: 1
- error_path: 60
- external_program_calls: 1
- paragraph_logic: 54
- program_summary: 1
- screen.key_dispatch: 2
- screen.pagination: 3
- screen.row_build: 4
- screen.selection: 5
- static_values: 11
- unused_copybooks: 2
- variable_group: 16
- workflow: 4

## Added Combined Artifacts

- `integration.cobol_rekt_bundle`: provenance, chunk inventory, and selected external evidence refs.
- `architecture.call_contracts`: normalized external call contracts, including USING parameters and preparation evidence.
- `controlflow.cfg.rich`: external control-flow chunk inventory.
- `dataflow.variable.rich`: external variable/dataflow chunk inventory.
- `screen.interaction`: external key dispatch, pagination, row build, and selection chunks.
- `quality.error_paths.rich`: external error path chunks.
- `architecture.copybook_fields`: external copybook field chunks.
- `integration.conflicts`: explicit differences between current final_scripts and cobol-rekt evidence.

## Conflict Policy

No current final_scripts facts were overwritten. When a difference exists, the combined output preserves both facts with source labels.
Detected conflicts: 3
- commented_out_code: prefer_final_scripts_for_commented_out_code; keep cobol-rekt as external evidence
- unused_copybooks: treat both as heuristics; report union with source labels until a compiler-level usage proof exists
- line_count_methodology: do not collapse different counting methods into one number

## Combined RAG JSONL

- Base documents copied: 824
- New cobol-rekt/combined documents added: 652
- Total combined documents: 1476

## How To Test

Point `COBOL_RAG_FINAL_SCRIPTS_DIR` to `artifacts/combined/final_scripts` and sync the generated combined JSONL instead of replacing the stable JSONL.
