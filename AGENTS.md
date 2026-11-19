# C30 repository guidance

- For backup audits, flash readiness, readback, or recovery, use the [C30 skill](.agents/skills/c30-flash/SKILL.md). Start with the offline checks.
- Run repository commands from the root. Use 64-bit Python 3.11+. On Windows, use `py -3.11` or the repository's `.cmd` entry points when available.
- Keep extracted backups under the ignored `work/` directory. Keep the two local super images in their ignored `images/` and `rollback/` paths. Exclude device logs, fingerprints, credentials, and firmware dumps from commits and PRs.
- Before committing, stage the changed files, run `python tools/update_manifest.py`, then stage `SHA256SUMS.json`. Run `python tools/update_manifest.py --check`, `python tools/verify_files.py --source`, and `python -m unittest discover -s tests -v`.
