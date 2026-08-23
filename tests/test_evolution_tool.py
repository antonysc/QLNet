from __future__ import annotations

import importlib.util
import datetime as dt
import pathlib
import subprocess
import tempfile
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "tools" / "evolution.py"
SPEC = importlib.util.spec_from_file_location("evolution", MODULE_PATH)
assert SPEC and SPEC.loader
evolution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evolution)


class EvolutionToolTests(unittest.TestCase):
    def git(self, root: pathlib.Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout

    def repository(self) -> tuple[tempfile.TemporaryDirectory[str], pathlib.Path]:
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Test User")
        self.git(root, "config", "user.email", "test@example.invalid")
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        document = f"# Project Evolution\n\n<!-- evolution:reviewed={today}; owner=test -->\n\n"
        for heading in evolution.REQUIRED_HEADINGS:
            document += f"{heading}\n\n"
        (root / evolution.ROOT_DOCUMENT).write_text(document, encoding="utf-8")
        (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "-m", "docs: initialize fixture")
        return temporary, root

    def meaningful_commit(self, root: pathlib.Path, event_type: str = "done", extras: list[str] | None = None) -> str:
        (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
        self.git(root, "add", "app.py")
        message = [
            "feat: add behavior",
            "",
            f"Evolution-Type: {event_type}",
            "Evolution-Refs: auto",
            "Evolution-Expected: behavior is observable",
            "Evolution-Why: fixture requires behavior",
            "Evolution-Rollout: none — test fixture",
            "Evolution-Rollback: revert the commit",
            "Evolution-Next: test — verify — today",
            *(extras or []),
        ]
        message_file = root / "message.txt"
        message_file.write_text("\n".join(message), encoding="utf-8")
        self.git(root, "commit", "-F", str(message_file))
        return self.git(root, "rev-parse", "HEAD").strip()

    def test_valid_commit_generates_record_and_renders(self) -> None:
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        sha = self.meaningful_commit(root)
        created = evolution.generate(root, [sha])
        self.assertEqual([evolution.record_path(root, sha)], created)
        self.assertTrue(created[0].is_file())
        self.assertIn(sha[:7], (root / evolution.ROOT_DOCUMENT).read_text(encoding="utf-8"))
        self.assertEqual([], evolution.validate_commits(root, [sha]))

    def test_missing_trailer_is_rejected(self) -> None:
        trailers = {
            "evolution-type": "done",
            "evolution-refs": "auto",
        }
        errors = evolution.validate_trailers(trailers)
        self.assertTrue(any("evolution-expected" in error for error in errors))

    def test_fixed_requires_root_cause(self) -> None:
        trailers = {name: "value" for name in evolution.REQUIRED_TRAILERS}
        trailers["evolution-type"] = "fixed"
        errors = evolution.validate_trailers(trailers)
        self.assertIn("fixed commits require evolution-root-cause", errors)

    def test_decision_requires_choice(self) -> None:
        trailers = {name: "value" for name in evolution.REQUIRED_TRAILERS}
        trailers["evolution-type"] = "decision"
        errors = evolution.validate_trailers(trailers)
        self.assertIn("decision commits require evolution-choice", errors)

    def test_markdown_only_commit_is_exempt(self) -> None:
        self.assertFalse(evolution.meaningful(["README.md", "docs/guide.md"]))

    def test_generation_is_idempotent(self) -> None:
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        sha = self.meaningful_commit(root)
        evolution.generate(root, [sha])
        self.assertEqual([], evolution.generate(root, [sha]))

    def test_multiple_commits_are_generated_in_order(self) -> None:
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        first = self.meaningful_commit(root)
        (root / "app.py").write_text("print('changed')\n", encoding="utf-8")
        self.git(root, "add", "app.py")
        message = root / "message-two.txt"
        message.write_text(
            "fix: correct behavior\n\n"
            "Evolution-Type: fixed\n"
            "Evolution-Refs: R-002, CHG-004\n"
            "Evolution-Expected: corrected behavior is observable\n"
            "Evolution-Why: the first behavior was incorrect\n"
            "Evolution-Rollout: deploy after tests\n"
            "Evolution-Rollback: revert the commit\n"
            "Evolution-Next: test — verify — today\n"
            "Evolution-Root-Cause: incorrect fixture value\n",
            encoding="utf-8",
        )
        self.git(root, "commit", "-F", str(message))
        second = self.git(root, "rev-parse", "HEAD").strip()
        evolution.generate(root, [first, second])
        events = evolution.load_events(root)
        self.assertEqual([first, second], [event["sha"] for event in events])

    def test_altered_record_is_rejected(self) -> None:
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        sha = self.meaningful_commit(root)
        evolution.generate(root, [sha])
        path = evolution.record_path(root, sha)
        path.write_text(path.read_text(encoding="utf-8").replace("behavior is observable", "tampered"), encoding="utf-8")
        errors = evolution.validate_commits(root, [sha])
        self.assertTrue(any("altered or is stale" in error for error in errors))

    def test_render_check_detects_drift(self) -> None:
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        sha = self.meaningful_commit(root)
        evolution.generate(root, [sha])
        document = root / evolution.ROOT_DOCUMENT
        document.write_text(document.read_text(encoding="utf-8").replace("Automated current state", "Stale current state"), encoding="utf-8")
        with self.assertRaises(evolution.EvolutionError):
            evolution.render(root, check=True)

    def test_rollback_is_rendered_as_release_signal(self) -> None:
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        sha = self.meaningful_commit(root, event_type="rollback")
        evolution.generate(root, [sha])
        document = (root / evolution.ROOT_DOCUMENT).read_text(encoding="utf-8")
        self.assertIn(f"`{sha[:7]}` | `rollback`", document)

    def test_auto_commit_does_not_require_record(self) -> None:
        self.assertEqual([], evolution.validate_trailers({"evolution-auto": "true"}))


if __name__ == "__main__":
    unittest.main()

