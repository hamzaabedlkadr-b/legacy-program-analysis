# Combined MAPA/Hamza and cobol-rekt Merge Report

Date: 2026-05-06
Program: PDCBVC
Generated combined JSONL: `artifacts/final/final_scripts/output/combined/rag_index/PDCBVC_combined.jsonl`

## Purpose

The combined pipeline is designed to make answers feel natural without turning the system into a set of ready-made answers. It does this by merging evidence, not by writing final responses in advance.

The main idea is simple:

- MAPA/Hamza remains the source for precise static facts: calls, copybooks, variables, line evidence, control-flow edges, and generated final_scripts artifacts.
- cobol-rekt adds richer program-understanding context: call contracts, paragraph intent, workflows, dataflow expansion, error paths, CICS/screen behavior, and quality observations.
- The integration layer creates neutral context records that connect both sides for the same call, paragraph, or variable. These records are not final answers. They are structured evidence briefs that help retrieval produce a grounded and more human answer.

The RAG/UI code was not changed.

## Input Sources

### MAPA/Hamza final_scripts

MAPA/Hamza output comes from the normal fixed-input pipeline:

`artifacts/final/final_scripts/output/program_artifacts/programs/PDCBVC/artifacts/`

It provides the stable baseline artifacts used by the current RAG flow. Important examples:

- `architecture.calls.json`
- `architecture.call_parameters.json`
- `controlflow.cfg.json`
- `dataflow.variable/*.json`
- `dataflow.used_variables.json`
- `business_rule/*.json`
- `program.comments.json`
- `quality.dead_code.json`
- `architecture.unused_copybooks.json`

### cobol-rekt knowledge-base_rag

cobol-rekt input is read from:

`artifacts/final/final_scripts/input/knowledge-base_rag/`

This bundle is treated as external evidence. The importer does not rewrite the friend report and does not replace final_scripts facts.

Important imported chunk families include:

- `call_contract`
- `paragraph_logic`
- `workflow`
- `controlflow.cfg`
- `dataflow.variable`
- `error_path`
- `copybook_fields`
- `screen.key_dispatch`
- `screen.pagination`
- `screen.row_build`
- `screen.selection`
- `unused_copybooks`
- `program_summary`

## Merge Basis

The merge is based on explicit entity matching and source-role policy.

### 1. Call matching

Calls are matched with a normalized key:

`PROGRAM|TARGET|CALL_TYPE`

Example:

`PDCBVC|PD1VOCI|LINK`

MAPA/Hamza contributes:

- exact target
- call type
- paragraph
- source line
- statement text
- parameters, COMMAREA, and length
- parameter variables when available

cobol-rekt contributes:

- call contract chunk
- nearby preparation evidence
- call-related context around how data is prepared or checked

The current PDCBVC combined output has 5 real linked outbound call contexts:

- `PDCBVC|PD0UTI01|LINK`
- `PDCBVC|PD1FS00|LINK`
- `PDCBVC|PD1VOCI|LINK`
- `PDCBVC|PDPRED|XCTL`
- `PDCBVC|PXRSEMAF|CALL`

### 2. Paragraph matching

Paragraphs are matched by paragraph name.

MAPA/Hamza contributes:

- whether the paragraph is present in the generated control-flow graph
- incoming and outgoing edges
- edge type
- conditions
- evidence strings from the control-flow artifact

cobol-rekt contributes:

- paragraph intent from comments and paragraph logic
- variables read and modified
- local complexity and reachability metadata
- workflow relationships
- CICS/screen/error-path context when present

Example for `PREP-RIGA`:

- MAPA/Hamza says it has 1 incoming edge and 2 outgoing edges.
- MAPA/Hamza records a `CALL_RANGE` to `LINK-PD0UTI01` and a conditional jump to `PREP-RIGA-010`.
- cobol-rekt describes it as preparation of a row in the map, lists read/modified variables, and says it orchestrates `LINK-PD0UTI01`.

