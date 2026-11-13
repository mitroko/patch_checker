#!/usr/bin/env python3
"""Verify that patches from patches/*.yaml are applied in a git repo.

Patch file format:
    name: <check name>
    checks:
    - path: <file path relative to repo root>
      lines:
      - <N>: "<expected content of line N>"
      - "<A>-<B>": |
          <expected content of lines A..B, inclusive>

Comparison rules:
- single line: compared with leading/trailing whitespace stripped
- block: file lines A..B are dedented by their common indentation, then
  compared line by line (trailing whitespace ignored), so relative
  indentation inside the block still matters
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import yaml

repo_path = 'nvidia-infra-controller' # default; relative to current dir, override with argv[1]
patches_dir = Path(__file__).resolve().parent / 'patches'


def git_branch(p: str | Path) -> tuple[str, str, str]:
    """Return (branch name, first 8 chars of HEAD hash, ref decoration) for repo at p.

    Branch is "HEAD" when the repo is in detached HEAD state.
    Decoration is what `git log` shows next to HEAD, e.g.
    "HEAD, tag: v2.2.2-mira3, origin/release-v2.2.2".
    """
    def git(*args: str) -> str:
        return subprocess.run(
            ['git', '-C', str(p), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    return (
        git('rev-parse', '--abbrev-ref', 'HEAD'),
        git('rev-parse', 'HEAD')[:8],
        git('log', '-1', '--format=%D'),
    )


def _parse_range(key: int | str) -> tuple[int, int]:
    """Turn a line key (12, "12", "44-58") into an inclusive 1-based range."""
    if isinstance(key, int):
        return key, key
    start, sep, end = str(key).partition('-')
    return (int(start), int(end)) if sep else (int(start), int(start))


def _line_matches(file_lines: list[str], key: int | str, expected: str) -> bool:
    start, end = _parse_range(key)
    if start < 1 or end < start or end > len(file_lines):
        return False

    if start == end:
        return file_lines[start - 1].strip() == str(expected).strip()

    actual = textwrap.dedent('\n'.join(file_lines[start - 1:end])).splitlines()
    wanted = textwrap.dedent(str(expected)).rstrip('\n').splitlines()
    if len(actual) != len(wanted):
        return False
    return all(a.rstrip() == w.rstrip() for a, w in zip(actual, wanted))


def _check_path(repo: Path, check: dict) -> list[str]:
    """Return failed line keys for this check; ["missing"] if file is unreadable."""
    target = repo / check['path']
    try:
        file_lines = target.read_text(encoding='utf-8').splitlines()
    except OSError:
        return ['missing']

    return [
        str(key)
        for entry in check.get('lines') or []
        for key, expected in entry.items()
        if not _line_matches(file_lines, key, expected)
    ]


def verifier(repo: str | Path = repo_path, pdir: Path = patches_dir) -> bool:
    """Run all checks from pdir/*.yaml against repo. True if all matched."""
    repo = Path(repo)
    ok = True
    for patch_file in sorted(pdir.glob('*.yaml')):
        data = yaml.safe_load(patch_file.read_text(encoding='utf-8')) or {}
        name = data.get('name', patch_file.stem)
        for check in data.get('checks') or []:
            for key in _check_path(repo, check):
                print(f"[{name}] failed {repo / check['path']}:{key}")
                ok = False
    return ok


if __name__ == '__main__':
    repo = sys.argv[1] if len(sys.argv) > 1 else repo_path
    if not Path(repo).is_dir():
        sys.exit(f'repo not found: {repo} (usage: {sys.argv[0]} [repo_path])')
    branch, sha, refs = git_branch(repo)
    print(f'{repo}: {branch} {sha} ({refs})')
    if verifier(repo):
        print('OK. All patches in place')
        sys.exit(0)
    sys.exit(1)
