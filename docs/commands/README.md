# Slash Commands Documentation

This directory contains documentation for custom Claude Code slash commands used in the TrainingMonkey project.

---

## Available Commands

### `/verify-ui`
**Purpose**: Automated UI verification workflow for frontend components
**Status**: Implemented (awaiting CLI registration)
**Documentation**: [VERIFY_UI_COMMAND.md](./VERIFY_UI_COMMAND.md)

**Quick usage**:
```bash
/verify-ui <component-id> <checklist-items>
```

**Example**:
```bash
/verify-ui #at-a-glance-meters "stroke widths 8px, gauges aligned, ticks light"
```

**What it does**:
1. Rebuilds React application
2. Deploys to mock server
3. Screenshots component with Playwright
4. Programmatically verifies alignment, dimensions, colors
5. Generates detailed verification report

---

### `/design-review`
**Purpose**: Comprehensive design review of branch changes
**Status**: Active
**Location**: `.claude/commands/design-review.md`

**Quick usage**:
```bash
/design-review
```

**What it does**:
- Reviews all frontend changes in current branch
- Tests across multiple viewports (desktop/tablet/mobile)
- Verifies brand compliance
- Checks accessibility
- Reports findings with priority levels

---

### `/summarize-chat`
**Purpose**: Create session summary documentation
**Status**: Active
**Location**: `.claude/commands/summarize-chat.md`

**Quick usage**:
```bash
/summarize-chat
```

**What it does**:
- Reviews conversation history
- Extracts key decisions and changes
- Creates timestamped markdown summary
- Saves to `docs/session_summaries/`

---

### `/troubleshoot`
**Purpose**: Systematic debugging and issue resolution
**Status**: Active
**Location**: `.claude/commands/troubleshoot.md`

**Quick usage**:
```bash
/troubleshoot
```

**What it does**:
- Analyzes current error or issue
- Checks logs and system state
- Provides step-by-step debugging guide
- Suggests solutions with root cause analysis

---

## Command Implementation Guide

### Creating a New Slash Command

1. **Create command file**: `.claude/commands/your-command.md`

2. **Add front matter**:
```markdown
---
allowed-tools: Bash, Read, Write, Grep, Glob
description: Brief description of what the command does
---
```

3. **Write command instructions**:
```markdown
You are a [specialist role] for **Your Training Monkey**.

## Your Task
[What the command should do]

## Workflow
[Step-by-step instructions]

## Output Format
[Expected output structure]
```

4. **Test the command**:
```bash
/your-command [parameters]
```

5. **Document it**: Add entry to this README

---

## Best Practices

### Command Design

✅ **DO**:
- Keep commands focused on a single purpose
- Provide clear usage examples
- Include error handling instructions
- Document expected output format
- List required tools in front matter

❌ **DON'T**:
- Create overly complex multi-purpose commands
- Assume prerequisites without checking
- Skip validation steps
- Omit error handling

---

### Usage Tips

**When to use slash commands**:
- Repetitive multi-step workflows
- Standardized verification/review processes
- Documentation generation
- Complex analysis requiring multiple tools

**When NOT to use slash commands**:
- Simple one-off tasks
- Tasks requiring interactive decisions
- Exploratory work without clear workflow
- Tasks better suited for direct tool use

---

## Related Documentation

- **Project Guidelines**: `.claude/CLAUDE.md`
- **Code Quality Standards**: `.claude/rules/code-quality.md`
- **Design Principles**: `docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`
- **Session Summaries**: `docs/session_summaries/`

---

## Command Reference Matrix

| Command | Use Case | Duration | Prerequisites |
|---------|----------|----------|---------------|
| `/verify-ui` | UI component verification | ~2 min | Mock server running |
| `/design-review` | Branch design compliance | ~5 min | Mock server running |
| `/summarize-chat` | Session documentation | ~1 min | None |
| `/troubleshoot` | Debug issues | Varies | Error context |

---

## Contributing

### Adding Command Documentation

1. Create new markdown file in `docs/commands/`
2. Follow structure of existing documentation
3. Include examples and troubleshooting
4. Update this README with new command entry

### Documentation Template

```markdown
# `/command-name` Command Documentation

**Purpose**: One-line description
**Status**: Active/Planned/Experimental
**Location**: `.claude/commands/command-name.md`

## Overview
[Detailed description]

## Usage
[Syntax and parameters]

## Examples
[Real-world usage examples]

## Output Format
[Expected results]

## Troubleshooting
[Common issues and solutions]
```

---

**Last Updated**: 2025-12-13
**Maintained By**: Claude Code Team
