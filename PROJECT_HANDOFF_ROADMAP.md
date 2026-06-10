# COBOL RAG Project Handoff And Roadmap

Created: 2026-06-08

Use this file as the first context document for any new AI chat. The goal is that the new chat can understand the project without the user re-explaining the repositories, branches, current pipeline, and remaining plan.

Important machine context:

```text
This local PC is mainly for development.
Do not assume Ollama/model runtime is available here.
Local checks should focus on code inspection, pipeline generation, deterministic final_scripts answers, unit/gold tests that do not need Ollama, and compile checks.
Full embedding sync, Chroma runtime validation, RAG LLM answers, and UI/model testing are normally run on the friend's PC.
```

## 1. What This Project Is

This project builds a RAG system for COBOL program understanding.

The current main program used for testing is:

```text
PDCBVC
```

The project combines two evidence sources:

```text
1. Hamza / MAPA / final_scripts analysis
2. Ermin / cobol-rekt knowledge-base_rag analysis
```

The output is indexed into a RAG UI so the user can ask technical questions such as:

```text
What calls does PDCBVC make?
Where is PD1VOCI-RETURN set?
What happens when the user presses PF7?
Which copybooks are unused?
How is the PD1VOCI COMMAREA prepared?
```

The final target is not a simple single-file RAG. The final target is a scalable COBOL RAG pipeline that can work across hundreds or thousands of COBOL files, with deterministic program/entity routing, strict metadata filtering, hybrid retrieval, source citations, and hallucination guards.

## 2. Repositories We Are Working On

There are two core repos and one optional/external repo.

### 2.1 Analysis Repo

Local path:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow
```

Remote:

```text
https://github.com/hamzaabedlkadr-b/legacy-program-analysis
```

Branch:

```text
feature/combine-cobol-rekt-analysis
```

Purpose:

```text
COBOL inputs
MAPA/control-flow inputs
copybooks/JCL inputs
fixed input packaging
final_scripts artifact generation
Hamza-only RAG JSONL generation
combined Hamza + cobol-rekt JSONL generation
```

Important files to inspect first:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\scripts\pipeline\run_fixed_input.py
C:\Users\Lenovo\Desktop\Camera\control_flow\scripts\pipeline\import_cobol_rekt_rag_bundle.py
C:\Users\Lenovo\Desktop\Camera\control_flow\scripts\pipeline\build_rag_index.py
C:\Users\Lenovo\Desktop\Camera\control_flow\scripts\pipeline\build_global_rag_maps.py
C:\Users\Lenovo\Desktop\Camera\control_flow\REPO_ORGANIZATION.md
C:\Users\Lenovo\Desktop\Camera\control_flow\input\README.md
C:\Users\Lenovo\Desktop\Camera\control_flow\PIPELINE_DIAGRAM.md
C:\Users\Lenovo\Desktop\Camera\control_flow\docs\combined_cobol_rekt_mapa_merge_report.md
```

Current local layout:

```text
input\                                  human COBOL/MAPA/control-flow inputs
artifacts\final\final_scripts\output\   generated active pipeline output
artifacts\final\final_scripts\work\     generated working packages
unused\                                 non-active samples, old outputs, anonymization, external clones
```

The old deep input path `artifacts\final\final_scripts\input\` is no longer the working input location. Use root `input\`.

Current state:

```text
Local branch tracks origin/feature/combine-cobol-rekt-analysis.
Last checked local HEAD matched the remote-tracking branch.
The worktree has many generated/untracked files and some modified/deleted input files.
Do not clean, reset, or delete anything unless the user explicitly asks.
```

Latest important pushed analysis commits on this branch:

```text
da7f412 Add constant optimization and compact RAG indexing
5c15835 Accept DOT controlflow inputs
940da68 Improve combined cobol-rekt MAPA evidence merge
d3948c3 Document combined RAG pipeline
5067e2b Support shared cobol-rekt bundle input
49ae35b Emit source-aware integration metadata and links
f33046d Improve copybook validation for fixed inputs
af08885 Normalize MAPA program names from paths
6ea6026 Fix fixed-input controlflow handling
2b668b2 Add PDCBVC fixed input files
ba3eb7a Add fixed final scripts input workflow
264e902 Add simple program test-case runner
```

### 2.2 RAG/UI Repo

Local path for the correct clean worktree:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui
```