### 3. Variable matching

Variables are matched by variable name.

MAPA/Hamza contributes:

- defined-in paragraphs
- modified-in paragraphs
- used-in paragraphs
- exact write/read/control evidence
- whether the variable controls flow
- fanout nodes

cobol-rekt contributes:

- expanded read/write site context
- origin group or data group
- read/write counts from its Java CFG analysis
- split dataflow chunks when the evidence is large

Example for `PD1VOCI-RETURN`:

- MAPA/Hamza says it is defined, modified, and used in `LINK-PD1VOCI`.
- MAPA/Hamza gives exact line evidence: line 484 writes `HIGH-VALUE`; line 489 checks whether it equals `E`.
- cobol-rekt adds that it belongs to origin group `WPD1VOCI`, has 5 reads and 5 writes, and provides broader CFG context.

### 4. Conflict recording

The merge does not overwrite facts when the two systems disagree. It records conflicts in:

`artifacts/final/final_scripts/output/combined/final_scripts/PDCBVC/integration.conflicts/integration.conflicts.json`

Current conflict topics:

- `commented_out_code`: MAPA/Hamza reports 15 commented-out items; cobol-rekt reports none detected.
- `unused_copybooks`: MAPA/Hamza marks `DFHBMSCA`, `PDCBVCM`, `PDRTIP01`, and `PDRVC` as needing review; cobol-rekt marks `PDRTIP01` and `PDRVC` as candidates.
- `line_count_methodology`: counts from the two systems may represent different things, so answers should preserve labels instead of collapsing them into one number.

## What Is Taken From Each Side

### Prefer MAPA/Hamza for exact static facts

Use MAPA/Hamza as primary evidence for:

- exact call inventory
- exact call line and statement
- call parameters and COMMAREA
- copybook inventory and generated copybook status
- generated control-flow graph edges
- variable read/write/control sites
- business rules extracted from final_scripts
- stable final_scripts quality artifacts

Reason: these artifacts are already structured for deterministic RAG answers and include exact citations and generated line-level facts.

### Prefer cobol-rekt for richer context

Use cobol-rekt as primary evidence for:

- paragraph intent
- call-contract preparation evidence
- workflow summaries
- expanded variable/dataflow context
- error-path descriptions
- CICS and screen behavior chunks
- copybook fields and ownership-style observations
- analysis health and quality-confidence context

Reason: cobol-rekt gives deeper contextual explanations around how the program behaves, especially where a single MAPA artifact is too terse.

### Use integration records for natural answers

The new integration records are the bridge:

- `integration.call_context`
- `integration.paragraph_context`
- `integration.variable_context`
- `integration.entity_link`
- `integration.source_balance`

These records are deliberately not final answers. They are evidence summaries that say what each system knows about the same entity. This should help the RAG layer produce answers that sound natural because it can retrieve one combined context and then compose an answer from facts.

## Volume

Current combined manifest:

- Base MAPA/Hamza records: 364
- Added records: 803
- Total combined records: 1167

The 803 added records include raw cobol-rekt records, integration artifacts, and neutral synthesis records.

### cobol-rekt imported chunk counts

- `dataflow.variable`: 264
- `paragraph_logic`: 54
- `error_path`: 53
- `controlflow.cfg`: 36
- `copybook_fields`: 34
- `workflow`: 20
- `variable_group`: 16
- `cics.operation`: 13
- `static_values`: 11
- `cics.resource`: 7
- `call_contract`: 5
- `screen.key_dispatch`: 4
- `screen.pagination`: 4
- `screen.selection`: 4
- `screen.row_build`: 3
- `unused_copybooks`: 2
- several one-record summary or quality families

### Integration context counts

- `integration.call_context`: 5
- `integration.paragraph_context`: 67
- `integration.variable_context`: 171
- `integration.entity_link`: 5
- `integration.source_balance`: 2 records in JSONL, because one is the direct guide record and one is the indexed artifact record

## Why This Should Feel More Natural

