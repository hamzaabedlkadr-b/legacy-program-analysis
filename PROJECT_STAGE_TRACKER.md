# COBOL RAG Project Stage Tracker

Created: 2026-06-08
Last updated: 2026-07-08

This file tracks the execution plan for finishing the COBOL RAG project. Use it together with:

```text
PROJECT_HANDOFF_ROADMAP.md
```

Rule:

```text
Do one stage at a time.
After each stage, run its checkpoint.
Only move to the next stage when the checkpoint is acceptable.
Update this file when a stage is completed.
```

Machine rule:

```text
This local PC is the development machine.
Do not require Ollama/model-dependent checks to pass here.
Run local deterministic checks here.
Run full Chroma embedding sync, RAG LLM answers, and browser/UI model testing on the friend PC.
```

Current repo layout note:

```text
Use root input\ for COBOL/MAPA/control-flow inputs.
Use artifacts\final\final_scripts\output\ for generated active output.
Use artifacts\final\final_scripts\work\ for generated working packages.
Use unused\ for non-active samples, old generated outputs, anonymization, and external clones.
```

## Stage Summary

Total stages:

```text
10 stages, numbered 0 through 9.
```

Current stage:

```text
Stage 6: Metadata-Filtered Hybrid Retrieval
```

Latest local snapshot, checked on 2026-07-08:

```text
Analysis repo:
- Branch: feature/combine-cobol-rekt-analysis
- Latest local commit: 2c39e13 Add PDB305 input and harden MAPA parsing
- Worktree has untracked docs/current_rag_detailed_report.* files, rag_*.svg diagrams, and cobol-code-anonymizer/.
- Active input folders: input\PDCBVC and input\PD305
- Generated programs: PDCBVC and PDB305

RAG/UI repo:
- Branch: feature/combine-cobol-rekt-rag
- Latest local commit: 40f8c7f Preserve combined RAG evidence metadata
- Worktree has modified data/inbox/control_flow_rag_documents.jsonl and untracked data/chroma-fixed-pdcbvc/, eval/scope_router_smoke.py, src/cobol_rag/scope_router.py.

Latest Hamza-only RAG JSONL:
- records: 621
- by_program: PDB305=206, PDCBVC=271, __GLOBAL__=144
- required routing metadata present on 621/621 records
- entity_key present on 394/621 records

Latest combined two-program JSONL:
- file: artifacts\final\final_scripts\output\combined\rag_index\PDB305_PDCBVC_combined.jsonl
- records: 2016
- by_program: PDB305=772, PDCBVC=1100, __GLOBAL__=144
- required routing metadata present on 2016/2016 records
- entity_key present on 943/2016 records

Current global sidecar indexes:
- program_count: 2
- programs: PDB305, PDCBVC
- entity_name_count: 358
- ambiguous_entities: 74
- call_edges: 11
- copybook_usage: 18
- db2_table_usage: 2
- sql_include_usage: 6

PDCBVC knowledge-base_rag manifest is not present on this PC at latest check.
Do not reset or clean either repo without explicit user approval.
```

## Stage 0: Baseline Audit And Readiness Check

Status:

```text
COMPLETED
```

Completed:

```text
2026-06-08
```

Goal:

```text
Confirm the current local state before changing code.
```

Work:

```text
Check analysis repo branch, remote, latest commits, and dirty files.
Check RAG/UI repo branch, remote, latest commits, and dirty files.
Confirm key pipeline files exist.
Confirm expected Hamza-only and combined output paths.
Confirm current run commands are still valid.
```

Checkpoint:

```text
git status --short --branch
git log --oneline -5
Test-Path scripts/pipeline/run_fixed_input.py
Test-Path scripts/pipeline/import_cobol_rekt_rag_bundle.py
Test-Path ..\cobol-rag-pipeline\.worktrees\ui\scripts\run_fixed_input_rag.sh
Test-Path ..\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\retrieve.py
```

Pass condition:

```text
Both repos are on the expected feature branches.
Critical files exist.
No unexpected repo switch is needed.
Dirty files are documented, not reset.
```

Result:

```text
PASS WITH DOCUMENTED DIRTY WORKTREE

Analysis repo:
- Branch: feature/combine-cobol-rekt-analysis
- Latest checked commit: 2c39e13 Add PDB305 input and harden MAPA parsing
- Critical files exist:
  - scripts/pipeline/run_fixed_input.py
  - scripts/pipeline/import_cobol_rekt_rag_bundle.py
- Worktree has untracked current report/diagram docs and an untracked cobol-code-anonymizer folder.
- Do not reset or clean without explicit user approval.

RAG/UI repo:
- Branch: feature/combine-cobol-rekt-rag
- Latest checked commit: 40f8c7f Preserve combined RAG evidence metadata
- Critical files exist:
  - scripts/run_fixed_input_rag.sh
  - src/cobol_rag/retrieve.py
- Worktree has local generated/index changes and untracked scope-router files.
- Do not reset or clean without explicit user approval.
```

## Stage 1: Stabilize PDCBVC Baseline

Status:

```text
LOCAL_CHECKS_COMPLETE_FRIEND_PC_PENDING
```

Goal:

```text
Make sure Hamza-only and combined PDCBVC still run before adding enterprise retrieval changes.
```

Work:

```text
Run Hamza-only build/index.
Run combined build/index if knowledge-base_rag exists.
Keep COBOL_RAG_LLM_POLISH_FINAL_SCRIPTS=false.
Run deterministic evaluation/smoke checks.
Record current pass/fail status.
```

Local development checkpoint:

```text
python scripts/pipeline/run_fixed_input.py --program PDCBVC --mode my
python eval/run_gold_eval.py
python -m compileall -q src/cobol_rag eval
```

Friend PC runtime checkpoint:

```text
./scripts/run_fixed_input_rag.sh --mode my --program PDCBVC --analysis-repo /c/Users/Lenovo/Desktop/Camera/control_flow --build-analysis --no-server
./scripts/run_fixed_input_rag.sh --mode combined --program PDCBVC --analysis-repo /c/Users/Lenovo/Desktop/Camera/control_flow --build-analysis --no-server
python eval/run_gold_eval.py
Open http://127.0.0.1:8000/ and test the good questions.
```

Pass condition:

```text
PDCBVC can be indexed.
Gold/smoke checks pass or known gaps are documented.
No generic LLM hallucination appears in deterministic answers.
```

Current local result:

```text
LOCAL PASS, FRIEND-PC RUNTIME PENDING

Latest 2026-07-08 refresh:
- Hamza-only analysis output now includes PDB305 and PDCBVC.
- Latest RAG manifest: 621 records total.
- by_program: PDB305=206, PDCBVC=271, __GLOBAL__=144.
- PDCBVC knowledge-base_rag bundle is still not present on this PC.
- Full Chroma/Ollama/UI runtime validation remains friend-PC work.

Hamza-only analysis build:
- PASS
- Earlier PDCBVC-only run generated 364 RAG documents/chunks.
- Latest two-program run generated 621 RAG records.
- RAG index valid.
- Factory readiness: READY_WITH_WARNINGS.
- Warning: missing copybooks PDIABEND, PDSAVTW2, PXCSEMAF.

Combined analysis build:
- NOT RUN LOCALLY.
- PDCBVC knowledge-base_rag bundle is not present on this PC.

RAG Chroma sync:
- NOT REQUIRED LOCALLY.
- Attempted once and failed because Ollama is not running.
- This is expected on the development PC.

Deterministic gold eval:
- Ran without Ollama.
- Initial result: 41 pass, 2 fail, 6 skip, 1 xfail.
- Fixed the 2 active entity-validation failures in the RAG/UI repo.
- Current result: 43 pass, 0 fail, 6 skip, 1 xfail.
- Skips are expected locally: 1 requires Ollama, 5 require combined_rag_index.
- XFAIL is expected: datasets.batch_program_outputs needs missing batch/JCL evidence.

Compile check:
- PASS: python -m compileall -q src/cobol_rag eval

RAG/UI code change:
- C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\final_scripts_answers.py
- Direct variable guard now keeps the "will not infer" limitation.
- Direct variable guard no longer misclassifies known call targets/copybooks/DB2 tables/SQL includes as unknown variables.
```

## Stage 2: Enterprise Metadata Schema

Status:

```text
LOCAL_CHECKS_COMPLETE_FRIEND_PC_COMBINED_PENDING
```

Goal:

```text
Define the metadata needed for 1000-file routing and retrieval.
```

Work:

```text
Add or normalize metadata fields in generated RAG JSONL.
Add program, intent_domain, entity_type, entity_key, parent_id, hierarchy_level, and evidence path fields.
Make Hamza-only and combined records follow the same metadata contract.
Keep source_system/provenance labels.
```

Likely files:

```text
scripts/pipeline/build_rag_index.py
scripts/pipeline/build_global_rag_maps.py
scripts/pipeline/import_cobol_rekt_rag_bundle.py
```

Checkpoint:

```text
Run the analysis pipeline for PDCBVC.
Inspect rag_documents.jsonl and PDCBVC_combined.jsonl.
Verify required metadata fields exist on representative records.
```

Pass condition:

```text
RAG records can be filtered by program, intent_domain, entity_key, and hierarchy_level.
No existing important source fields are lost.
```

Current local result:

```text
PASS, LOCAL HAMZA-ONLY

Analysis repo changes:
- scripts/pipeline/build_rag_index.py now adds:
  - intent_domain
  - hierarchy_level
  - parent_id
  - parent_type
  - evidence_path
  - entity_type/entity_key for variables, calls, paragraphs, copybooks, DB2 tables, and SQL includes.
- scripts/pipeline/import_cobol_rekt_rag_bundle.py now normalizes the same metadata contract for added cobol-rekt/integration records before writing combined JSONL.

RAG/UI repo changes:
- src/cobol_rag/loaders/rag_documents.py now preserves the new fields during JSONL loading.

Validation:
- Rebuilt Hamza-only RAG index for current active inputs: 621 records.
- Program coverage: PDB305=206, PDCBVC=271, __GLOBAL__=144.
- Pipeline validator: 1 WARN, 0 FAIL.
- The warning is unchanged: missing copybooks PDIABEND, PDSAVTW2, PXCSEMAF.
- Metadata audit:
  - program: 621/621
  - intent_domain: 621/621
  - hierarchy_level: 621/621
  - parent_id: 621/621
  - parent_type: 621/621
  - evidence_path: 621/621
  - chunk_type: 621/621
  - entity_key: 394/621
- Combined two-program metadata audit:
  - file: artifacts/final/final_scripts/output/combined/rag_index/PDB305_PDCBVC_combined.jsonl
  - records: 2016
  - program/source_system/intent_domain/hierarchy_level/parent/evidence_path/chunk_type: 2016/2016
  - entity_key: 943/2016
- Earlier RAG/UI loader audit against PDCBVC Hamza-only JSONL:
  - loaded split documents: 1341
  - intent_domain/hierarchy/parent/evidence_path preserved: 1341/1341
  - entity_key preserved on 570 split documents.
- Deterministic gold eval: 43 pass, 0 fail, 6 skip, 1 xfail.
- Compile checks passed for changed analysis and RAG/UI Python files.

Pending on friend PC:
- Run combined mode with PDCBVC knowledge-base_rag.
- Verify added cobol-rekt/integration records receive the same metadata contract.
- Run Chroma/Ollama sync and UI model tests.
```

## Stage 3: Program, Entity, And Relationship Indexes

Status:

```text
LOCAL_CHECKS_COMPLETE
```

Goal:

```text
Build deterministic indexes for program/entity resolution before vector search.
```

Work:

```text
Generate program_index.json.
Generate entity_index.json.
Generate relationship_index.json.
Track variables, paragraphs, copybooks, call targets, DB2 tables, datasets, UI keys, and transaction IDs.
Track ambiguous entities that appear in multiple programs.
```

Likely files:

```text
scripts/pipeline/build_global_rag_maps.py
scripts/pipeline/run_fixed_input.py
```

Checkpoint:

```text
Inspect generated indexes.
Confirm PDCBVC entities resolve correctly.
Confirm ambiguous names are represented as ambiguous.
```

Pass condition:

```text
The system can answer "which program owns this entity?" without using the LLM.
```

Current local result:

