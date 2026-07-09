# integrations/ — generated, do not edit by hand

Every file here is produced by `scripts/build_integrations.py` from `skills/*/SKILL.md`.
Edit the skills, then regenerate:

```sh
python3 scripts/build_integrations.py
```

CI runs `--check` and fails if these files don't match the skills.

| Path | For | Mounted by |
|---|---|---|
| `skills/motiscope-*/SKILL.md` | Codex, Cursor, and any agent reading the [agentskills.io](https://agentskills.io) `SKILL.md` shape | `motiscope install codex` / `cursor` / `skills --dir P` |
| `agents/AGENTS.motiscope.md` | The ~20 tools that read [`AGENTS.md`](https://agents.md) | `motiscope install agents` |
| `cursor/rules/motiscope.mdc` | Cursor project rule (`alwaysApply: false` + description = "Apply Intelligently") | `motiscope install cursor` |

The skills carry only `name` and `description` frontmatter — the only two keys both Codex
and Cursor read. Claude Code uses `skills/` at the repo root instead, which additionally
carries `allowed-tools`, `argument-hint`, and `user-invocable`.

See [PLATFORMS.md](../PLATFORMS.md).
