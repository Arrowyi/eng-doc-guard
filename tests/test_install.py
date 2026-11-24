#!/usr/bin/env python3
"""Tests for the eng-doc-guard cross-client installer.

Run with: python3 tests/test_install.py -v
"""

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parent
SCRIPTS = REPO / "scripts"
INSTALL_PY = SCRIPTS / "install.py"
INSTALL_SH = SCRIPTS / "install.sh"
TEMPLATE = SCRIPTS / "templates" / "eng-doc-guard.md"
sys.path.insert(0, str(SCRIPTS))

try:
    import install as installer_mod
except Exception:  # pragma: no cover - red phase before implementation
    installer_mod = None

ROOT_NAME = "eng-doc-guard"
COMMAND_NAME = "eng-doc-guard.md"
MANIFEST_NAME = ".managed-by-eng-doc-guard.json"
SENTINEL = "<!-- eng-doc-guard:command-managed -->"
PAYLOAD_FILES = ("SKILL.md", "references/examples.md")

TMP_ROOT = Path(os.environ.get("TMPDIR", "/tmp")) / "opencode"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def bundled_command_hash():
    return sha256_file(TEMPLATE)


def bundled_payload_hashes():
    return dict((rel, sha256_file(REPO / rel)) for rel in PAYLOAD_FILES)


def load_manifest(root):
    path = Path(root) / MANIFEST_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def sentinel_after_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1 < len(lines) and lines[index + 1].strip() == SENTINEL
    return False


def text_outside_seeded_blocks(text):
    """Drop each '### Seeded repo' block: from its heading to the next '###' or '##' heading."""
    kept = []
    in_seeded = False
    for line in text.splitlines():
        stripped = line.strip()
        if in_seeded:
            if stripped.startswith("##"):
                in_seeded = False
            else:
                continue
        if stripped.startswith("### Seeded repo"):
            in_seeded = True
            continue
        kept.append(line)
    return "\n".join(kept)


