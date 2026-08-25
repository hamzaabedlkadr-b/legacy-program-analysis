from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_build_rag_index_call_metadata_entity_key():
    build_rag_index = _load_module("scripts/pipeline/build_rag_index.py", "build_rag_index")

    metadata = build_rag_index.call_metadata(
        {"content": {"target": "PD1VOCI", "call_type": "CICSLINKBYLITERAL"}},
        "architecture.call",
        "PDCBVC",
        Path("architecture.call.CICSLINKBYLITERAL.PD1VOCI.json"),
    )

    assert metadata["entity_type"] == "call"
    assert metadata["entity_key"] == "PDCBVC|PD1VOCI|LINK"
    assert metadata["target"] == "PD1VOCI"
    assert metadata["call_type"] == "LINK"


def test_build_rag_index_record_preserves_source_metadata(tmp_path: Path):
    build_rag_index = _load_module("scripts/pipeline/build_rag_index.py", "build_rag_index_record")
    artifact = tmp_path / "programs" / "PDCBVC" / "artifacts" / "architecture.call" / "architecture.call.CICSLINKBYLITERAL.PD1VOCI.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"content": {"target": "PD1VOCI", "call_type": "CICSLINKBYLITERAL"}}),
        encoding="utf-8",
    )
    records = []

    build_rag_index.add_json_source_file(
        artifact,
        default_program="PDCBVC",
        base_root=tmp_path,
        records=records,
        invalid_files=[],
        by_program=build_rag_index.Counter(),
        by_type=build_rag_index.Counter(),
        program_types=build_rag_index.defaultdict(build_rag_index.Counter),
        max_chars=12000,
        overlap=600,
        profile="full",
    )

    metadata = records[0]["metadata"]
    assert metadata["source_system"] == "mapa_hamza"
    assert metadata["chunk_type"] == "architecture.call"
    assert metadata["source_chunk_type"] == "architecture.call"
    assert metadata["coverage_dimension"] == "static_inventory"
    assert metadata["entity_key"] == "PDCBVC|PD1VOCI|LINK"
    assert metadata["intent_domain"] == "external_programs"
    assert metadata["program_parent_id"] == "program:PDCBVC"
    assert metadata["domain_parent_id"] == "domain:PDCBVC:external_programs"
    assert metadata["entity_parent_id"] == "entity:PDCBVC|PD1VOCI|LINK"
    assert metadata["node_id"] == "entity:PDCBVC|PD1VOCI|LINK"
    assert metadata["parent_id"] == "domain:PDCBVC:external_programs"
    assert len(metadata["source_sha256"]) == 64
    assert len(metadata["artifact_hash"]) == 32
    assert len(metadata["content_hash"]) == 24
    assert metadata["extractor_version"] == "rag-index-v2"
    assert metadata["index_schema_version"] == "2"
    assert metadata["access_scope"] == "project"
    assert metadata["security_classification"] == "internal"


def test_normalized_evidence_is_indexed_with_typed_entity_and_domain(tmp_path: Path):
    build_rag_index = _load_module("scripts/pipeline/build_rag_index.py", "normalized_rag_index")
    artifact = (
        tmp_path / "programs" / "PDCBVC" / "artifacts" /
        "evidence.normalized" / "evidence.normalized.json"
    )
    artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps([{
        "id": "normalized-variable",
        "type": "evidence.normalized",
        "program": "PDCBVC",
        "title": "PDCBVC variable HSQL-DATE",
        "embedding_text": "HSQL-DATE is written by SELECT INTO.",
        "content": {
            "capability": "variable_access",
            "entity_type": "variable",
            "entity": "HSQL-DATE",
            "entity_key": "PDCBVC|VARIABLE|HSQL-DATE",
            "claim_type": "variable_access",
            "facts": [],
        },
    }]), encoding="utf-8")
    records = []
    build_rag_index.add_json_source_file(
        artifact, default_program="PDCBVC", base_root=tmp_path,
        records=records, invalid_files=[],
        by_program=build_rag_index.Counter(), by_type=build_rag_index.Counter(),
        program_types=build_rag_index.defaultdict(build_rag_index.Counter),
        max_chars=12000, overlap=600, profile="full",
    )
    metadata = records[0]["metadata"]
    assert metadata["source_system"] == "normalized_view"
    assert metadata["entity_key"] == "PDCBVC|VARIABLE|HSQL-DATE"
    assert metadata["intent_domain"] == "variable_dataflow"
    assert metadata["evidence_capability"] == "variable_access"