Remote:

```text
https://github.com/erminlilaj/cobol-rag-pipeline.git
```

Branch:

```text
feature/combine-cobol-rekt-rag
```

Purpose:

```text
Load RAG JSONL
Sync/index into Chroma
Use LlamaIndex/Chroma retrieval
Use BM25 when available
Serve the RAG UI/API
Answer from deterministic final_scripts artifacts before using the LLM
Guard against off-evidence or hallucinated answers
```

Important files to inspect first:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\scripts\run_fixed_input_rag.sh
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\api.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\chat.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\query.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\retrieve.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\question_router.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\final_scripts_answers.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\sync.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\loaders\rag_documents.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\bm25.py
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\config\default.yaml
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\config\chunk_type_boosts.yaml
```

Current RAG branch status:

```text
feature/combine-cobol-rekt-rag tracks origin/feature/combine-cobol-rekt-rag.
The worktree was clean when last checked.
```

Latest important pushed RAG commits on this branch:

```text
d16e3d8 Route general and code questions explicitly
35500e0 Improve intent routing and answer guards
b5f3f3d Add RAG pipeline handoff docs
0b04d39 Catch generic off-evidence program answers
e0a531e Guard RAG answers against off-evidence prose
08e55bd Improve grounded RAG evidence synthesis
0bb59e0 Use structured artifacts as RAG evidence
e2abe19 Tune grounded RAG retrieval
59a716b Ground RAG answers in retrieved evidence
805a816 Refactor RAG script to use PYTHON_BIN variable and update answer_query to prioritize current question
082295a Prefer RAG retrieval for COBOL questions
1fee13f Fix retrieval boost config loading
```

### 2.3 Ermin / cobol-rekt Repo

Remote:

```text
https://github.com/erminlilaj/cobol-rekt
```

Role in this project:

```text
It produces the external knowledge-base_rag bundle.
Our combined pipeline imports this bundle as evidence.
We do not rewrite cobol-rekt output.
```

The important output folder is:

```text
knowledge-base_rag/
  manifest.json
  chunks/
```

For combined PDCBVC tests, place the bundle under:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\input\PDCBVC\knowledge-base_rag
```

The importer also accepts nested bundle layouts like:

```text
knowledge-base_rag\knowledge-base_rag\manifest.json
knowledge-base_rag\knowledge-base_rag\chunks\
```

## 3. Input And Output Layout

### 3.1 Fixed Input Layout

Program inputs live under:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\input\<PROGRAM>\
```

For PDCBVC:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\input\PDCBVC\
```

Expected shape:

```text
PDCBVC\
  PDCBVC.CBL
  PDCBVC_controlflow.json
  PDCBVC_result.csv or PDCBVC_result.txt
  copybooks\
  jcl\
  knowledge-base_rag\        optional, only for combined mode
```

### 3.2 Hamza-Only Analysis Output

Generated by:

```text
scripts\pipeline\run_fixed_input.py --program PDCBVC --mode my
```

Main outputs:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\program_artifacts\programs\PDCBVC\artifacts\
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\rag_index\rag_documents.jsonl
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\validation\
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\factory_report\
```

### 3.3 Combined Analysis Output

Generated by:

```text
scripts\pipeline\run_fixed_input.py --program PDCBVC --mode both
```

Main outputs:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\combined\final_scripts\PDCBVC\
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\combined\rag_index\PDCBVC_combined.jsonl
```

Combined mode preserves provenance. It does not overwrite Hamza facts with cobol-rekt facts. It adds source labels and integration records.

Important combined chunk families:

```text
integration.call_context
integration.paragraph_context
integration.variable_context
integration.entity_link
integration.source_balance
call_contract
paragraph_logic
workflow
controlflow.cfg
dataflow.variable
error_path
copybook_fields
screen.key_dispatch
screen.pagination
screen.selection
screen.row_build
unused_copybooks
program_summary
```

## 4. How To Run

Use Git Bash or WSL for the `.sh` script. PowerShell can run it through `bash`.

### 4.1 Pull Latest Code

Analysis repo:

```bash
cd /c/Users/Lenovo/Desktop/Camera/control_flow
git switch feature/combine-cobol-rekt-analysis
git pull --ff-only origin feature/combine-cobol-rekt-analysis
```

RAG/UI repo:

```bash
cd /c/Users/Lenovo/Desktop/Camera/cobol-rag-pipeline/.worktrees/ui
git switch feature/combine-cobol-rekt-rag
git pull --ff-only origin feature/combine-cobol-rekt-rag
pip install -e .
```

Always keep final_scripts LLM polishing disabled unless deliberately testing it:

```bash
export COBOL_RAG_LLM_POLISH_FINAL_SCRIPTS=false
```

### 4.2 Run Hamza-Only RAG

This builds Hamza-only analysis, indexes it, then starts the UI:

```bash
cd /c/Users/Lenovo/Desktop/Camera/cobol-rag-pipeline/.worktrees/ui

./scripts/run_fixed_input_rag.sh \
  --mode my \
  --program PDCBVC \
  --analysis-repo /c/Users/Lenovo/Desktop/Camera/control_flow \
  --build-analysis
```

The script indexes:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\rag_index\rag_documents.jsonl
```

Into:

```text
collection: cobol-fixed-pdcbvc
chroma:     data/chroma-fixed-pdcbvc
inbox:      data/inbox/control_flow_rag_documents.jsonl
```

Open:

```text
http://127.0.0.1:8000/
```

### 4.3 Run Combined RAG

Stop the previous UI server first with Ctrl+C.

This requires Ermin's cobol-rekt bundle here:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\input\PDCBVC\knowledge-base_rag\
```

Then run:

```bash
cd /c/Users/Lenovo/Desktop/Camera/cobol-rag-pipeline/.worktrees/ui

export COBOL_RAG_LLM_POLISH_FINAL_SCRIPTS=false

./scripts/run_fixed_input_rag.sh \
  --mode combined \
  --program PDCBVC \
  --analysis-repo /c/Users/Lenovo/Desktop/Camera/control_flow \
  --build-analysis
```

The script indexes:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\artifacts\final\final_scripts\output\combined\rag_index\PDCBVC_combined.jsonl
```

Into:

```text
collection: cobol-combined-pdcbvc
chroma:     data/chroma-combined-pdcbvc
inbox:      data/inbox/control_flow_rag_documents_combined.jsonl
```

Open:

```text
http://127.0.0.1:8000/
```

### 4.4 Run Indexing Only

Use this when you want to build/sync the index but not start the server:

```bash
./scripts/run_fixed_input_rag.sh \
  --mode combined \
  --program PDCBVC \
  --analysis-repo /c/Users/Lenovo/Desktop/Camera/control_flow \
  --build-analysis \
  --no-server
```

## 5. Current RAG Query Flow

The current RAG has two router layers before final answer generation.

### 5.1 First Router: General vs Code vs Ambiguous

File:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\query.py
```

Function:

```python
_route_question(question, config)
```

Purpose:

```text
Decide whether the user question is:
GENERAL   -> answer normally without COBOL retrieval
CODE      -> use COBOL evidence and retrieval
AMBIGUOUS -> ask the user for a program/entity
```

Implementation:

```text
Mostly deterministic rules first.
If the rules cannot decide, the code can ask the configured LLM to classify the question.
```

This router is not the detailed COBOL intent router. It only decides whether we should enter the COBOL RAG path.

### 5.2 Entity Guard

File:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\question_router.py
```

Function:

```python
preflight_entity_answer(question)
```

Purpose:

```text
Prevent hallucination when the user asks about an entity that is not indexed.
```

Implementation:

```text
Deterministic.
It builds an EntityIndex from final_scripts artifacts.
It checks programs, variables, paragraphs, copybooks, call targets, DB2 tables, SQL includes, screen fields, and evidence terms.
It returns a guarded answer if the entity is explicit but missing.
```

This is not controlled by the model.

### 5.3 Second Router: COBOL Intent Detection

File:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\retrieve.py
```

Function:

```python
_detect_intent(query)
```

Purpose:

```text
Select which evidence families should be preferred during retrieval.
```

Implementation:

```text
Deterministic keyword/regex cases.
No model is used here.
```