```text
PASS, LOCAL

Analysis repo changes:
- scripts/pipeline/build_global_rag_maps.py now writes:
  - program_index.json
  - entity_index.json
  - relationship_index.json
- These are routing sidecar files, not vector chunks.
- scripts/pipeline/build_rag_index.py excludes those sidecar index files from vector indexing.

Generated sidecar indexes:
- artifacts/final/final_scripts/output/program_artifacts/_global/rag_maps/program_index.json
- artifacts/final/final_scripts/output/program_artifacts/_global/rag_maps/entity_index.json
- artifacts/final/final_scripts/output/program_artifacts/_global/rag_maps/relationship_index.json

Latest two-program global index audit:
- programs: 2
- program names: PDB305, PDCBVC
- entity names: 358
- ambiguous entities: 74
- call edges: 11
- copybook usage records: 18
- DB2 table usage records: 2
- SQL include usage records: 6

Earlier PDCBVC-only index audit:
- programs: 1
- variables: 170
- paragraphs: 64
- copybooks: 12
- call targets: 5
- DB2 tables: 1
- SQL includes: 3
- JCL jobs: 0
- entity names: 249
- ambiguous names: 6
- call edges: 5

Important examples:
- PD1VOCI-RETURN resolves to PDCBVC variable entity key PDCBVC|VARIABLE|PD1VOCI-RETURN.
- PD1VOCI resolves as both a PDCBVC call target and COPY member.
- Call types are normalized to LINK/XCTL/CALL.

Validation:
- build_global_rag_maps.py compile check passed.
- build_rag_index.py compile check passed.
- Earlier PDCBVC-only RAG index remained 364 vector records after sidecar indexes were excluded.
- Latest two-program RAG index has 621 vector records after sidecar indexes are excluded from vector indexing.
- Pipeline validator: 1 WARN, 0 FAIL.
- Warning unchanged: missing copybooks PDIABEND, PDSAVTW2, PXCSEMAF.
```

## Stage 4: RAG Loader And Sync Metadata Preservation

Status:

```text
LOCAL_LOADER_CHECKS_COMPLETE_FRIEND_PC_SYNC_PENDING
```

Goal:

```text
Make sure the RAG/UI repo preserves all new metadata into Chroma and manifests.
```

Work:

```text
Update RAG JSONL loader if needed.
Update sync manifest handling if needed.
Confirm Chroma receives program, intent_domain, entity_key, parent_id, and hierarchy_level.
```

Likely files:

```text
src/cobol_rag/loaders/rag_documents.py
src/cobol_rag/sync.py
```

Checkpoint:

```text
cobol-rag inspect data/inbox/control_flow_rag_documents.jsonl --preview-chars 80
cobol-rag sync data/inbox/control_flow_rag_documents.jsonl --apply
Inspect collection metadata for sample records.
```

Pass condition:

```text
Metadata needed for branch filtering is available at retrieval time.
```

Current local result:

```text
PASS, LOCAL LOADER CHECK

RAG/UI repo changes:
- src/cobol_rag/loaders/rag_documents.py now preserves:
  - intent_domain
  - hierarchy_level
  - parent_id
  - parent_type
  - evidence_path
  - copybook
  - db2_table
  - sql_include

Current raw JSONL metadata audit:
- Hamza-only records: 621
- required branch/filter metadata present: 621/621
- entity_key present: 394/621
- combined two-program records: 2016
- combined required branch/filter metadata present: 2016/2016
- combined entity_key present: 943/2016

Earlier loader audit against regenerated PDCBVC Hamza-only JSONL:
- loaded split documents: 1341
- intent_domain: 1341/1341
- hierarchy_level: 1341/1341
- parent_id: 1341/1341
- parent_type: 1341/1341
- evidence_path: 1341/1341
- entity_key: 570 split documents

Validation:
- Deterministic gold eval: 43 pass, 0 fail, 6 skip, 1 xfail.
- RAG/UI compile check passed.

Pending on friend PC:
- Run cobol-rag sync with Ollama embeddings.
- Confirm Chroma stores these metadata fields and supports filters over them.
```

## Stage 5: Program Scope Resolver

Status:

```text
LOCAL_CHECKS_COMPLETE
```

Goal:

```text
Before retrieval, determine which program or global scope the question belongs to.
```

Work:

```text
Use explicit program mentions.
Infer program from unique entity names.
Use current chat program for follow-up questions.
Ask clarification when an entity appears in multiple programs.
Allow global/cross-program questions for dependencies.
```

Likely files:

```text
src/cobol_rag/query.py
src/cobol_rag/question_router.py
```

Checkpoint:

```text
Test explicit program question.
Test unique entity question.
Test ambiguous entity question.
Test follow-up question using previous program context.
```

Pass condition:

```text
The retriever does not search all programs for local variable/call/paragraph questions.
```

Current local result:

```text
PASS, LOCAL RESOLVER

RAG/UI repo changes:
- Added src/cobol_rag/scope_router.py.
- Added eval/scope_router_smoke.py.

Resolver behavior:
- Explicit program question:
  - "What calls does PDCBVC make?" -> PDCBVC, reason explicit_program.
- Unique entity question:
  - "Where is PD1VOCI-RETURN set?" -> PDCBVC, reason unique_entity.
- Call-target/copybook entity:
  - "What does PD1VOCI do?" -> PDCBVC, reason unique_entity.
- Follow-up with current chat program:
  - "And where is it checked?" + current_program=PDCBVC -> PDCBVC, reason chat_context.
- Single indexed program default:
  - "Explain the indexed program" -> PDCBVC, reason single_indexed_program_default.

Validation:
- eval/scope_router_smoke.py passed.
- Deterministic gold eval: 43 pass, 0 fail, 6 skip, 1 xfail.
- RAG/UI compile check passed.

Important boundary:
- Stage 5 adds the resolver but does not yet force retrieval to use metadata filters.
- Stage 6 must wire this resolver into retrieval and apply Chroma/BM25 filters.
```

## Stage 6: Metadata-Filtered Hybrid Retrieval

Status:

```text
PENDING
```

Goal:

```text
Make retrieval search inside the selected tree branch.
```

Work:

```text
Build Chroma where filters from program scope, intent, and entity.
Restrict or strongly rerank BM25 results using the same branch.
Keep intent-aware chunk boosts.
Keep exact identifier boosts.
Fail closed when an exact entity is missing.
```

Likely file:

```text
src/cobol_rag/retrieve.py
```

Checkpoint:

```text
Ask variable, call, UI, copybook, and control-flow questions.
Inspect retrieved source metadata.
Confirm top results come from the selected program/entity/domain.
```

Pass condition:

```text
Wrong-program or wrong-domain chunks cannot outrank the correct local evidence.
```

## Stage 7: Parent/Sibling Context Expansion

Status:

```text
PENDING
```

Goal:

```text
Retrieve exact leaf evidence first, then add useful context around it.
```

Work:

```text
For variable hits, add parent variable summary and nearby read/write facts.
For call hits, add parent call context and call-parameter evidence.
For paragraph hits, add paragraph summary and CFG neighbors.
For combined hits, add integration context for the same entity_key.
```

Likely file:

```text
src/cobol_rag/retrieve.py
```

Checkpoint:

```text
Ask "Where is PD1VOCI-RETURN set?"
Verify answer has exact write/check evidence plus useful parent context.
Ask "What prepares PD1VOCI?"
Verify answer has both call context and parameter preparation context.
```

Pass condition:

```text
Answers are precise and explanatory without retrieving random broad chunks.
```

## Stage 8: Evaluation Suite For Scaling

Status:

```text
PENDING
```

Goal:

```text
Create tests that prove the tree-based RAG is grounded.
```

Work:

```text
Add gold questions for program summaries, calls, variables, UI keys, errors, copybooks, datasets, DB2, dead code, unknown entities, and ambiguous entities.
Add tests for wrong-program contamination.
Add tests for combined source provenance.
```

Likely folder:

```text
eval/
```

Checkpoint:

```text
python eval/run_gold_eval.py
python -m compileall -q src/cobol_rag eval
```

Pass condition:

```text
Gold eval passes.
Known gaps are explicit.
No hallucinated answers pass.
```

## Stage 9: Multi-Program Scale And Final Promotion

Status:

```text
PENDING
```

Goal:

```text
Move from PDCBVC-only confidence to multi-program confidence.
```

Work:

```text
Index multiple programs.
Build global maps for calls, copybooks, datasets, DB2 tables, and transactions.
Test one enterprise collection with strict filters.
Measure retrieval quality and speed.
Promote combined mode only if it beats Hamza-only mode in evaluation.
Prepare final demo and thesis explanation.
```

Checkpoint:

```text
Run multi-program indexing.
Run cross-program eval.
Run ambiguous entity eval.
Run final smoke demo.
```

Pass condition:

```text
The system can answer scoped questions across many programs without mixing evidence.
Combined mode is source-aware and evaluated.
The final architecture is ready to present.
```