def test_normalized_evidence_builder_preserves_exact_variable_and_call_facts(tmp_path: Path):
    builder = _load_module(
        "scripts/pipeline/build_normalized_evidence.py", "normalized_evidence_builder",
    )
    variable_dir = tmp_path / "dataflow.variable"
    variable_dir.mkdir()
    (variable_dir / "dataflow.variable.FIELD-A.json").write_text(json.dumps({
        "content": {
            "variable": "FIELD-A", "origin": "WORKING-STORAGE",
            "controls_flow": True, "fanout_nodes": ["ABEND00"],
            "relationships": {"parents": ["AREA-A"], "children": [], "declarations": [{
                "line_start": 10, "source_file": "DEMO.CBL",
                "statement": "05 FIELD-A PIC X.",
            }]},
            "evidence": {"write_sites": [{
                "paragraph": "INIT", "line_start": 20,
                "statement": "MOVE 'Y' TO FIELD-A.",
            }], "read_sites": [{
                "paragraph": "CHECK-A", "line_start": 30,
                "statement": "IF FIELD-A = 'Y'",
            }]},
        },
    }), encoding="utf-8")
    (tmp_path / "architecture.call_parameters.json").write_text(json.dumps({
        "calls": [{
            "target": "SUBPGM", "call_type": "CICSLINK", "paragraph": "CALL-SUB",
            "line_start": 40, "statement": "EXEC CICS LINK PROGRAM('SUBPGM') END-EXEC.",
            "parameters": ["AREA-A"], "commarea": "AREA-A", "length": "100",
        }],
    }), encoding="utf-8")
    records = builder.build_normalized_evidence(tmp_path, "DEMO")
    variable = next(item for item in records if item["content"]["entity"] == "FIELD-A")
    call = next(item for item in records if item["content"]["entity"] == "SUBPGM")
    assert {fact["role"] for fact in variable["content"]["facts"]} == {
        "declaration", "write", "read",
    }
    assert "line 20" in variable["embedding_text"]
    assert call["content"]["attributes"]["commarea"] == "AREA-A"
    assert call["content"]["attributes"]["length"] == "100"


def test_normalized_evidence_ignores_stale_variable_files(tmp_path: Path):
    builder = _load_module(
        "scripts/pipeline/build_normalized_evidence.py", "normalized_evidence_stale_guard",
    )
    variable_dir = tmp_path / "dataflow.variable"
    variable_dir.mkdir()
    for variable in ("CURRENT-FIELD", "STALE-FIELD"):
        (variable_dir / f"dataflow.variable.{variable}.json").write_text(json.dumps({
            "content": {"variable": variable, "evidence": {}, "relationships": {}},
        }), encoding="utf-8")
    (tmp_path / "dataflow.used_variables.json").write_text(json.dumps({
        "variables": [{"variable": "CURRENT-FIELD"}],
    }), encoding="utf-8")

    records = builder.build_normalized_evidence(tmp_path, "DEMO")
    entities = {item["content"]["entity"] for item in records}

    assert "CURRENT-FIELD" in entities
    assert "STALE-FIELD" not in entities


def test_variable_artifact_builder_removes_only_stale_variable_outputs(tmp_path: Path):
    builder = _load_module(
        "artifacts/final/final_scripts/dataflow.variable/build_dataflow_variable_details.py",
        "variable_artifact_stale_cleanup",
    )
    current = tmp_path / "dataflow.variable.CURRENT-FIELD.json"
    stale = tmp_path / "dataflow.variable.STALE-FIELD.json"
    unrelated = tmp_path / "notes.json"
    current.write_text("{}", encoding="utf-8")
    stale.write_text("{}", encoding="utf-8")
    unrelated.write_text("{}", encoding="utf-8")

    removed = builder.remove_stale_outputs(tmp_path, {current.name})

    assert removed == 1
    assert current.exists()
    assert not stale.exists()
    assert unrelated.exists()


def test_combined_baseline_copy_mirrors_analyzer_directories(tmp_path: Path):
    importer = _load_module(
        "scripts/pipeline/import_cobol_rekt_rag_bundle.py", "baseline_mirror_importer",
    )
    source = tmp_path / "source"
    target = tmp_path / "combined"
    (source / "dataflow.variable").mkdir(parents=True)
    (target / "dataflow.variable").mkdir(parents=True)
    (target / "integration.entity_link").mkdir(parents=True)
    (source / "dataflow.variable" / "current.json").write_text("{}", encoding="utf-8")
    (target / "dataflow.variable" / "stale.json").write_text("{}", encoding="utf-8")
    integration = target / "integration.entity_link" / "link.json"
    integration.write_text("{}", encoding="utf-8")

    importer.copy_baseline(source, target)

    assert (target / "dataflow.variable" / "current.json").exists()
    assert not (target / "dataflow.variable" / "stale.json").exists()
    assert integration.exists()


def test_dataflow_target_subscript_is_read_not_modified():
    extractor = _load_module("scripts/pipeline/extract_dataflow.py", "typed_dataflow_subscript")

    writes, reads, read_writes, subscripts = extractor.detect_statement_accesses(
        "MOVE RIGA-MAPPA TO MRIGAO(WCTRIG)"
    )

    assert writes == {"MRIGAO"}
    assert "WCTRIG" in reads
    assert read_writes == set()
    assert subscripts == {"WCTRIG"}


