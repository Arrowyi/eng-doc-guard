#!/usr/bin/env python3
"""Install or uninstall the eng-doc-guard skill across agent clients."""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

MANIFEST_NAME = ".managed-by-eng-doc-guard.json"
ROOT_NAME = "eng-doc-guard"
COMMAND_NAME = "eng-doc-guard.md"
COMMAND_SENTINEL = "<!-- eng-doc-guard:command-managed -->"
VERSION = "1.2.0"
LOCK_NAME = ".eng-doc-guard-install.lock"
BAK_NAME = ".eng-doc-guard.bak"
TMP_PREFIX = ".eng-doc-guard.tmp."
COMMAND_TMP_SUFFIX = ".tmp."
STALE_LOCK_AGE = 300.0
LOCK_ATTEMPTS = 5
PAYLOAD_FILES = ("SKILL.md", "references/examples.md")
CLIENTS = ("opencode", "claude", "cursor", "codex")

SCRIPTS_DIR = Path(__file__).resolve().parent
PAYLOAD_DIR = SCRIPTS_DIR.parent
COMMAND_TEMPLATE = SCRIPTS_DIR / "templates" / COMMAND_NAME


class InstallError(Exception):
    pass


class LockError(Exception):
    pass


class PreflightError(Exception):
    def __init__(self, problems):
        Exception.__init__(self, "preflight failed")
        self.problems = problems


@dataclass(frozen=True)
class Entry:
    client: str
    skill: Path
    command: object
    scope: str


def global_entries(home):
    home = Path(home)
    return {
        "opencode": Entry(
            "opencode",
            home / ".config" / "opencode" / "skills" / ROOT_NAME,
            home / ".config" / "opencode" / "commands" / COMMAND_NAME,
            "global",
        ),
        "claude": Entry(
            "claude",
            home / ".claude" / "skills" / ROOT_NAME,
            home / ".claude" / "commands" / COMMAND_NAME,
            "global",
        ),
        "cursor": Entry("cursor", home / ".cursor" / "skills" / ROOT_NAME, None, "global"),
        "codex": Entry("codex", home / ".agents" / "skills" / ROOT_NAME, None, "global"),
    }


def project_entry(cwd):
    return Entry("codex", Path(cwd) / ".agents" / "skills" / ROOT_NAME, None, "project")


def global_skill_parents(home):
    entries = global_entries(home)
    return [entries[name].skill.parent for name in CLIENTS]


def global_command_parents(home):
    entries = global_entries(home)
    parents = []
    for name in CLIENTS:
        command = entries[name].command
        if command is not None:
            parents.append(command.parent)
    return parents


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def bundled_payload_hashes():
    return dict((rel, sha256_file(PAYLOAD_DIR / rel)) for rel in PAYLOAD_FILES)


def bundled_command_bytes():
    return COMMAND_TEMPLATE.read_bytes()


def bundled_command_hash():
    return sha256_bytes(bundled_command_bytes())


