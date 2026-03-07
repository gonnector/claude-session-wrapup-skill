[English](README.md) | [한국어](README_ko.md)

# /wrapup — Session Wrapup Skill for Claude Code

A Claude Code skill that automatically records two layers of structured notes at the end of each session:

- **Layer 1 — Session Summary**: info bullets, Q&A pairs, decisions with rationale, work done, action items
- **Layer 2 — Lesson-Learned**: what the user learned, what the AI learned (separated by perspective)
- **Layer 3 — Session Evaluation** (v1.4.0): AI self-assessment (5 sub-metrics) + user feedback — a meta-feedback loop for session quality improvement

Records are saved as JSONL — git-friendly, incrementally appendable, queryable.

---

## Requirements

- [Claude Code](https://claude.ai/claude-code) CLI
- Python 3.x

---

## Permission Setup

Add the following to your **global** Claude Code settings (`~/.claude/settings.json`) so the skill runs without approval prompts:

```json
{
  "permissions": {
    "allow": [
      "Bash(python:*)"
    ]
  }
}
```

### Why only `python`?

The skill calls Python scripts at four points (Steps 0, 1, 5). Other tools used during the workflow — `Read`, `Glob`, `Bash(date:*)`, `Bash(pwd:*)` — are auto-approved by Claude Code in default mode because they are non-destructive read-only or trivial operations.

| Step | Tool | Command |
|------|------|---------|
| 0 | `Bash(python:*)` | `settings.py read / detect / write` |
| 1 | `Bash(date:*)` | get current timestamp — auto-approved |
| 1 | `Bash(pwd:*)` | get project path — auto-approved |
| 1 | `Bash(python:*)` | `read-stats.py` |
| 1 | `Read` / `Glob` | scan `~/.claude/projects/` session files — auto-approved |
| 6 | `Bash(python:*)` | `python -c "importlib..."` save to JSONL |

> **Project-level vs global:** The skill's own repo contains `.claude/settings.local.json` for development use only. For the skill to work across all your projects, add `Bash(python:*)` to `~/.claude/settings.json` (global).

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

## Workflow (10 Steps)

```
Step 0  Language check (silent after first run)
Step 1  Collect session metadata
Step 2  Analyze conversation → draft 2-layer summary (with auto memory dedup check)
Step 3  Show draft + confirm (AskUserQuestion)
Step 4  Edit loop (if changes requested)
Step 5  Session evaluation — AI self-assessment + user feedback (v1.4.0)
Step 6  Save to JSONL (including evaluation data)
Step 7  Auto memory sync — promote lessons to auto memory (v1.3.0)
Step 8  Offer to register action items in /atodo
Step 9  Show completion message with evaluation summary + stats
```

### Session Evaluation (v1.4.0)

The skill evaluates session **process quality** (not the topic) from both perspectives:

- **AI self-assessment**: 5 sub-metrics (goal achievement, communication efficiency, technical quality, session flow, learning value) each scored 1-5 with brief reasoning, plus actionable improvements with tags for recurring pattern detection
- **User feedback**: overall score (1-5) + optional good points / bad points / improvements (press Enter to skip each)

AI evaluates first, then user — preventing anchoring bias.

> **Definition**: "AI satisfaction" means **AI's self-diagnosis of session quality**, not emotional satisfaction.

### Auto Memory Integration (v1.3.0)

The skill detects items already recorded in Claude Code's [auto memory](https://docs.anthropic.com/en/docs/claude-code/memory) (`~/.claude/projects/{slug}/memory/`) and avoids duplicating them as lesson-learned entries. Instead, overlapping lessons are tagged `[📝 auto memory]` and focused on **context/reasoning** rather than restating facts.

After saving, the skill offers to **promote** AI lessons that aren't yet in auto memory — useful patterns, tools, or discoveries worth persisting across sessions.

---

## Repository Structure

```
wrapup/
├── SKILL.md                      ← Skill definition (workflow + prompts)
├── scripts/
│   ├── save-wrapup.py            ← JSONL save logic
│   ├── read-stats.py             ← Cumulative stats reader
│   ├── collect-meta.py           ← Session metadata collector
│   └── settings.py               ← Language settings manager
├── references/
│   └── schema.md                 ← JSONL schema definitions
└── docs/
    ├── prd.md                    ← Product Requirements Document
    ├── plans/
    │   └── 2026-02-23-wrapup-skill-design.md
    └── research/
        └── research-report-2026-02-23-lesson-learned-system-design.md
```

---

## License

MIT © 2026 [Gonnector (고영혁)](https://github.com/gonnector)
