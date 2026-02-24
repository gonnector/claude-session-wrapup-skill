[English](README.md) | [한국어](README_ko.md)

# /wrapup — Session Wrapup Skill for Claude Code

A Claude Code skill that automatically records two layers of structured notes at the end of each session:

- **Layer 1 — Session Summary**: info bullets, Q&A pairs, decisions with rationale, work done, action items
- **Layer 2 — Lesson-Learned**: what the user learned, what the AI learned (separated by perspective)

Records are saved as JSONL — git-friendly, incrementally appendable, queryable.

---

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- Python 3.x

---

## Installation

```bash
# Symlink the skill into Claude Code's skill discovery path
ln -s /path/to/wrapup ~/.claude/skills/wrapup
```

After linking, Claude Code will automatically recommend `/wrapup` at the end of sessions.

---

## Usage

### Standard wrapup
Start a session wrapup (Claude will draft and confirm before saving):
```
/wrapup
```

### Change language
```
/wrapup change lang
```

---

## Language Settings

On first run, the skill detects your system language and asks you to confirm.
After that, it runs silently using the saved setting.

To change the language later, mention the change keyword when invoking the skill.
The keyword is shown in the completion message footer in your current language:

```
Wrap-up Language: English | Change: /wrapup change lang
```

**Supported languages:** Korean, English, Japanese, Chinese (Simplified), and others via free input.

Settings are stored at: `~/.claude/skill-settings/wrapup/settings.json`

---

## Output Files

| Data | Path |
|------|------|
| Session summaries | `Z:\_ai\session-summaries\{project-slug}\summaries.jsonl` |
| User lesson-learned | `Z:\_myself\lesson-learned\lessons.jsonl` |
| AI lesson-learned | `Z:\_ai\lesson-learned\lessons.jsonl` |

> Paths are configurable in `scripts/save-wrapup.py`.

---

## Workflow (8 Steps)

```
Step 0  Language check (silent after first run)
Step 1  Collect session metadata
Step 2  Analyze conversation → draft 2-layer summary
Step 3  Show draft + confirm (AskUserQuestion)
Step 4  Edit loop (if changes requested)
Step 5  Save to JSONL
Step 6  Offer to register action items in /atodo
Step 7  Show completion message with stats
```

---

## Repository Structure

```
wrapup/
├── SKILL.md                      ← Skill definition (workflow + prompts)
├── scripts/
│   ├── save-wrapup.py            ← JSONL save logic
│   ├── read-stats.py             ← Cumulative stats reader
│   └── settings.py               ← Language settings manager
├── references/
│   └── schema.md                 ← JSONL schema definitions
└── docs/
    ├── plans/
    │   └── 2026-02-23-wrapup-skill-design.md
    └── research/
        └── research-report-2026-02-23-lesson-learned-system-design.md
```

---

## License

MIT © 2026 [Gonnector (고영혁)](https://github.com/gonnector)
