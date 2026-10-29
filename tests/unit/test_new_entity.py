"""scripts/new_entity.py: names, refusals and where it writes. (The template smoke test adds a
real entity and runs the whole gate on it.)"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
_spec = importlib.util.spec_from_file_location("new_entity", ROOT / "scripts/new_entity.py")
new_entity = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(new_entity)


def test_names_follow_python_and_url_conventions():
    n = new_entity.names("VolunteerRole", None)
    assert (n["Plural"], n["snake_plural"], n["path"]) == (
        "VolunteerRoles",
        "volunteer_roles",
        "volunteer-roles",
    )
    assert new_entity.names("Opportunity", None)["Plural"] == "Opportunities"
    assert new_entity.names("Person", "People")["path"] == "people"


@pytest.mark.parametrize("bad", ["volunteer", "Volunteer-Role", "2Fast"])
def test_a_name_must_be_pascal_case(bad):
    with pytest.raises(SystemExit):
        new_entity.main([bad, "--root", str(ROOT)])


def test_it_never_overwrites_an_existing_entity(tmp_path, capsys):
    (tmp_path / "src/app/domain").mkdir(parents=True)
    (tmp_path / "src/app/domain/volunteers.py").write_text("# mine\n")
    assert new_entity.main(["Volunteer", "--root", str(tmp_path)]) == 1
    assert "nothing written" in capsys.readouterr().err
    assert (tmp_path / "src/app/domain/volunteers.py").read_text() == "# mine\n"


def test_the_mobile_registries_keep_their_markers():
    assert "// new_entity: routes" in (ROOT / new_entity.ROUTES).read_text()
    assert "// new_entity: features" in (ROOT / new_entity.FEATURES).read_text()