Current possible intents include:

```text
program_summary
external_programs
variable_dataflow
control_flow
ui_navigation
error_paths
business_rules
copybooks
datasets_tables
dead_code
static_values
comments
dependencies
general
```

Examples:

```text
"What calls does PDCBVC make?"
  -> external_programs

"Where is PD1VOCI-RETURN set?"
  -> variable_dataflow

"What happens when user presses PF7?"
  -> ui_navigation or control_flow

"How many unused copybooks?"
  -> copybooks or dead_code
```

Meaning:

```text
The intent controls chunk-type preference.
A call question should prefer call artifacts.
A variable question should prefer dataflow artifacts.
A PF-key question should prefer screen/CICS/control-flow artifacts.
```

### 5.4 Query Expansion

File:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\retrieve.py
```

Function:

```python
_expanded_query_for_intent(query, intent)
```

Implementation:

```text
Deterministic.
Adds COBOL domain terms depending on the detected intent.
```

Examples:

```text
external_programs -> LINK, XCTL, CALL, COMMAREA, target program
variable_dataflow -> read, write, move, set, modified, used
ui_navigation     -> PF, EIBAID, DFH, map, screen, pagination
```

### 5.5 Retrieval

File:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\retrieve.py
```

Function:

```python
retrieve(query, config, top_k=None, chunk_types=None)
```

Current behavior:

```text
1. Detect intent.
2. Expand query.
3. Retrieve from Chroma vector store.
4. If BM25 index is available and config says hybrid, also run BM25.
5. Fuse vector and BM25 results.
6. Rerank by intent, exact identifiers, integration context, coverage, and base score.
7. Expand companion records by entity_key where available.
```

Config:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\config\default.yaml
```

Important settings:

```yaml
retrieval:
  mode: hybrid
  top_k: 6
  bm25_top_k: 12

answers:
  llm_polish_final_scripts: false
```

Intent chunk boosts:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\config\chunk_type_boosts.yaml
```

### 5.6 Answer Generation And Guarding

File:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\src\cobol_rag\query.py
```

High-level answer flow:

```text
1. Extract current user question from chat history.
2. Try local/general answer.
3. Route GENERAL/CODE/AMBIGUOUS.
4. Try deterministic final_scripts answer.
5. Try program metadata answer.
6. Try entity guard.
7. Retrieve evidence if needed.
8. Validate retrieved evidence against named entities.
9. Validate intent evidence.
10. Ask LLM to compose answer only from evidence.
11. Reject off-evidence/generic answers.
12. Return grounded fallback if the LLM answer looks unsupported.
```

Important rule:

```text
Direct final_scripts answers should not be polished by the LLM by default.
```

Reason:

```text
The LLM previously invented generic business stories when it was allowed to rewrite deterministic COBOL evidence.
```

## 6. Role Of Chroma, LlamaIndex, And BM25

### Chroma

Role:

```text
Chroma stores embeddings for chunks and finds semantically similar chunks for a question.
```

How it works:

```text
The question is embedded into a vector.
Each indexed chunk already has a vector.
Chroma compares the query vector with chunk vectors and returns nearest chunks.
```

Good for:

```text
Meaning-based search.
Questions where wording differs from the chunk text.
```

Weakness:

```text
Can miss exact COBOL identifiers if semantic similarity is weak.
```

### BM25

Role:

```text
BM25 finds exact keyword and identifier matches.
```

Good for:

```text
COBOL variable names
copybook names
paragraph names
program names
literal values
PF keys
```

Weakness:

```text
Does not understand meaning or paraphrase.
```

### LlamaIndex

Role:

```text
LlamaIndex manages the retrieval pipeline around documents/nodes and vector-store access.
```

In this project:

```text
It is the orchestration layer around loaded documents, metadata, and Chroma retrieval.
It is not the database itself.
```

One-sentence summary:

```text
LlamaIndex orchestrates retrieval, Chroma searches by meaning, and BM25 searches by exact words.
```

## 7. Why Single-File RAG Is Not Enough For 1000 COBOL Files

The current PDCBVC test works because the corpus is small and the program is known.

For 1000 COBOL files, naive vector search over all chunks will fail because:

```text
too many chunks
many repeated COBOL names
same copybooks reused by many programs
same paragraph names across programs
generic chunks with high semantic similarity
questions may not name the program
LLM may combine evidence from wrong programs
```

Therefore the final system needs hierarchical retrieval:

```text
Enterprise corpus
  -> Program
      -> Intent/domain
          -> Entity
              -> Evidence chunks