def command_has_sentinel(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1 < len(lines) and lines[index + 1].strip() == COMMAND_SENTINEL
    return False


def load_manifest(root):
    path = Path(root) / MANIFEST_NAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("managed") is not True:
        return None
    if not isinstance(data.get("files_sha256"), dict):
        return None
    return data


def platform_notice(os_name):
    if os_name == "nt":
        return (
            "eng-doc-guard: Windows uses best-effort os.replace semantics for the root swap "
            "and age-based stale-lock breaking only (process liveness is unavailable)."
        )
    return None


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def lexists(path):
    return os.path.lexists(str(path))


class Installer(object):
    def __init__(self, home, cwd, force=False, dry_run=False, project=False,
                 os_name=None, out=None, err=None, rename=None, replace=None):
        self.home = Path(home)
        self.cwd = Path(cwd)
        self.force = force
        self.dry_run = dry_run
        self.project = project
        self.os_name = os.name if os_name is None else os_name
        self.out = sys.stdout if out is None else out
        self.err = sys.stderr if err is None else err
        self._rename = os.rename if rename is None else rename
        self._replace = os.replace if replace is None else replace
        self._copy = shutil.copy2
        self._unlink = os.unlink
        self._rmtree = shutil.rmtree
        self._pid = os.getpid()
        self.lock_path = self.home / LOCK_NAME
        self._token = None
        self.failures = []

    # -- output --------------------------------------------------------
    def say(self, message):
        print(message, file=self.out)

    def warn(self, message):
        print(message, file=self.err)

    # -- lock ----------------------------------------------------------
    def _lock_token(self):
        return "%d %.6f" % (self._pid, time.time())

    def _read_lock(self):
        try:
            return self.lock_path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            return None

    def _parse_lock(self, text):
        if not text:
            return None, None
        parts = text.split()
        if len(parts) < 2:
            return None, None
        try:
            return int(parts[0]), float(parts[1])
        except ValueError:
            return None, None

    def _lock_age(self, timestamp):
        if timestamp is None:
            try:
                timestamp = self.lock_path.stat().st_mtime
            except OSError:
                timestamp = time.time()
        return time.time() - timestamp

    def _pid_dead(self, pid):
        if pid is None or self.os_name == "nt":
            return None
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except OSError:
            return False
        return False

    def _lock_is_stale(self, pid, timestamp):
        if self._lock_age(timestamp) > STALE_LOCK_AGE:
            return True
        return self._pid_dead(pid) is True

    def _break_stale_lock(self, observed):
        stale = self.lock_path.with_name(
            self.lock_path.name + ".stale-%d-%d" % (self._pid, int(time.time() * 1000))
        )
        try:
            self._rename(str(self.lock_path), str(stale))
        except OSError:
            return False
        current = None
        try:
            current = stale.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            current = None
        if current != observed:
            if not lexists(self.lock_path):
                try:
                    os.link(str(stale), str(self.lock_path))
                except OSError:
                    pass
                else:
                    try:
                        os.unlink(str(stale))
                    except OSError:
                        pass
            return False
        try:
            os.unlink(str(stale))
        except OSError:
            pass
        return True

    def acquire_lock(self):
        for _ in range(LOCK_ATTEMPTS):
            try:
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                observed = self._read_lock()
                pid, timestamp = self._parse_lock(observed)
                if not self._lock_is_stale(pid, timestamp):
                    raise LockError(
                        "another eng-doc-guard install is running (lock: %s)" % self.lock_path
                    )
                if not self._break_stale_lock(observed):
                    continue
                continue
            token = self._lock_token()
            try:
                os.write(fd, token.encode("utf-8"))
            finally:
                os.close(fd)
            self._token = token
            return
        raise LockError("could not acquire install lock: %s" % self.lock_path)

    def release_lock(self):
        if self._token is None:
            return
        if self._read_lock() == self._token:
            try:
                os.unlink(str(self.lock_path))
            except OSError:
                pass
        self._token = None

    # -- recovery ------------------------------------------------------
    def _cleanup_path(self, path):
        try:
            if lexists(path):
                if os.path.isdir(str(path)) and not os.path.islink(str(path)):
                    shutil.rmtree(str(path), ignore_errors=True)
                else:
                    os.unlink(str(path))
        except OSError:
            pass

    def recover(self, apply):
        actions = []
        parents = list(global_skill_parents(self.home))
        if self.project:
            parents.append(project_entry(self.cwd).skill.parent)
        seen = set()
        for parent in parents:
            key = os.path.abspath(str(parent))
            if key in seen or not parent.is_dir():
                continue
            seen.add(key)
            for child in sorted(parent.iterdir()):
                if child.name.startswith(TMP_PREFIX):
                    actions.append("remove staging dir %s" % child)
                    if apply:
                        self._cleanup_path(child)
            root = parent / ROOT_NAME
            bak = parent / BAK_NAME
            if not lexists(root) and lexists(bak):
                actions.append("restore %s -> %s" % (bak, root))
                if apply:
                    try:
                        self._rename(str(bak), str(root))
                    except OSError as exc:
                        self.warn("warning: could not restore %s: %s" % (root, exc))
            elif lexists(root) and lexists(bak):
                actions.append("delete stale backup %s" % bak)
                if apply:
                    self._cleanup_path(bak)
        command_parents = list(global_command_parents(self.home))
        if self.project:
            pass
        for parent in command_parents:
            if not parent.is_dir():
                continue
            for child in sorted(parent.iterdir()):
                if child.name.startswith(COMMAND_NAME + COMMAND_TMP_SUFFIX):
                    actions.append("remove command leftover %s" % child)
                    if apply:
                        self._cleanup_path(child)
        return actions

    # -- preflight -----------------------------------------------------
    def preflight(self, entries):
        problems = []
        payload = bundled_payload_hashes()
        command_hash = bundled_command_hash()
        for entry in entries:
            problems.extend(self._preflight_skill(entry, payload))
            problems.extend(self._preflight_command(entry, command_hash))
        return problems

    def _preflight_skill(self, entry, payload):
        root = entry.skill
        if os.path.islink(str(root)):
            return ["%s: foreign symlink at skill path; remove it manually" % root]
        if not lexists(root):
            return []
        if not root.is_dir():
            return ["%s: foreign file at skill path; remove it manually" % root]
        manifest = load_manifest(root)
        if manifest is None:
            return ["%s: unmanaged directory (no %s); remove it manually" % (root, MANIFEST_NAME)]
        problems = []
        for rel, expected in manifest["files_sha256"].items():
            target = root / rel
            if not target.is_file():
                continue
            if sha256_file(target) == expected:
                continue
            if sha256_file(target) == payload.get(rel):
                continue
            if self.force:
                continue
            problems.append("%s: modified managed file (use --force to overwrite)" % target)
        return problems

    def _preflight_command(self, entry, command_hash):
        command = entry.command
        if command is None or not lexists(command):
            return []
        if os.path.islink(str(command)):
            return ["%s: foreign symlink at command path; remove it manually" % command]
        if not command_has_sentinel(read_text(command)):
            return ["%s: foreign command file (missing managed sentinel); remove it manually" % command]
        actual = sha256_file(command)
        root = entry.skill
        manifest = None
        if root.is_dir() and not os.path.islink(str(root)):
            manifest = load_manifest(root)
        if manifest is None:
            if actual == command_hash:
                return []
            return ["%s: command file differs from the bundled command; remove it manually" % command]
        recorded = manifest.get("command_sha256") or ""
        if actual == command_hash or (recorded and actual == recorded):
            return []
        if self.force:
            return []
        return ["%s: modified managed command file (use --force to overwrite)" % command]

    # -- install -------------------------------------------------------
    def _copy_payload(self, staged):
        for rel in PAYLOAD_FILES:
            source = PAYLOAD_DIR / rel
            if not source.is_file():
                raise InstallError("missing bundled payload: %s" % source)
            target = staged / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            self._copy(str(source), str(target))

    def _write_manifest(self, staged, entry):
        manifest = {
            "managed": True,
            "version": VERSION,
            "files_sha256": dict((rel, sha256_file(staged / rel)) for rel in PAYLOAD_FILES),
            "command_path": str(entry.command) if entry.command is not None else "",
            "command_sha256": bundled_command_hash() if entry.command is not None else "",
        }
        path = staged / MANIFEST_NAME
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _install_command(self, entry):
        command = entry.command
        command.parent.mkdir(parents=True, exist_ok=True)
        staged = command.with_name(command.name + COMMAND_TMP_SUFFIX + str(self._pid))
        try:
            staged.write_bytes(bundled_command_bytes())
            self._replace(str(staged), str(command))
        except OSError as exc:
            self._cleanup_path(staged)
            raise InstallError("could not install command file %s: %s" % (command, exc))

    def _install_root(self, entry):
        root = entry.skill
        parent = root.parent
        parent.mkdir(parents=True, exist_ok=True)
        staged = parent / (TMP_PREFIX + str(self._pid))
        backup = parent / BAK_NAME
        self._cleanup_path(staged)
        try:
            staged.mkdir()
            self._copy_payload(staged)
            self._write_manifest(staged, entry)
        except BaseException as exc:
            self._cleanup_path(staged)
            if isinstance(exc, InstallError):
                raise
            raise InstallError("staging failed for %s: %s" % (root, exc))
        had_root = lexists(root)
        if had_root:
            try:
                self._rename(str(root), str(backup))
            except OSError as exc:
                self._cleanup_path(staged)
                raise InstallError("could not move aside %s: %s" % (root, exc))
        try:
            self._rename(str(staged), str(root))
        except OSError as exc:
            if had_root:
                try:
                    self._rename(str(backup), str(root))
                except OSError as restore_exc:
                    self._cleanup_path(staged)
                    raise InstallError(
                        "swap failed for %s and restore failed: %s / %s"
                        % (root, exc, restore_exc)
                    )
            self._cleanup_path(staged)
            raise InstallError("could not activate %s: %s" % (root, exc))
        if had_root:
            self._cleanup_path(backup)

    def install_entry(self, entry):
        if entry.command is not None:
            self._install_command(entry)
        self._install_root(entry)

    def _discover(self):
        entries = global_entries(self.home)
        return [entries[name] for name in CLIENTS if load_manifest(entries[name].skill) is not None]

    def _overlap_notice(self):
        entries = global_entries(self.home)
        installed = [name for name in CLIENTS if load_manifest(entries[name].skill) is not None]
        if len(installed) > 1:
            self.say("eng-doc-guard is installed in %d global clients: %s." % (len(installed), ", ".join(installed)))
            self.say("Lockstep upgrades keep every global copy identical; rerun with no arguments to refresh them.")

    def _plan(self, targets):
        for entry in targets:
            self.say("eng-doc-guard: would install %s (%s)" % (entry.skill, entry.scope))

    def install(self, entries=None, lockstep=False):
        notice = platform_notice(self.os_name)
        if notice:
            self.say(notice)
        if self.dry_run:
            for action in self.recover(apply=False):
                self.say("eng-doc-guard: would %s" % action)
            targets = self._discover() if lockstep else list(entries or [])
            if not targets:
                self._print_usage()
                return 2
            problems = self.preflight(targets)
            if problems:
                for problem in problems:
                    self.warn("error: %s" % problem)
                return 1
            self._plan(targets)
            return 0
        try:
            self.acquire_lock()
        except LockError as exc:
            self.warn("error: %s" % exc)
            return 4
        try:
            self.recover(apply=True)
            targets = self._discover() if lockstep else list(entries or [])
            if not targets:
                self._print_usage()
                return 2
            problems = self.preflight(targets)
            if problems:
                for problem in problems:
                    self.warn("error: %s" % problem)
                return 1
            for entry in targets:
                try:
                    self.install_entry(entry)
                except InstallError as exc:
                    self.warn("error: %s" % exc)
                    return 1
            self._overlap_notice()
            return 0
        finally:
            self.release_lock()

    # -- uninstall -----------------------------------------------------
    def _uninstall_entries(self):
        entries = [global_entries(self.home)[name] for name in CLIENTS]
        if self.project:
            entries.append(project_entry(self.cwd))
        return entries

    def _modified_files(self, root, manifest):
        tracked = manifest.get("files_sha256", {})
        modified = []
        for rel, expected in tracked.items():
            target = root / rel
            if not target.is_file() or sha256_file(target) != expected:
                modified.append(rel)
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                rel = path.relative_to(root).as_posix()
                if rel != MANIFEST_NAME and rel not in tracked:
                    modified.append(rel)
        return sorted(set(modified))

    def _uninstall_command(self, entry, apply):
        command = entry.command
        if command is None or not lexists(command):
            return False, False
        if os.path.islink(str(command)):
            self.say("eng-doc-guard: kept foreign command symlink %s" % command)
            return True, False
        if not command_has_sentinel(read_text(command)):
            self.say("eng-doc-guard: kept foreign command file %s" % command)
            return True, False
        actual = sha256_file(command)
        root = entry.skill
        manifest = None
        if root.is_dir() and not os.path.islink(str(root)):
            manifest = load_manifest(root)
        recorded = (manifest or {}).get("command_sha256") or ""
        ours = actual == bundled_command_hash() or bool(recorded and actual == recorded)
        if not ours:
            self.say("eng-doc-guard: kept user-modified command file %s" % command)
            return True, False
        if manifest is not None:
            stored = manifest.get("command_path") or ""
            if stored and stored != str(command):
                self.say(
                    "eng-doc-guard: warning: manifest command_path %s does not match %s; "
                    "deleting only the matrix path" % (stored, command)
                )
        if apply:
            try:
                self._unlink(str(command))
            except OSError as exc:
                self.failures.append(str(command))
                self.warn("error: could not remove %s: %s" % (command, exc))
                return True, False
            self.say("eng-doc-guard: removed command %s" % command)
        else:
            self.say("eng-doc-guard: would remove command %s" % command)
        return True, True

    def _uninstall_root(self, entry, apply):
        root = entry.skill
        if os.path.islink(str(root)):
            self.say("eng-doc-guard: kept foreign symlink %s" % root)
            return False, False
        if not lexists(root):
            return False, False
        if not root.is_dir():
            self.say("eng-doc-guard: kept foreign file %s" % root)
            return True, False
        manifest = load_manifest(root)
        if manifest is None:
            self.say("eng-doc-guard: kept unmanaged directory %s" % root)
            return True, False
        modified = self._modified_files(root, manifest)
        if modified:
            self.say(
                "eng-doc-guard: warning: removing marker-owned root %s with modified files: %s"
                % (root, ", ".join(modified))
            )
        if apply:
            try:
                self._rmtree(str(root))
            except OSError as exc:
                self.failures.append(str(root))
                self.warn("error: could not remove %s: %s" % (root, exc))
                return True, False
            self.say("eng-doc-guard: removed skill root %s" % root)
        else:
            self.say("eng-doc-guard: would remove skill root %s" % root)
        return True, True

    def uninstall(self):
        notice = platform_notice(self.os_name)
        if notice:
            self.say(notice)
        entries = self._uninstall_entries()
        self.failures = []
        if self.dry_run:
            for action in self.recover(apply=False):
                self.say("eng-doc-guard: would %s" % action)
            found, removed = self._do_uninstall(entries, apply=False)
            if not found and not removed:
                self.say("eng-doc-guard: nothing installed")
            return 0
        try:
            self.acquire_lock()
        except LockError as exc:
            self.warn("error: %s" % exc)
            return 4
        try:
            self.recover(apply=True)
            found, removed = self._do_uninstall(entries, apply=True)
            if not found and not removed:
                self.say("eng-doc-guard: nothing installed")
            if self.failures:
                self.warn(
                    "error: %d removal(s) failed: %s"
                    % (len(self.failures), ", ".join(self.failures))
                )
                return 1
            return 0
        finally:
            self.release_lock()

    def _do_uninstall(self, entries, apply):
        found = False
        removed = False
        for entry in entries:
            entry_found, entry_removed = self._uninstall_command(entry, apply)
            found = found or entry_found
            removed = removed or entry_removed
            entry_found, entry_removed = self._uninstall_root(entry, apply)
            found = found or entry_found
            removed = removed or entry_removed
        return found, removed

    def _print_usage(self):
        self.say("eng-doc-guard: no managed installation found.")
        self.say("Install or upgrade one client explicitly:")
        self.say("  python3 scripts/install.py --client opencode|claude|cursor|codex|all")
        self.say("Add --dry-run to preview, --force to override local edits, --project for a project-local codex install.")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="Install or uninstall the eng-doc-guard skill across agent clients.",
    )
    parser.add_argument("--client", choices=list(CLIENTS) + ["all"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--project", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.project and args.client not in (None, "codex"):
        print("error: --project is only supported with --client codex", file=sys.stderr)
        return 2
    home = Path.home()
    installer = Installer(
        home=home,
        cwd=Path.cwd(),
        force=args.force,
        dry_run=args.dry_run,
        project=args.project,
    )
    if args.uninstall:
        return installer.uninstall()
    if args.project:
        return installer.install([project_entry(Path.cwd())])
    if args.client == "all":
        entries = global_entries(home)
        return installer.install([entries[name] for name in CLIENTS])
    if args.client:
        return installer.install([global_entries(home)[args.client]])
    return installer.install(lockstep=True)


if __name__ == "__main__":
    sys.exit(main())