Before this change, combined mode mostly added cobol-rekt records beside MAPA/Hamza records. Retrieval could find both, but it had to infer how to combine them. That can lead to answers that feel like copied chunks, stitched bullet points, or generic summaries.

Now the combined output contains records that explain the relationship:

- for this call, here is the exact MAPA/Hamza call fact and here is the cobol-rekt preparation context
- for this paragraph, here are the graph edges and here is the paragraph/workflow intent
- for this variable, here are exact read/write/control sites and here is broader dataflow context

This gives the answer generator a more natural evidence shape: facts plus context, not isolated documents.

## Current Limitations

1. The merge is deterministic and rule-based.

It links entities by names and normalized call types. It does not yet do semantic matching for renamed aliases, partial names, or indirect relationships that require deeper program reasoning.

2. Variable context volume is high.

There are 171 variable context records. This is useful for coverage, but some variables may be low-value for user questions. Ranking or filtering could improve retrieval precision.

3. cobol-rekt chunks may be verbose.

Some cobol-rekt preparation evidence is long. The importer truncates large text for embedding safety, but future work should make better concise summaries from repeated or expanded evidence.

4. Conflict policy is recorded but not resolved.

For disagreements such as commented-out code and unused copybooks, the pipeline preserves both views. It does not decide which one is absolutely correct unless a clear source policy exists.

5. Screen and CICS behavior are imported but lightly synthesized.

Screen chunks are currently grouped under `screen.interaction`, and paragraph contexts include some related context. A future pass could build dedicated `integration.screen_flow_context` records.

6. No RAG/UI routing changes were made.

The combined JSONL is richer, but the UI/RAG layer still needs to index this specific combined JSONL to benefit from it.

## Future Improvements

### 1. Add query-focused routing metadata

Add metadata such as:

- `question_intents: ["call_parameters", "paragraph_explanation", "variable_lifecycle"]`
- `primary_answer_source`
- `supporting_answer_source`
- `confidence_basis`

This would help retrieval select the right synthesis record for a question without relying only on text similarity.

### 2. Add dedicated screen-flow integration

Build records that combine:

- MAPA/Hamza CICS navigation
- cobol-rekt key dispatch
- pagination
- row building
- selection behavior

This would help answer questions such as "what happens on PF7/PF8", "how rows are built", and "how selection works".

### 3. Improve copybook reconciliation

The current copybook conflict report is fair but conservative. A stronger future version could compare:

- COPY statements
- declared fields
- referenced fields
- field prefixes in dataflow
- copybook ownership from cobol-rekt

Then it could distinguish "not referenced in available artifacts" from "probably unused" more clearly.

### 4. Summarize large cobol-rekt evidence

Some cobol-rekt chunks contain repeated CFG-expanded evidence. A future summarizer could preserve exact citations but reduce repetition before indexing.

### 5. Add confidence tiers

Each merged record could expose confidence:

- high: both systems agree on the same entity
- medium: one system provides exact evidence and the other provides partial context
- low: heuristic-only or conflict-only evidence

This would make answers more transparent without making them verbose.

### 6. Add evaluation questions

Create a small benchmark of questions:

- What calls does PDCBVC make?
- What does `PREP-RIGA` do?
- What prepares the `PD1VOCI` call?
- Where is `PD1VOCI-RETURN` set and checked?
- Which copybooks need review and why?
- What are the known conflict areas between the analyzers?

Then compare base MAPA/Hamza RAG vs combined JSONL to confirm that combined mode improves answers without hallucinating.

## Recommended Use

For stable demos and evaluation, keep the normal MAPA/Hamza JSONL as the baseline:

`artifacts/final/final_scripts/output/rag_index/rag_documents.jsonl`

Use the combined JSONL only when testing combined mode:

`artifacts/final/final_scripts/output/combined/rag_index/PDCBVC_combined.jsonl`

Do not replace the stable baseline until combined answers are evaluated and shown to be better.
