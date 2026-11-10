import tempfile
import unittest
from pathlib import Path

from scripts import cleanup_audit


class CleanupAuditTests(unittest.TestCase):
    def test_path_stats_counts_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("abc", encoding="utf-8")
            (root / "sub").mkdir()
            (root / "sub" / "b.txt").write_text("de", encoding="utf-8")
            stats = cleanup_audit.path_stats(root)
            self.assertTrue(stats["exists"])
            self.assertEqual(stats["files"], 2)
            self.assertEqual(stats["size_bytes"], 5)

    def test_candidate_paths_include_cli_config(self):
        items = cleanup_audit.candidate_paths(Path("/tmp/fake-home"))
        categories = {item["category"] for item in items}
        self.assertIn("cli_config", categories)
        self.assertTrue(any(item["path"].endswith(".claude.json") for item in items))

    def test_audit_marks_config_as_never_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cli = home / ".claude"
            cli.mkdir()
            (cli / "settings.json").write_text("{}", encoding="utf-8")
            report = cleanup_audit.audit(home)
            row = next(item for item in report["rows"] if item["path"].endswith("settings.json"))
            self.assertTrue(row["never_delete"])
            self.assertTrue(row["exists"])

    def test_audit_marks_transcripts_as_conversation(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            projects = home / ".claude" / "projects" / "proj"
            projects.mkdir(parents=True)
            (projects / "session.jsonl").write_text("{}\n", encoding="utf-8")
            report = cleanup_audit.audit(home)
            row = next(item for item in report["rows"] if item["category"] == "conversation")
            self.assertTrue(row["never_delete"])
            self.assertTrue(row["exists"])

    def test_compaction_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            projects = Path(tmp) / ".claude" / "projects" / "proj"
            projects.mkdir(parents=True)
            path = projects / "session.jsonl"
            path.write_text(
                '{"type":"compact_boundary"}\n'
                '{"isCompactSummary":true}\n'
                '{"type":"user","message":{"role":"user"}}\n'
                '{"type":"assistant"}\n',
                encoding="utf-8",
            )
            stats = cleanup_audit.compaction_stats(Path(tmp) / ".claude" / "projects")
            self.assertEqual(stats["files"], 1)
            self.assertEqual(stats["lines"], 4)
            self.assertEqual(stats["compact_boundaries"], 1)
            self.assertEqual(stats["compact_summaries"], 1)

    def test_human_size(self):
        self.assertEqual(cleanup_audit.human_size(0), "0.0 B")
        self.assertIn("KB", cleanup_audit.human_size(2048))


if __name__ == "__main__":
    unittest.main()
