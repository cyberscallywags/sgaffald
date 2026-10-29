"""The hook scripts: commit message prefixes and branch names."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
BASH = shutil.which("bash")
pytestmark = pytest.mark.skipif(BASH is None, reason="bash is not installed")


def run(script: str, arg: str) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603 - fixed script, test input
        [BASH, str(ROOT / "scripts" / script), arg], capture_output=True, text=True, check=False
    )


@pytest.mark.parametrize(
    "message",
    [
        "ADDED: mock sign-on in the API",
        "FIXED: reject items with an empty name\n\nWith a body.",
        "# a comment git adds\nDOCS: describe the brand kit",
        "Merge branch 'feature/x'",
        'Revert "ADDED: something"',
        "fixup! TASK: bump the hooks",
    ],
)
def test_commit_messages_with_a_prefix_pass(tmp_path, message):
    (msg := tmp_path / "COMMIT_EDITMSG").write_text(message)
    assert run("check_commit_msg.sh", str(msg)).returncode == 0


@pytest.mark.parametrize(
    "message", ["added a thing", "ADDED:no space", "FEATURE: not a prefix", "ADDED: ", ""]
)
def test_commit_messages_without_one_are_refused(tmp_path, message):
    (msg := tmp_path / "COMMIT_EDITMSG").write_text(message)
    result = run("check_commit_msg.sh", str(msg))
    assert result.returncode == 1
    assert "must start with ADDED:" in result.stderr


@pytest.mark.parametrize(
    "branch",
    ["feature/add-login", "refs/heads/docs/handbook-split", "dependabot/uv/python-abc123"],
)
def test_branch_names_with_a_kind_pass(branch, monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert run("check_branch_name.sh", branch).returncode == 0


@pytest.mark.parametrize("branch", ["main", "add-login", "feature/Add_Login"])
def test_other_branch_names_are_refused(branch, monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert run("check_branch_name.sh", branch).returncode == 1