```

The retrieval must go down the tree before searching deeply.

## 8. Target Hierarchical Retrieval Algorithm

The next major project direction is to implement a tree-based retrieval layer.

### 8.1 Target Tree

```text
enterprise
  programs
    PDCBVC
      summary
      calls
        PD1VOCI
        PD1FS00
        PD0UTI01
      variables
        PD1VOCI-RETURN
        TWCOB-FUNZIONE
      paragraphs
        INIZ-PARAM
        LINK-PD1VOCI
        PREP-RIGA
      ui_navigation
        PF7
        PF8
        ENTER
      copybooks
        PDRTWA2
        PD1VOCI
      db2_tables
      datasets
      errors
```

### 8.2 Target Query Algorithm

Pseudo-code:

```python
def answer(question):
    route = route_general_code_ambiguous(question)
    if route == "GENERAL":
        return answer_general(question)
    if route == "AMBIGUOUS":
        return ask_clarification(question)

    scope = resolve_program_scope(question)
    intent = detect_intent(question)
    entities = resolve_entities(question, scope)

    if scope.is_ambiguous or entities.are_ambiguous:
        return ask_clarification(scope, entities)

    where = build_metadata_filter(scope, intent, entities)

    leaf_hits = hybrid_search(
        query=expand_query(question, intent),
        where=where,
        vector_store="Chroma",
        keyword_index="BM25",
    )

    context = expand_context(
        hits=leaf_hits,
        include_parent=True,
        include_siblings=True,
        include_cross_source_integration=True,
    )

    validate_context(question, intent, entities, context)
    return generate_grounded_answer(question, context)
```

### 8.3 Metadata Needed For The Tree

Every indexed record should contain enough metadata to filter before search.

Recommended metadata fields:

```text
program
program_group
source_system
source_repo
chunk_type
intent_domain
entity_type
entity_key
entity_name
parent_id
parent_type
child_ids
hierarchy_level
coverage_dimension
call_type
target
variable
paragraph
copybook
screen_key
dataset
db2_table
line_start
line_end
evidence_path
confidence_tier
conflict_status
factory_content_hash
```

Recommended hierarchy levels:

```text
enterprise
program
domain
entity
evidence
```

### 8.4 Search Branch Selection

Examples:

Call question:

```text
Question: "What calls does PDCBVC make?"

program = PDCBVC
intent_domain = external_programs
entity_type = call_target or program_call
chunk_types = integration.call_context, architecture.calls, architecture.call_parameters, call_contract
```

Variable question:

```text
Question: "Where is PD1VOCI-RETURN set?"

program = PDCBVC
intent_domain = variable_dataflow
entity_key = PD1VOCI-RETURN
chunk_types = integration.variable_context, dataflow.variable, dataflow.used_variables
```

UI question:

```text
Question: "What happens on PF7?"

program = resolved from question or current chat context
intent_domain = ui_navigation
entity_key = PF7
chunk_types = screen.key_dispatch, screen.pagination, ui.cics.navigation, controlflow.cfg
```

Unknown or ambiguous question:

```text
Question: "Where is RETURN set?"

If RETURN appears in many programs or variables:
ask the user to choose program/entity.
Do not search the entire corpus and guess.
```

## 9. Roadmap To Finish The Project

### Phase 0: Stabilize Current PDCBVC Baseline

Status:

```text
Mostly done.
```

Tasks:

```text
Keep Hamza-only mode working.
Keep combined mode working.
Keep final_scripts answers deterministic.
Keep COBOL_RAG_LLM_POLISH_FINAL_SCRIPTS=false by default.
Add/keep gold questions for bad answers that were fixed.
```

Success criteria:

```text
PDCBVC answers use real evidence.
No generic customer/travel/booking hallucinations.
Unknown variables/programs get guarded "not indexed/evidenced" answers.
```

### Phase 1: Define The Enterprise Metadata Schema

Status:

```text
Next.
```

Main repo:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow
```

