"""app.typegen: the mobile app's TypeScript types are generated from the Pydantic models."""

from pathlib import Path

from app import typegen
from app.docgen import documented_models

ROOT = Path(__file__).parents[2]


def test_the_mobile_types_are_current():
    assert (ROOT / typegen.OUT).read_text() == typegen.render(), "run `uv run task types`"


def test_every_model_becomes_an_interface():
    text = typegen.render()
    for cls in documented_models():
        assert f"export interface {cls.__name__} {{" in text


def test_only_fields_that_default_to_null_are_optional():
    text = typegen.render()
    assert "  created_by?: string | null;" in text  # Item: None by default
    assert "  pages: ContentPage[];" in text  # Site: [] by default, always present
    assert "  id: string;" in text  # Item: a default factory, always present


def test_schema_shapes_map_to_typescript():
    assert typegen.ts_type({"enum": ["off", "mock"]}) == "'off' | 'mock'"
    assert typegen.ts_type({"anyOf": [{"type": "string"}, {"type": "null"}]}) == "string | null"
    assert typegen.ts_type({"type": "array", "items": {"$ref": "#/$defs/Member"}}) == "Member[]"
    union = {"type": "array", "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]}}
    assert typegen.ts_type(union) == "(string | number)[]"
    assert typegen.ts_type({"type": "object"}) == "Record<string, unknown>"


def test_check_reports_a_stale_file(tmp_path, capsys):
    out = tmp_path / typegen.OUT
    out.parent.mkdir(parents=True)
    out.write_text("stale")
    assert typegen.main(["--check", "--root", str(tmp_path)]) == 1
    assert typegen.main(["--root", str(tmp_path)]) == 0
    assert typegen.main(["--check", "--root", str(tmp_path)]) == 0
