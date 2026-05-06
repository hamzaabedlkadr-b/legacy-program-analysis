from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
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
    )

    metadata = records[0]["metadata"]
    assert metadata["source_system"] == "mapa_hamza"
    assert metadata["chunk_type"] == "architecture.call"
    assert metadata["source_chunk_type"] == "architecture.call"
    assert metadata["coverage_dimension"] == "static_inventory"
    assert metadata["entity_key"] == "PDCBVC|PD1VOCI|LINK"


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


def test_fixed_input_finds_shared_rekt_bundle(tmp_path: Path):
    run_fixed_input = _load_module("scripts/pipeline/run_fixed_input.py", "run_fixed_input")
    program_dir = tmp_path / "PDCBVC"
    bundle = tmp_path / "knowledge-base_rag"
    program_dir.mkdir()
    (bundle / "chunks").mkdir(parents=True)
    (bundle / "manifest.json").write_text("{}", encoding="utf-8")

    assert run_fixed_input.find_rekt_bundle(program_dir) == str(bundle.resolve())