def test_dataflow_inline_arithmetic_records_read_write_target():
    extractor = _load_module("scripts/pipeline/extract_dataflow.py", "typed_dataflow_inline")

    writes, reads, read_writes, subscripts = extractor.detect_statement_accesses(
        "IF RIGA-MAPPA NOT EQUAL SPACES THEN ADD 1 TO NPAGT"
    )

    assert "NPAGT" in writes
    assert "NPAGT" in reads
    assert "NPAGT" in read_writes
    assert "RIGA-MAPPA" in reads
    assert subscripts == set()


def test_dataflow_declarations_create_typed_parent_child_and_redefines_relations():
    extractor = _load_module("scripts/pipeline/extract_dataflow.py", "typed_dataflow_relations")
    statements = [
        (1, "DATA DIVISION."),
        (2, "WORKING-STORAGE SECTION."),
        (3, "01 CUSTOMER-AREA."),
        (4, "05 CUSTOMER-ID PIC X(10)."),
        (5, "05 CUSTOMER-STATUS PIC X."),
        (6, "01 CUSTOMER-VIEW REDEFINES CUSTOMER-AREA."),
    ]

    relations = extractor.parse_declaration_relations(statements, None)

    assert relations["CUSTOMER-ID"]["parents"] == ["CUSTOMER-AREA"]
    assert relations["CUSTOMER-AREA"]["children"] == ["CUSTOMER-ID", "CUSTOMER-STATUS"]
    assert relations["CUSTOMER-VIEW"]["redefines"] == ["CUSTOMER-AREA"]
    assert relations["CUSTOMER-AREA"]["redefined_by"] == ["CUSTOMER-VIEW"]


def test_importer_makes_integration_entity_link_records(tmp_path: Path):
    importer = _load_module("scripts/pipeline/import_cobol_rekt_rag_bundle.py", "importer")
    base = tmp_path / "base.jsonl"
    base.write_text(
        json.dumps(
            {
                "id": "mapa-call",
                "program": "PDCBVC",
                "type": "architecture.call",
                "text": "PDCBVC calls PD1VOCI.",
                "metadata": {
                    "source_system": "mapa_hamza",
                    "chunk_type": "architecture.call",
                    "entity_type": "call",
                    "entity_key": "PDCBVC|PD1VOCI|LINK",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    records, artifact = importer.make_entity_link_records(
        program="PDCBVC",
        base_rag_jsonl=base,
        cobol_rekt_records=[
            {
                "id": "rekt-call",
                "metadata": {
                    "source_system": "cobol_rekt",
                    "chunk_type": "cobol_rekt.call_contract",
                    "entity_type": "call",
                    "entity_key": "PDCBVC|PD1VOCI|LINK",
                },
            }
        ],
    )

    assert len(records) == 1
    assert records[0]["type"] == "integration.entity_link"
    assert records[0]["metadata"]["entity_key"] == "PDCBVC|PD1VOCI|LINK"
    assert artifact["link_count"] == 1



def test_copybook_builder_extracts_portable_source_locations(tmp_path: Path):
    builder = _load_module(
        "artifacts/final/final_scripts/architecture.copybooks/build_architecture_copybooks.py",
        "copybook_location_builder",
    )
    source = tmp_path / "DEMO.CBL"
    source.write_text(
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. DEMO.\n"
        "       DATA DIVISION.\n"
        "       WORKING-STORAGE SECTION.\n"
        "           COPY CUSTOMER-AREA.\n"
        "       LINKAGE SECTION.\n"
        "           COPY REQUEST-AREA SUPPRESS.\n"
        "       PROCEDURE DIVISION.\n"
        "           COPY ERROR-HANDLER.\n",
        encoding="utf-8",
    )

    inclusions = builder.extract_copybook_inclusions(source)

    assert [item["copybook"] for item in inclusions] == [
        "CUSTOMER-AREA",
        "REQUEST-AREA",
        "ERROR-HANDLER",
    ]
    assert inclusions[0]["division"] == "DATA DIVISION"
    assert inclusions[0]["section"] == "WORKING-STORAGE SECTION"
    assert inclusions[1]["section"] == "LINKAGE SECTION"
    assert inclusions[2]["division"] == "PROCEDURE DIVISION"
    assert inclusions[2]["line"] == 9

def test_fixed_input_finds_shared_rekt_bundle(tmp_path: Path):
    run_fixed_input = _load_module("scripts/pipeline/run_fixed_input.py", "run_fixed_input")
    program_dir = tmp_path / "PDCBVC"
    bundle = tmp_path / "knowledge-base_rag"
    program_dir.mkdir()
    (bundle / "chunks").mkdir(parents=True)
    (bundle / "manifest.json").write_text("{}", encoding="utf-8")

    assert run_fixed_input.find_rekt_bundle(program_dir) == str(bundle.resolve())