def slice_between(text, start_marker, end_marker, label):
    """Lines from the first line starting with start_marker up to (excluding) the
    first later line starting with end_marker; end_marker None runs to end of text.
    label names the file + slice in the error when a marker heading is missing."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith(start_marker):
            start = index
            break
    if start is None:
        raise ValueError("%s: no line starts with %r" % (label, start_marker))
    end = len(lines)
    if end_marker is not None:
        for index in range(start + 1, len(lines)):
            if lines[index].startswith(end_marker):
                end = index
                break
        else:
            raise ValueError("%s: no line after %r starts with %r" % (label, start_marker, end_marker))
    return "\n".join(lines[start:end])


def snapshot(root):
    """Map every path under root to a stable digest (dirs get a marker)."""
    root = Path(root)
    result = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel.split("/")[0] == "Library":
            # macOS Python writes ~/Library/Caches/com.apple.python; not installer output.
            continue
        if path.is_symlink():
            result[rel] = "SYMLINK:" + os.readlink(str(path))
        elif path.is_dir():
            result[rel] = "DIR"
        else:
            result[rel] = sha256_file(path)
    return result


class InstallerTestCase(unittest.TestCase):
    def setUp(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self._tmpdir = Path(tempfile.mkdtemp(prefix="edg-", dir=str(TMP_ROOT)))
        self.home = self._tmpdir / "home"
        self.home.mkdir()
        self.cwd = self._tmpdir / "cwd"
        self.cwd.mkdir()
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["USERPROFILE"] = str(self.home)
        self.env.pop("ENG_DOC_GUARD_SRC_DIR", None)

    def tearDown(self):
        shutil.rmtree(str(self._tmpdir), ignore_errors=True)

    # -- helpers -------------------------------------------------------
    def require_installer(self):
        self.assertIsNotNone(installer_mod, "scripts/install.py is not implemented yet")
        return installer_mod

    def run_installer(self, args, cwd=None, env=None):
        self.assertTrue(INSTALL_PY.is_file(), "scripts/install.py is missing")
        proc = subprocess.run(
            [sys.executable, str(INSTALL_PY)] + list(args),
            cwd=str(cwd or self.cwd),
            env=env or self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return proc

    def install_client(self, client, *extra, **kwargs):
        return self.run_installer(["--client", client] + list(extra), **kwargs)

    def skill_path(self, client):
        return {
            "opencode": self.home / ".config" / "opencode" / "skills" / ROOT_NAME,
            "claude": self.home / ".claude" / "skills" / ROOT_NAME,
            "cursor": self.home / ".cursor" / "skills" / ROOT_NAME,
            "codex": self.home / ".agents" / "skills" / ROOT_NAME,
        }[client]

    def command_path(self, client):
        return {
            "opencode": self.home / ".config" / "opencode" / "commands" / COMMAND_NAME,
            "claude": self.home / ".claude" / "commands" / COMMAND_NAME,
        }[client]

    def skills_parent(self, client):
        return self.skill_path(client).parent

    def assert_no_swap_artifacts(self, parent):
        leftovers = [p.name for p in Path(parent).iterdir() if ".eng-doc-guard." in p.name]
        self.assertEqual(leftovers, [])


class FreshInstallTests(InstallerTestCase):
    def test_fresh_install_opencode_payload_manifest_command(self):
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        root = self.skill_path("opencode")
        self.assertTrue((root / "SKILL.md").is_file())
        self.assertTrue((root / "references" / "examples.md").is_file())
        self.assertFalse((root / "acceptance-fixtures.md").exists())
        self.assertEqual((root / "SKILL.md").read_bytes(), (REPO / "SKILL.md").read_bytes())
        manifest = load_manifest(root)
        self.assertTrue(manifest["managed"])
        cmd = self.command_path("opencode")
        self.assertEqual(manifest["command_path"], str(cmd))
        self.assertEqual(manifest["command_sha256"], sha256_file(cmd))
        self.assertEqual(cmd.read_bytes(), TEMPLATE.read_bytes())
        self.assertTrue(sentinel_after_frontmatter(cmd.read_text(encoding="utf-8")))

    def test_fresh_install_all_four_clients_root_matrix(self):
        proc = self.install_client("all")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for client in ("opencode", "claude", "cursor", "codex"):
            root = self.skill_path(client)
            self.assertTrue((root / "SKILL.md").is_file(), client)
            self.assertIsNotNone(load_manifest(root), client)
        self.assertTrue(self.command_path("opencode").is_file())
        self.assertTrue(self.command_path("claude").is_file())

    def test_manifest_content_version_and_hashes(self):
        self.assertEqual(self.install_client("claude").returncode, 0)
        root = self.skill_path("claude")
        manifest = load_manifest(root)
        self.assertEqual(manifest["version"], "1.3.1")
        self.assertEqual(set(manifest["files_sha256"]), set(PAYLOAD_FILES))
        for rel, expected in bundled_payload_hashes().items():
            self.assertEqual(manifest["files_sha256"][rel], expected)
            self.assertEqual(sha256_file(root / rel), expected)
        cmd = self.command_path("claude")
        self.assertEqual(manifest["command_path"], str(cmd))
        self.assertEqual(manifest["command_sha256"], bundled_command_hash())

    def test_command_sentinel_sits_immediately_after_frontmatter(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(lines[0], "---")
        self.assertEqual(lines[2], "---")
        self.assertEqual(lines[3], SENTINEL)
        self.assertTrue(sentinel_after_frontmatter(text))
        self.assertLessEqual(len([line for line in lines[4:] if line.strip()]), 15)

    def test_platform_notice_windows_injectable(self):
        mod = self.require_installer()
        notice = mod.platform_notice("nt")
        self.assertIsNotNone(notice)
        self.assertIn("os.replace", notice)
        self.assertIn("age-based", notice)
        self.assertIsNone(mod.platform_notice("posix"))


class LockstepTests(InstallerTestCase):
    def test_no_arg_lockstep_upgrades_existing_roots(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        self.assertEqual(self.install_client("claude").returncode, 0)
        proc = self.run_installer([])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for client in ("opencode", "claude"):
            self.assertEqual(
                (self.skill_path(client) / "SKILL.md").read_bytes(),
                (REPO / "SKILL.md").read_bytes(),
            )
            self.assertTrue(self.command_path(client).is_file())

    def test_no_arg_no_root_usage_exit_2_zero_writes(self):
        before = snapshot(self.home)
        proc = self.run_installer([])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--client", proc.stdout + proc.stderr)
        self.assertEqual(snapshot(self.home), before)


class PreflightTests(InstallerTestCase):
    def test_modified_skill_file_aborts_cross_root_zero_writes(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        self.assertEqual(self.install_client("claude").returncode, 0)
        dirty = self.skill_path("opencode") / "SKILL.md"
        dirty.write_text(dirty.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
        before = snapshot(self.home)
        clean_before = sha256_file(self.skill_path("claude") / "SKILL.md")
        proc = self.run_installer([])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(sha256_file(self.skill_path("claude") / "SKILL.md"), clean_before)

    def test_modified_command_file_aborts(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        cmd = self.command_path("opencode")
        cmd.write_text(cmd.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
        before = snapshot(self.home)
        proc = self.run_installer(["--client", "opencode"])
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(snapshot(self.home), before)

    def test_missing_managed_file_is_repaired(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        (self.skill_path("opencode") / "SKILL.md").unlink()
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            (self.skill_path("opencode") / "SKILL.md").read_bytes(),
            (REPO / "SKILL.md").read_bytes(),
        )

    def test_unmanaged_root_aborts_even_with_force(self):
        root = self.skill_path("opencode")
        root.mkdir(parents=True)
        (root / "foreign.txt").write_text("mine", encoding="utf-8")
        proc = self.install_client("opencode", "--force")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual((root / "foreign.txt").read_text(encoding="utf-8"), "mine")
        self.assertFalse((root / MANIFEST_NAME).exists())

    def test_symlink_root_aborts_even_with_force(self):
        target = self._tmpdir / "elsewhere"
        target.mkdir()
        (target / "foreign.txt").write_text("mine", encoding="utf-8")
        root = self.skill_path("opencode")
        root.parent.mkdir(parents=True)
        os.symlink(str(target), str(root))
        proc = self.install_client("opencode", "--force")
        self.assertEqual(proc.returncode, 1)
        self.assertTrue(root.is_symlink())
        self.assertEqual((target / "foreign.txt").read_text(encoding="utf-8"), "mine")

    def test_force_overrides_modified_managed_file(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        (self.skill_path("opencode") / "SKILL.md").write_text("local edit", encoding="utf-8")
        proc = self.install_client("opencode", "--force")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            (self.skill_path("opencode") / "SKILL.md").read_bytes(),
            (REPO / "SKILL.md").read_bytes(),
        )

    def test_foreign_sentinel_less_command_aborts_even_with_force(self):
        cmd = self.command_path("opencode")
        cmd.parent.mkdir(parents=True)
        cmd.write_text("---\ndescription: foreign\n---\nnot ours\n", encoding="utf-8")
        for extra in ([], ["--force"]):
            proc = self.run_installer(["--client", "opencode"] + extra)
            self.assertEqual(proc.returncode, 1, extra)
            self.assertEqual(cmd.read_text(encoding="utf-8"), "---\ndescription: foreign\n---\nnot ours\n")

    def test_sentinel_command_hash_mismatch_without_root_aborts(self):
        cmd = self.command_path("opencode")
        cmd.parent.mkdir(parents=True)
        cmd.write_text("---\ndescription: x\n---\n%s\nforeign body\n" % SENTINEL, encoding="utf-8")
        for extra in ([], ["--force"]):
            proc = self.run_installer(["--client", "opencode"] + extra)
            self.assertEqual(proc.returncode, 1, extra)
            self.assertIn("foreign body", cmd.read_text(encoding="utf-8"))

    def test_interrupted_upgrade_converges_without_force(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        manifest = load_manifest(root)
        manifest["command_sha256"] = "0" * 64
        (root / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(load_manifest(root)["command_sha256"], bundled_command_hash())

    def test_interrupted_fresh_install_converges_without_force(self):
        cmd = self.command_path("opencode")
        cmd.parent.mkdir(parents=True)
        cmd.write_bytes(TEMPLATE.read_bytes())
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.skill_path("opencode") / MANIFEST_NAME).is_file())


class RecoveryTests(InstallerTestCase):
    def make_installer(self, **kwargs):
        mod = self.require_installer()
        return mod.Installer(home=self.home, cwd=self.cwd, **kwargs)

    def test_recovery_restores_bak_when_root_missing(self):
        skills = self.skills_parent("opencode")
        bak = skills / ".eng-doc-guard.bak"
        bak.mkdir(parents=True)
        (bak / "proof.txt").write_text("restored", encoding="utf-8")
        actions = self.make_installer().recover(apply=True)
        root = self.skill_path("opencode")
        self.assertTrue((root / "proof.txt").is_file())
        self.assertFalse(bak.exists())
        self.assertTrue(any("restore" in a for a in actions))

    def test_recovery_deletes_stale_bak_when_root_exists(self):
        root = self.skill_path("opencode")
        root.mkdir(parents=True)
        (root / "keep.txt").write_text("keep", encoding="utf-8")
        bak = self.skills_parent("opencode") / ".eng-doc-guard.bak"
        bak.mkdir()
        self.make_installer().recover(apply=True)
        self.assertTrue((root / "keep.txt").is_file())
        self.assertFalse(bak.exists())

    def test_recovery_removes_staging_tmp_dir(self):
        parent = self.skills_parent("opencode")
        tmp = parent / ".eng-doc-guard.tmp.999"
        tmp.mkdir(parents=True)
        (tmp / "half.txt").write_text("x", encoding="utf-8")
        self.make_installer().recover(apply=True)
        self.assertFalse(tmp.exists())

    def test_recovery_removes_command_tmp(self):
        parent = self.command_path("opencode").parent
        parent.mkdir(parents=True)
        tmp = parent / (COMMAND_NAME + ".tmp.999")
        tmp.write_text("half", encoding="utf-8")
        self.make_installer().recover(apply=True)
        self.assertFalse(tmp.exists())


class LockTests(InstallerTestCase):
    def lock_path(self):
        return self.home / ".eng-doc-guard-install.lock"

    def test_lock_held_exit_4_other_lock_survives(self):
        content = "%d %.6f\n" % (os.getpid(), time.time())
        self.lock_path().write_text(content, encoding="utf-8")
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 4, proc.stderr)
        self.assertEqual(self.lock_path().read_text(encoding="utf-8"), content)

    def test_stale_lock_dead_pid_is_broken(self):
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait()
        self.lock_path().write_text("%d %.6f\n" % (child.pid, time.time()), encoding="utf-8")
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(self.lock_path().exists())
        self.assertEqual([p for p in self.home.iterdir() if p.name.startswith(".eng-doc-guard-install.lock.stale")], [])

    def test_stale_lock_aged_live_pid_is_broken(self):
        self.lock_path().write_text("%d %.6f\n" % (os.getpid(), time.time() - 1000), encoding="utf-8")
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(self.lock_path().exists())

    def test_lock_acquired_before_recovery(self):
        self.lock_path().write_text("%d %.6f\n" % (os.getpid(), time.time()), encoding="utf-8")
        parent = self.skills_parent("opencode")
        bak = parent / ".eng-doc-guard.bak"
        bak.mkdir(parents=True)
        tmp = parent / ".eng-doc-guard.tmp.999"
        tmp.mkdir()
        proc = self.install_client("opencode")
        self.assertEqual(proc.returncode, 4, proc.stderr)
        self.assertTrue(bak.exists())
        self.assertTrue(tmp.exists())

    def test_lock_released_after_success(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        self.assertFalse(self.lock_path().exists())


class AtomicityTests(InstallerTestCase):
    def make_installer(self, **kwargs):
        mod = self.require_installer()
        return mod.Installer(home=self.home, cwd=self.cwd, **kwargs)

    def entry(self, client="opencode"):
        mod = self.require_installer()
        return mod.global_entries(self.home)[client]

    def test_atomic_swap_leaves_no_bak_or_tmp(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        self.assert_no_swap_artifacts(self.skills_parent("opencode"))
        self.assertEqual([p.name for p in self.command_path("opencode").parent.iterdir() if p.name.endswith(".tmp") or ".tmp." in p.name], [])

    def test_staging_failure_leaves_old_root_tmp_removed_exit_1(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        (root / "SKILL.md").write_text("OLD", encoding="utf-8")
        inst = self.make_installer(force=True)

        def broken_copy(src, dst):
            raise OSError("simulated staging failure")

        inst._copy = broken_copy
        code = inst.install([self.entry()])
        self.assertEqual(code, 1)
        self.assertEqual((root / "SKILL.md").read_text(encoding="utf-8"), "OLD")
        self.assert_no_swap_artifacts(self.skills_parent("opencode"))

    def test_staging_failure_fresh_install_then_converges(self):
        cmd = self.command_path("opencode")
        cmd.parent.mkdir(parents=True)
        cmd.write_bytes(TEMPLATE.read_bytes())
        inst = self.make_installer()

        def broken_copy(src, dst):
            raise OSError("simulated staging failure")

        inst._copy = broken_copy
        self.assertEqual(inst.install([self.entry()]), 1)
        self.assertFalse(self.skill_path("opencode").exists())
        inst._copy = shutil.copy2
        self.assertEqual(inst.install([self.entry()]), 0)
        self.assertTrue((self.skill_path("opencode") / MANIFEST_NAME).is_file())

    def test_command_replace_failure_leaves_root_intact(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        (root / "SKILL.md").write_text("OLD", encoding="utf-8")
        inst = self.make_installer(force=True)

        def broken_replace(src, dst):
            raise OSError("simulated command replace failure")

        inst._replace = broken_replace
        self.assertEqual(inst.install([self.entry()]), 1)
        self.assertEqual((root / "SKILL.md").read_text(encoding="utf-8"), "OLD")

    def test_aside_move_failure_leaves_root_intact(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        (root / "SKILL.md").write_text("OLD", encoding="utf-8")
        inst = self.make_installer(force=True)
        bak = self.skills_parent("opencode") / ".eng-doc-guard.bak"
        real_rename = os.rename

        def failing_rename(src, dst):
            if os.path.abspath(str(dst)) == os.path.abspath(str(bak)):
                raise OSError("simulated aside failure")
            return real_rename(src, dst)

        inst._rename = failing_rename
        self.assertEqual(inst.install([self.entry()]), 1)
        self.assertEqual((root / "SKILL.md").read_text(encoding="utf-8"), "OLD")
        self.assertFalse(bak.exists())

    def test_swap_failure_after_aside_restores_root(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        (root / "SKILL.md").write_text("OLD", encoding="utf-8")
        inst = self.make_installer(force=True)
        real_rename = os.rename
        tmp_marker = ".eng-doc-guard.tmp."

        def failing_rename(src, dst):
            if os.path.basename(str(src)).startswith(tmp_marker):
                raise OSError("simulated swap failure")
            return real_rename(src, dst)

        inst._rename = failing_rename
        self.assertEqual(inst.install([self.entry()]), 1)
        self.assertEqual((root / "SKILL.md").read_text(encoding="utf-8"), "OLD")
        self.assertFalse((self.skills_parent("opencode") / ".eng-doc-guard.bak").exists())
        self.assert_no_swap_artifacts(self.skills_parent("opencode"))


class UninstallTests(InstallerTestCase):
    def test_uninstall_removes_managed_roots_and_unmodified_commands(self):
        self.assertEqual(self.install_client("all").returncode, 0)
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for client in ("opencode", "claude", "cursor", "codex"):
            self.assertFalse(self.skill_path(client).exists(), client)
        self.assertFalse(self.command_path("opencode").exists())
        self.assertFalse(self.command_path("claude").exists())

    def test_uninstall_keeps_user_modified_command(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        cmd = self.command_path("opencode")
        cmd.write_text(cmd.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(cmd.exists())
        self.assertFalse(self.skill_path("opencode").exists())

    def test_uninstall_leaves_unmanaged_dir_and_symlink_untouched(self):
        unmanaged = self.skill_path("opencode")
        unmanaged.mkdir(parents=True)
        (unmanaged / "foreign.txt").write_text("mine", encoding="utf-8")
        target = self._tmpdir / "elsewhere"
        target.mkdir()
        (target / "foreign.txt").write_text("mine", encoding="utf-8")
        linked = self.skill_path("claude")
        linked.parent.mkdir(parents=True)
        os.symlink(str(target), str(linked))
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((unmanaged / "foreign.txt").is_file())
        self.assertTrue(linked.is_symlink())
        self.assertTrue((target / "foreign.txt").is_file())

    def test_uninstall_ignores_tampered_manifest_command_path(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        decoy = self.home / "decoy-command.md"
        decoy.write_bytes(TEMPLATE.read_bytes())
        manifest = load_manifest(root)
        real_cmd = manifest["command_path"]
        manifest["command_path"] = str(decoy)
        (root / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(decoy.exists())
        self.assertFalse(Path(real_cmd).exists())
        self.assertIn("command_path", proc.stdout + proc.stderr)

    def test_uninstall_removes_orphan_bundled_equal_command(self):
        cmd = self.command_path("opencode")
        cmd.parent.mkdir(parents=True)
        cmd.write_bytes(TEMPLATE.read_bytes())
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(cmd.exists())

    def test_uninstall_keeps_orphan_command_with_different_hash(self):
        cmd = self.command_path("opencode")
        cmd.parent.mkdir(parents=True)
        cmd.write_text("---\ndescription: x\n---\n%s\nforeign\n" % SENTINEL, encoding="utf-8")
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(cmd.exists())
        self.assertIn("kept", proc.stdout + proc.stderr)

    def test_uninstall_stale_manifest_with_bundled_equal_command(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        manifest = load_manifest(root)
        manifest["command_sha256"] = "0" * 64
        (root / MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(self.command_path("opencode").exists())
        self.assertFalse(root.exists())

    def test_uninstall_removes_marker_owned_root_with_modified_files(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        (root / "SKILL.md").write_text("local edit", encoding="utf-8")
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(root.exists())
        output = proc.stdout + proc.stderr
        self.assertIn("SKILL.md", output)
        self.assertIn("warning", output.lower())

    def test_uninstall_nothing_installed_exit_0(self):
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing installed", (proc.stdout + proc.stderr).lower())

    def test_uninstall_cleans_leftover_bak_and_tmp_then_removes(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        parent = self.skills_parent("opencode")
        os.rename(str(self.skill_path("opencode")), str(parent / ".eng-doc-guard.bak"))
        tmp = parent / ".eng-doc-guard.tmp.999"
        tmp.mkdir()
        proc = self.run_installer(["--uninstall"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse(self.skill_path("opencode").exists())
        self.assertFalse((parent / ".eng-doc-guard.bak").exists())
        self.assertFalse(tmp.exists())

    def make_installer(self):
        mod = self.require_installer()
        out, err = io.StringIO(), io.StringIO()
        return mod.Installer(home=self.home, cwd=self.cwd, out=out, err=err), out, err

    def test_uninstall_command_unlink_failure_exits_1(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        cmd = self.command_path("opencode")
        inst, out, err = self.make_installer()

        def broken_unlink(path):
            raise OSError("simulated unlink failure")

        inst._unlink = broken_unlink
        self.assertEqual(inst.uninstall(), 1)
        self.assertTrue(cmd.exists())
        self.assertIn(str(cmd), out.getvalue() + err.getvalue())

    def test_uninstall_root_rmtree_failure_exits_1(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        root = self.skill_path("opencode")
        inst, out, err = self.make_installer()

        def broken_rmtree(path):
            raise OSError("simulated rmtree failure")

        inst._rmtree = broken_rmtree
        self.assertEqual(inst.uninstall(), 1)
        self.assertTrue(root.exists())
        self.assertIn(str(root), out.getvalue() + err.getvalue())

    def test_uninstall_dry_run_reports_only(self):
        self.assertEqual(self.install_client("opencode").returncode, 0)
        before = snapshot(self.home)
        proc = self.run_installer(["--uninstall", "--dry-run"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(snapshot(self.home), before)
        self.assertIn("would", (proc.stdout + proc.stderr).lower())


class DryRunTests(InstallerTestCase):
    def test_dry_run_zero_writes(self):
        before = snapshot(self.home)
        proc = self.install_client("opencode", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(snapshot(self.home), before)
        self.assertFalse((self.home / ".eng-doc-guard-install.lock").exists())

    def test_dry_run_with_leftovers_reports_and_writes_nothing(self):
        parent = self.skills_parent("opencode")
        tmp = parent / ".eng-doc-guard.tmp.999"
        tmp.mkdir(parents=True)
        before = snapshot(self.home)
        proc = self.install_client("opencode", "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(snapshot(self.home), before)
        self.assertIn("would", (proc.stdout + proc.stderr).lower())
        self.assertFalse((self.home / ".eng-doc-guard-install.lock").exists())


class ProjectTests(InstallerTestCase):
    def test_project_mode_per_dir_and_excluded_from_lockstep(self):
        proc = self.run_installer(["--client", "codex", "--project"], cwd=self.cwd)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        project_root = self.cwd / ".agents" / "skills" / ROOT_NAME
        self.assertTrue(project_root.is_dir())
        self.assertIsNotNone(load_manifest(project_root))
        self.assertFalse(self.skill_path("codex").exists())
        proc = self.run_installer([])
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(project_root.is_dir())


class NoticeTests(InstallerTestCase):
    def test_overlap_notice_with_two_roots(self):
        proc = self.install_client("all")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        output = proc.stdout
        self.assertIn("global clients", output)
        self.assertIn("identical", output)


class ShellTests(InstallerTestCase):
    def bash(self):
        for candidate in ("/bin/bash", shutil.which("bash")):
            if candidate and Path(candidate).is_file():
                return candidate
        self.skipTest("bash not available")

    def test_install_sh_local_src_dry_run_passthrough(self):
        self.assertTrue(INSTALL_SH.is_file(), "scripts/install.sh is missing")
        env = self.env.copy()
        env["ENG_DOC_GUARD_SRC_DIR"] = str(REPO)
        before = snapshot(self.home)
        proc = subprocess.run(
            [self.bash(), str(INSTALL_SH), "--client", "opencode", "--dry-run"],
            cwd=str(self.cwd), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(snapshot(self.home), before)

    def test_install_sh_python_gate_missing(self):
        self.assertTrue(INSTALL_SH.is_file())
        empty = self._tmpdir / "empty-path"
        empty.mkdir()
        env = self.env.copy()
        env["ENG_DOC_GUARD_SRC_DIR"] = str(REPO)
        env["PATH"] = str(empty)
        proc = subprocess.run(
            [self.bash(), str(INSTALL_SH), "--client", "opencode", "--dry-run"],
            cwd=str(self.cwd), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("python3", (proc.stdout + proc.stderr).lower())

    def test_install_sh_python_gate_old_version(self):
        self.assertTrue(INSTALL_SH.is_file())
        shim_dir = self._tmpdir / "shim"
        shim_dir.mkdir()
        shim = shim_dir / "python3"
        shim.write_text(
            "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'Python 3.8.10'; exit 0; fi\nexit 1\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
        env = self.env.copy()
        env["ENG_DOC_GUARD_SRC_DIR"] = str(REPO)
        env["PATH"] = str(shim_dir) + os.pathsep + "/usr/bin:/bin"
        proc = subprocess.run(
            [self.bash(), str(INSTALL_SH), "--client", "opencode", "--dry-run"],
            cwd=str(self.cwd), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("3.9", (proc.stdout + proc.stderr))

    def test_install_sh_remote_mode_local_fixture_end_to_end(self):
        git = shutil.which("git")
        if not git:
            self.skipTest("git not available")
        self.assertTrue(INSTALL_SH.is_file())
        fixture = self._tmpdir / "remote-fixture"
        fixture.mkdir()
        shutil.copy2(str(REPO / "SKILL.md"), str(fixture / "SKILL.md"))
        shutil.copytree(str(REPO / "references"), str(fixture / "references"))
        shutil.copytree(str(REPO / "scripts"), str(fixture / "scripts"))
        quote = ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid"]
        subprocess.run([git, "-C", str(fixture), "init", "-q"], check=True)
        subprocess.run([git, "-C", str(fixture), "symbolic-ref", "HEAD", "refs/heads/main"], check=True)
        subprocess.run([git, "-C", str(fixture), "add", "-A"], check=True)
        subprocess.run([git, "-C", str(fixture)] + quote + ["commit", "-q", "-m", "fixture"], check=True)
        env = self.env.copy()
        env.pop("ENG_DOC_GUARD_SRC_DIR", None)
        env["ENG_DOC_GUARD_REMOTE"] = str(fixture)
        env["ENG_DOC_GUARD_REF"] = "main"
        proc = subprocess.run(
            [self.bash(), str(INSTALL_SH), "--client", "opencode"],
            cwd=str(self.cwd), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIsNotNone(load_manifest(self.skill_path("opencode")))

    def test_install_sh_default_remote_is_canonical_url(self):
        self.assertTrue(INSTALL_SH.is_file())
        text = INSTALL_SH.read_text(encoding="utf-8")
        self.assertIn(
            'ENG_DOC_GUARD_REMOTE="${ENG_DOC_GUARD_REMOTE:-https://github.com/Arrowyi/eng-doc-guard.git}"',
            text,
        )
        self.assertNotIn("__SET_BEFORE_PUBLISH__", text)


class RepositoryTests(unittest.TestCase):
    def test_repo_portability_scan(self):
        forbidden = ["/Us" + "ers/", "bd" + "gong", "WorkSpace" + "GitRepositories"]
        targets = [REPO / "SKILL.md", REPO / "README.md", REPO / "AGENTS.md", TESTS_DIR / "acceptance-fixtures.md"]
        for base in (REPO / "references", REPO / "scripts", REPO / "docs"):
            if base.is_dir():
                targets.extend(sorted(base.rglob("*")))
        scanned = 0
        for path in targets:
            if not path.is_file() or path.suffix not in (".md", ".py", ".sh", ""):
                continue
            if "__pycache__" in path.parts or (path.parent == TESTS_DIR and path.suffix == ".py"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for literal in forbidden:
                self.assertNotIn(literal, text, "%s leaks %r" % (path, literal))
            scanned += 1
        self.assertGreaterEqual(scanned, 2)

    def test_acceptance_fixture_completeness(self):
        text = (TESTS_DIR / "acceptance-fixtures.md").read_text(encoding="utf-8")
        scenarios = ("## QS1", "## QS2", "## QS3", "## QS5", "## QS6", "## QS7")
        for scenario in scenarios:
            self.assertIn(scenario, text)
        for block in ("### Scenario", "### Seeded repo", "### Expected response", "### Pass criteria"):
            self.assertEqual(text.count(block), len(scenarios), block)
        pinned = [
            "live_refs == 0",
            "LIMIT 3",
            "--old is deprecated",
            "宏观架构边界未变",
            "✅ 当前顶层文档边界清晰、与代码一致，无需新增或修改。",
            "只改",
            "看 N",
            "[待用户确认]",
        ]
        for literal in pinned:
            self.assertIn(literal, text)

    def test_no_dogmatic_numeric_caps_in_shipped_payload(self):
        banned_caps = (
            r"<\s*200\s+lines",
            r"≤\s*30",
            r"≤\s*10",
            r"≤\s*5\s+source",
            r"≥\s*3[\s-]+decoupled",
            r"3[–-]5\s+(?:representative\s+)?examples",
            r"≤\s*8\s+items",
        )

        def assert_no_caps(path, text):
            for pattern in banned_caps:
                matches = re.findall(pattern, text)
                self.assertEqual(matches, [], "%s matches banned cap %r" % (path, pattern))

        for rel in ("SKILL.md", "references/examples.md"):
            assert_no_caps(rel, (REPO / rel).read_text(encoding="utf-8"))

        fixtures = TESTS_DIR / "acceptance-fixtures.md"
        remainder = text_outside_seeded_blocks(fixtures.read_text(encoding="utf-8"))
        self.assertTrue(remainder.strip(), "scanned remainder of acceptance-fixtures.md is empty")
        self.assertIn("### Expected response", remainder, "remainder lost Expected response headings")
        self.assertIn("### Pass criteria", remainder, "remainder lost Pass criteria headings")
        assert_no_caps(str(fixtures), remainder)

    def test_repo_governed_docs_carry_managed_sentinel(self):
        sentinel = "<!-- eng-doc-guard:managed -->"
        for rel in ("README.md", "AGENTS.md", "docs/design-rationale.md"):
            path = REPO / rel
            self.assertTrue(path.is_file(), "%s is missing" % rel)
            self.assertGreater(path.stat().st_size, 0, "%s is empty" % rel)
            first_line = path.read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(first_line, sentinel, "%s line 1 is not the managed sentinel" % rel)

    def test_iron_law_4_orthogonality_and_no_inferability_bleed(self):
        # Check 1 — SKILL.md slices: bare "- directory trees;" stays in the Iron Law #2
        # block only; the Iron Law #4 block and the Architecture Map lens block carry
        # the non-circular wording and no Iron Law #2 inferability wording.
        skill = (REPO / "SKILL.md").read_text(encoding="utf-8")
        il2 = slice_between(skill, "**Iron Law #2:", "**Iron Law #3:", "SKILL.md Iron Law #2 block")
        il4 = slice_between(skill, "**Iron Law #4:", "## 4.", "SKILL.md Iron Law #4 block")
        lens = slice_between(
            skill, "### 3. Architecture Map", "### 4. Design Rationale", "SKILL.md Architecture Map lens block"
        )
        self.assertIn(
            "- directory trees;", il2,
            "SKILL.md Iron Law #2 block lost the bare '- directory trees;' eviction",
        )
        self.assertNotIn(
            "- directory trees;", il4,
            "SKILL.md Iron Law #4 block must not keep the bare '- directory trees;' blanket tree ban",
        )
        self.assertIn(
            "- file-level or deep directory trees", il4,
            "SKILL.md Iron Law #4 block must use the '- file-level or deep directory trees' non-circular wording",
        )
        for phrase in ("code-identifiable", "a file search answers"):
            self.assertNotIn(
                phrase, il4,
                "SKILL.md Iron Law #4 block bleeds the Iron Law #2 inferability phrase %r" % phrase,
            )
            self.assertNotIn(
                phrase, lens,
                "SKILL.md Architecture Map lens block bleeds the Iron Law #2 inferability phrase %r" % phrase,
            )

        # Check 2 — references/examples.md A6 slice (to EOF): no inferability wording.
        a6 = slice_between(
            (REPO / "references" / "examples.md").read_text(encoding="utf-8"),
            "### A6.", None, "references/examples.md A6 slice",
        )
        for phrase in ("a file search answers", "not rediscoverable in one step", "code-identifiable"):
            self.assertNotIn(
                phrase, a6,
                "references/examples.md A6 slice contains the Iron Law #2 inferability phrase %r" % phrase,
            )

        # Check 3 — acceptance-fixtures.md QS2 slice: no Iron Law #4 line cites the phrases.
        fixtures = (TESTS_DIR / "acceptance-fixtures.md").read_text(encoding="utf-8")
        qs2 = slice_between(fixtures, "## QS2", "## QS3", "acceptance-fixtures.md QS2 slice")
        for line in qs2.splitlines():
            if "Iron Law #4" not in line:
                continue
            for phrase in ("a file search answers", "code-identifiable"):
                self.assertNotIn(
                    phrase, line,
                    "acceptance-fixtures.md QS2 slice has an Iron Law #4 line citing %r: %s" % (phrase, line),
                )

        # Check 4 — docs/design-rationale.md: zero skill meta-jargon.
        rationale = (REPO / "docs" / "design-rationale.md").read_text(encoding="utf-8")
        self.assertNotIn(
            "Iron Law", rationale,
            "docs/design-rationale.md contains the skill meta-jargon 'Iron Law'",
        )


if __name__ == "__main__":
    unittest.main()