Likely files to change:

```text
scripts\pipeline\build_rag_index.py
scripts\pipeline\build_global_rag_maps.py
scripts\pipeline\import_cobol_rekt_rag_bundle.py
```

Goal:

```text
Every RAG JSONL record should expose program, domain, entity, parent, and evidence metadata.
```

Output should include:

```text
rag_documents.jsonl
rag_hierarchy.jsonl
entity_index.json
program_index.json
relationship_index.json
```

### Phase 2: Build Program And Entity Indexes

Goal:

```text
Create deterministic maps that answer:
Which programs exist?
Which variables belong to which program?
Which paragraph/copybook/call target belongs to which program?
Which entities are ambiguous across programs?
```

Example data structure:

```json
{
  "programs": {
    "PDCBVC": {
      "variables": ["PD1VOCI-RETURN", "TWCOB-FUNZIONE"],
      "paragraphs": ["INIZ-PARAM", "LINK-PD1VOCI"],
      "call_targets": ["PD1VOCI", "PD1FS00"],
      "copybooks": ["PDRTWA2", "PD1VOCI"]
    }
  },
  "entity_to_programs": {
    "PD1VOCI-RETURN": ["PDCBVC"],
    "RETURN": ["many"]
  }
}
```

Success criteria:

```text
A question can be routed to a program/entity before vector search.
Ambiguous questions ask clarification instead of guessing.
```

### Phase 3: Add Hierarchical Metadata To The RAG Loader

