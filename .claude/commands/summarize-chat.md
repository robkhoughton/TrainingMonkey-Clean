---
allowed-tools: Read, Write, Grep, Glob, codebase_search
description: Summarize the current chat session and save to docs/session_summaries/
---

You are creating a comprehensive summary of the current chat session for **Your Training Monkey**.

## Your Task

Create a **concise** markdown summary of this conversation session and save it to `docs/session_summaries/` with a timestamped filename. Prioritize brevity and essential information only.

## Summary Structure

Generate a markdown document with the following sections:

1. **Header**: Title, Date, Session Focus
2. **Main Objectives**: What was the primary goal or question?
3. **Key Discussions**: Major topics covered
4. **Code Changes**: Files modified, features added/changed
5. **Issues Identified**: Problems discovered or bugs found
6. **Solutions Implemented**: Fixes applied or changes made
7. **Decisions Made**: Important choices or architectural decisions
8. **Next Steps**: Recommended follow-up actions or TODOs
9. **Technical Details**: Important code snippets, configurations, or technical notes

## File Naming Convention

Use format: `YYYY-MM-DD_session_topic.md`

Example: `2025-12-12_codebase_reorganization.md`

Generate the filename based on the main topic of the session.

## Instructions

1. Review the entire conversation history
2. Extract key information following the structure above
3. Generate a **concise** markdown summary (prioritize brevity - avoid verbose explanations)
4. Save the file to `docs/session_summaries/` using the Write tool
5. Confirm the file was created successfully

**Remember**: Keep it brief. Use bullet points, short sentences, and avoid repetition. Focus on essential information only.

## Output Format

The summary should be:
- **Concise**: Be brief and to the point - avoid verbosity, use bullet points and short paragraphs
- **Comprehensive**: Cover all major points discussed (but briefly)
- **Well-organized**: Use clear headings and sections
- **Actionable**: Include specific next steps
- **Technical**: Include relevant code references, file paths, and technical details (keep code snippets minimal)
- **Professional**: Suitable for future reference and onboarding

**CRITICAL**: Prioritize conciseness. Each section should be 2-5 sentences or bullet points maximum. Avoid lengthy explanations or repetition.

## Example Structure

```markdown
# Conversation Summary: [Main Topic]
**Date**: [Current Date]  
**Session Focus**: [Primary objective or theme]

---

## Main Objectives
[What was the user trying to accomplish?]

## Key Discussions
[Major topics covered in the conversation]

## Code Changes
- **Files Modified**: [List of files]
- **Features Added**: [New functionality]
- **Features Changed**: [Modified functionality]

## Issues Identified
[Problems discovered, bugs found, or concerns raised]

## Solutions Implemented
[Fixes applied, changes made, or workarounds implemented]

## Decisions Made
[Important choices, architectural decisions, or design patterns]

## Next Steps
[Recommended follow-up actions, TODOs, or future work]

## Technical Details
[Code snippets, configurations, database changes, API changes, etc.]
```

---

**Important**: After generating the summary, use the Write tool to save it to `docs/session_summaries/[filename].md` and confirm the file was created.

