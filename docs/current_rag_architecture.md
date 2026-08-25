# Current COBOL RAG Architecture

This diagram represents the current organized pipeline after the research recommendations were implemented on 2026-08-17.

The measured baseline now includes a typed request compiler, LLM semantic refinement, deterministic program/entity resolution, structured focused session scope, metadata-filtered hybrid retrieval, corrective exact-identifier lookup, bounded parent/sibling expansion, normalized evidence views, evidence validation, per-answer traces, trace-linked feedback, prompt-injection regressions, and checked-in development plus sealed holdout evaluation suites.

The 2026-08-25 hardening is backward-compatible: detailed analyzer artifacts remain
the source of truth. The pipeline adds a compact `evidence.normalized` view containing
capability, entity key, claim type, exact typed facts, and provenance. It also removes
obsolete per-variable artifacts from reused runs so corrected analysis results cannot
remain searchable in either the base or combined output.

## Build And Indexing Flow

```mermaid
flowchart LR
  subgraph input["Root input folder"]
    pdc["input/PDCBVC"]
    cbl["PDCBVC.CBL"]
    mapa["PDCBVC_result.txt"]
    cfg["PDCBVC_controlflow.json"]
    copybooks["copybooks/"]
    rekt["knowledge-base_rag/<br/>optional combined mode"]
    pdc --> cbl
    pdc --> mapa
    pdc --> cfg
    pdc --> copybooks
    pdc --> rekt
  end

  subgraph analysis["Analysis repo: control_flow"]
    runner["run_fixed_input.py"]
    packages["work/program_packages"]
    builders["final_scripts builders"]
    artifacts["output/program_artifacts/<br/>programs/PDCBVC/artifacts"]
    maps["global RAG maps<br/>program_index<br/>entity_index<br/>relationship_index"]
    hamza_jsonl["Hamza RAG JSONL<br/>rag_documents.jsonl"]
    combined_import["cobol-rekt importer"]
    combined_artifacts["combined final_scripts<br/>output/combined/final_scripts/PDCBVC"]
    combined_jsonl["Combined RAG JSONL<br/>PDCBVC_combined.jsonl"]
  end

  subgraph metadata["Metadata added to every RAG record"]
    entity_key["entity_key"]
    intent_domain["intent_domain"]
    hierarchy["hierarchy_level"]
    parent["parent_id / parent_type"]
    parent_groups["program/domain/entity parent ids"]
    evidence_path["evidence_path"]
    lineage["source/artifact/content hashes<br/>schema + extractor version"]
    access["access_scope + security classification"]
  end

  subgraph ragui["RAG/UI repo: cobol-rag-pipeline"]
    loader["rag_documents loader<br/>preserves metadata"]
    sync["sync/index"]
    chroma["Chroma vector store"]
    bm25["BM25 lexical index"]
    collection_my["cobol-fixed-pdcbvc"]
    collection_combined["cobol-combined-pdcbvc"]
  end

  cbl --> runner
  mapa --> runner
  cfg --> runner
  copybooks --> runner
  runner --> packages
  packages --> builders
  builders --> artifacts
  artifacts --> maps
  artifacts --> hamza_jsonl
  maps --> hamza_jsonl
  hamza_jsonl --> metadata

  rekt --> combined_import
  artifacts --> combined_import
  hamza_jsonl --> combined_import
  combined_import --> combined_artifacts
  combined_import --> combined_jsonl
  combined_jsonl --> metadata

  hamza_jsonl --> loader
  combined_jsonl --> loader
  loader --> sync
  sync --> chroma
  sync --> bm25
  chroma --> collection_my
  chroma --> collection_combined
```

## Query-Time Answer Flow

```mermaid
flowchart TD
  user["User question"]
  exact["Deterministic program/entity dispatch<br/>exact final_scripts facts"]
  exact_hit{"Authoritative answer found?"}
  scope["Resolve program + entity<br/>question or structured session state"]
  scope_route{"Deterministic route/intent certain?"}
  semantic["LLM semantic router<br/>route + canonical technical intent"]
  route{"Selected route"}
  intent_dispatch["Intent-driven final_scripts dispatch"]
  intent_hit{"Authoritative answer found?"}
  filters["Metadata filters<br/>program, entity, intent, source"]
  vector["Chroma semantic search"]
  lexical["BM25 keyword search"]
  rerank["merge + score + rerank"]
  correction["Corrective exact-identifier retrieval<br/>inside selected program"]
  expansion["Bounded parent/sibling expansion"]
  conversation["Conversational/clarification reply<br/>no evidence sources"]
  abstain["Explicit abstention<br/>rejected hits stay only in trace"]
  trace["Trace log + optional feedback"]

  subgraph evidence["Evidence sources"]
    hamza["Hamza/MAPA evidence<br/>calls, copybooks, CFG, variables,<br/>business rules, source-backed CICS"]
    ermin["Ermin/cobol-rekt evidence<br/>call contracts, paragraph logic,<br/>workflows, error paths, summaries"]
    maps["sidecar indexes<br/>program/entity/relationship"]
  end

  subgraph answer["Answer generation"]
    guard["hallucination guard<br/>no evidence means no inference"]
    llm["LLM synthesis<br/>only after evidence retrieval"]
    final["Final answer + cited sources"]
  end

  user --> exact --> exact_hit
  exact_hit -- yes --> final
  exact_hit -- no --> scope --> scope_route
  scope_route -- no or ambiguous --> semantic --> route
  scope_route -- technical --> intent_dispatch
  route -- conversational or unclear --> conversation
  route -- technical --> intent_dispatch --> intent_hit
  intent_hit -- yes --> final
  intent_hit -- no --> filters
  filters --> vector
  filters --> lexical

  maps --> exact
  maps --> intent_dispatch
  hamza --> exact
  hamza --> intent_dispatch
  hamza --> vector
  hamza --> lexical
  ermin --> vector
  ermin --> lexical

  vector --> rerank
  lexical --> rerank
  rerank --> correction --> expansion --> guard
  guard -- sufficient --> llm
  guard -- insufficient --> abstain
  llm --> final
  final --> trace
  abstain --> trace
  conversation --> trace
```

## Key Idea

The current system is not a simple vector search over random chunks. It is a metadata-aware hybrid RAG:

```text
question
  -> try deterministic program/entity artifact dispatch
  -> resolve program/entity from the question or structured session state
  -> use the semantic router only when route or intent remains ambiguous
  -> try the intent-specific final_scripts handler
  -> only then apply program metadata filters and retrieve with Chroma + lexical BM25-style scoring
  -> retry exact identifiers and add bounded parent/sibling context
  -> validate program/entity evidence and abstain when it fails
  -> use answer generation only for evidence requests with no authoritative handler
  -> return answer with sources and persist a trace for evaluation/feedback
```

This two-pass dispatch is the paraphrase mechanism: exact wording is not required. A rephrased technical request is mapped to a stable intent such as `control_flow`, `cics_operations`, or `business_rules`, and that intent selects the authoritative artifact.