Main repo:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui
```

Likely files to change:

```text
src\cobol_rag\loaders\rag_documents.py
src\cobol_rag\sync.py
```

Goal:

```text
Preserve all hierarchy metadata when loading JSONL into Chroma.
Do not lose parent_id, entity_key, intent_domain, hierarchy_level, or evidence_path.
```

Success criteria:

```text
Chroma records can be filtered by program, intent_domain, entity_key, and hierarchy_level.
```

### Phase 4: Implement Program Scope Resolver

Likely files:

```text
src\cobol_rag\query.py
src\cobol_rag\question_router.py
```

Goal:

```text
Before retrieval, determine the program scope.
```

Rules:

```text
If the question names a program, use that program.
If the question names a unique entity, infer the program from the entity index.
If the chat already has a current program and the question is follow-up, use the current program.
If multiple programs match, ask clarification.
If the question is cross-program, use global relationship indexes.
```

Success criteria:

```text
The retriever never searches all 1000 programs for a local variable question.
```

### Phase 5: Implement Filtered Hybrid Retrieval

Likely file:

```text
src\cobol_rag\retrieve.py
```

Goal:

```text
Build metadata filters from program, intent, and entity before calling Chroma/BM25.
```

Example filter:

```python
where = {
    "$and": [
        {"program": {"$eq": "PDCBVC"}},
        {"intent_domain": {"$eq": "variable_dataflow"}},
        {"entity_key": {"$eq": "PD1VOCI-RETURN"}},
    ]
}
```

Important:

```text
Vector search should happen inside the selected branch.
BM25 should also be restricted to the selected branch, or reranked with strong branch penalties.
```

Success criteria:

```text
Top results are from the correct program and entity.
Wrong-program chunks cannot outrank exact local evidence.
```

### Phase 6: Add Parent/Sibling Expansion

Goal:

```text
After retrieving exact leaf chunks, add enough surrounding context.
```

Expansion rules:

```text
If leaf is a variable write, add parent variable summary.
If leaf is a call parameter, add parent call context.
If leaf is a paragraph evidence chunk, add paragraph summary and adjacent CFG edges.
If combined mode is active, add integration context for the same entity_key.
```

This is the "go down the tree, then expand upward/sideways" algorithm.

Success criteria:

```text
Answers include exact line facts plus enough explanation to be useful.
The system does not retrieve random large chunks just to get context.
```

### Phase 7: Evaluation Set For 1000-File Scaling

Create a gold eval suite with these categories:

```text
program summary
external calls
call parameters
variable dataflow
control flow
UI navigation
PF keys
error paths
copybooks
unused/dead code
DB2 tables
datasets/JCL
cross-program dependencies
ambiguous entity questions
unknown entity questions
```

Likely files:

```text
C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui\eval\
```

Success criteria:

```text
Every answer must cite indexed evidence.
Unknown entities must be rejected.
Ambiguous entities must ask clarification.
No answer may combine facts from unrelated programs.
```

### Phase 8: Scale Indexing To Many Programs

Goal:

```text
Run the fixed input pipeline for many programs, not only PDCBVC.
```

Implementation direction:

```text
Use one enterprise collection or carefully sharded collections.
Prefer one logical enterprise corpus with strict metadata filters.
Allow incremental sync using content hashes.
Preserve collection manifests.
Build global maps for cross-program calls, copybooks, DB2 tables, datasets, and transactions.
```

Suggested collection strategy:

```text
cobol-enterprise
```

Required filters:

```text
program
intent_domain
entity_key
chunk_type
source_system
hierarchy_level
```

When to shard:

```text
If Chroma performance becomes poor, shard by application/domain or program family.
Do not start with one collection per program unless operationally necessary.
```

### Phase 9: Promote Combined Mode

Combined mode should become the main mode only after evaluation proves it improves answers.

Promotion criteria:

```text
Combined answers are more complete than Hamza-only answers.
Combined answers do not hallucinate.
Conflicts are clearly labeled.
Source provenance is visible.
Exact static facts still prefer Hamza/final_scripts evidence.
cobol-rekt context is used as supporting explanation.
```

## 10. What To Prefer From Each Evidence Source

Prefer Hamza / MAPA / final_scripts for:

```text
exact call inventory
exact call line/statement
call parameters and COMMAREA
copybook inventory
generated control-flow graph edges
variable read/write/control sites
business rules extracted from final_scripts
quality/dead-code artifacts
stable line-level facts
```

Prefer cobol-rekt for:

```text
paragraph intent
call-contract context
workflow summaries
expanded variable/dataflow context
error-path descriptions
CICS/screen behavior chunks
copybook fields and ownership-style observations
analysis health and quality context
```

Use integration records for:

```text
natural answers that combine exact facts with context
source balance explanations
entity-linked MAPA + cobol-rekt evidence
conflict-aware summaries
```

Conflict policy:

```text
Do not silently overwrite facts.
Keep both facts with source labels.
Only choose a winner when a documented source policy says so.
```

## 11. Good Test Questions

Use these after running the UI:

```text
Which copybooks are included by PDCBVC.CBL, and what role does each one play in the program?
How does PDCBVC decide whether to start from BROWSE-FASE1 or BROWSE-FASE2, and which TWA field controls this decision?
What happens when TWCOB-FUNZIONE is one of I, A, C, D, or P and TWCOB-ID-SISTEMA = 'IP'?
Which semaphore is checked before allowing insert/update operations, and how is the semaphore request prepared?
How does PDCBVC prepare the communication area before linking to PD1VOCI?
Which fields from PDRTWA2 are copied into the PD1VOCI copybook before the CICS LINK?
How does TWCOB-VARCONT-NUMFUNZ change the value of PD1VOCI-FUNZIONE and PD1VOCI-TIPO-VOCE?
When does PDCBVC call PD1FS00, and what information does it obtain from the PD1FS00 copybook?
How does PDCBVC display the session status on the map, and which values of PD1FS00-SESS-FLAG correspond to Aperta, Chiusa, and Liquidata?
How does PDCBVC calculate the total number of pages for the browse result?
Where is PD1VOCI-RETURN set and checked?
What happens when user presses PF7?
How many unused copybooks are there and which source reported them?
```

Expected answer behavior:

```text
Use indexed evidence.
Mention sources when relevant.
Do not invent business domain stories.
Do not answer unknown entities as if they exist.
Ask clarification when entity/program scope is ambiguous.
```

## 12. Debug Checklist

### 12.1 Check Branches

Analysis:

```bash
cd /c/Users/Lenovo/Desktop/Camera/control_flow
git status --short --branch
git log --oneline -3
```

Expected branch:

```text
feature/combine-cobol-rekt-analysis
```

RAG/UI:

```bash
cd /c/Users/Lenovo/Desktop/Camera/cobol-rag-pipeline/.worktrees/ui
git status --short --branch
git log --oneline -3
```

Expected branch:

```text
feature/combine-cobol-rekt-rag
```

### 12.2 Check Environment Variables

```bash
echo "$COBOL_RAG_FINAL_SCRIPTS_DIR"
echo "$COBOL_RAG_COLLECTION"
echo "$COBOL_RAG_CHROMA_DIR"
echo "$COBOL_RAG_LLM_POLISH_FINAL_SCRIPTS"
```

For Hamza-only PDCBVC:

```text
COBOL_RAG_FINAL_SCRIPTS_DIR = ...output/program_artifacts/programs/PDCBVC/artifacts
COBOL_RAG_COLLECTION        = cobol-fixed-pdcbvc
COBOL_RAG_CHROMA_DIR        = data/chroma-fixed-pdcbvc
```

For combined PDCBVC:

```text
COBOL_RAG_FINAL_SCRIPTS_DIR = ...output/combined/final_scripts/PDCBVC
COBOL_RAG_COLLECTION        = cobol-combined-pdcbvc
COBOL_RAG_CHROMA_DIR        = data/chroma-combined-pdcbvc
```

Polishing should be:

```text
false or unset
```

### 12.3 Check Server Restart

If answers look stale:

```text
Stop uvicorn with Ctrl+C.
Start it again with scripts/run_fixed_input_rag.sh.
```

Old servers can keep old config and old code loaded.

### 12.4 Check For Missing Combined Bundle

If combined mode fails, check:

```text
C:\Users\Lenovo\Desktop\Camera\control_flow\input\PDCBVC\knowledge-base_rag\manifest.json
C:\Users\Lenovo\Desktop\Camera\control_flow\input\PDCBVC\knowledge-base_rag\chunks\
```

If missing, combined mode cannot import Ermin/cobol-rekt evidence.

## 13. Known Risks And Limitations

Current limitations:

```text
PDCBVC is the strongest tested program.
Multi-program enterprise routing is not finished yet.
Combined mode is promising but should not replace Hamza-only mode until evaluated.
Some JCL/dataset questions require JCL artifacts to be present and indexed.
Unused copybook detection is still partly heuristic.
Very broad questions can still retrieve noisy evidence unless scoped.
BM25 only helps when the BM25 index is available in the manifest.
```

Main technical risk:

```text
Without hierarchical filtering, 1000-file RAG will retrieve plausible but wrong chunks from other programs.
```

Main mitigation:

```text
Implement program/entity/intent routing before vector search.
```

## 14. Definition Of Done For The Thesis-Quality System

The project is in a good final state when:

```text
1. The pipeline can ingest many COBOL programs.
2. Every chunk has strong metadata.
3. The system can resolve program/entity scope before retrieval.
4. Retrieval uses hybrid Chroma + BM25 inside the selected branch.
5. Parent/sibling expansion adds context after exact leaf retrieval.
6. Answers cite or name evidence sources.
7. Unknown entities are rejected.
8. Ambiguous questions ask clarification.
9. Combined MAPA + cobol-rekt mode preserves source provenance.
10. A gold evaluation suite proves that answers are grounded and stable.
```

Short final architecture:

```text
COBOL inputs
  -> Hamza/MAPA final_scripts
  -> optional cobol-rekt knowledge-base_rag
  -> combined source-labeled RAG JSONL
  -> hierarchy/entity/program indexes
  -> Chroma + BM25 enterprise index
  -> program router
  -> intent router
  -> entity resolver
  -> metadata-filtered hybrid retrieval
  -> parent/sibling expansion
  -> evidence validator
  -> grounded answer with sources
```

## 15. First Instruction For A New AI Chat

If a new chat starts, tell it:

```text
Read C:\Users\Lenovo\Desktop\Camera\control_flow\PROJECT_HANDOFF_ROADMAP.md first.
Then inspect the files listed in sections 2, 5, and 8.
Do not reset the git worktree.
Do not delete generated files.
Use the RAG worktree at C:\Users\Lenovo\Desktop\Camera\cobol-rag-pipeline\.worktrees\ui.
Continue from the roadmap, especially the hierarchical retrieval phases.
```

