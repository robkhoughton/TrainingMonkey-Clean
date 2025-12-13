# Troubleshooting Protocol

**CRITICAL**: Follow this process sequentially. DO NOT skip phases or propose solutions before Phase 3.

---

## Phase 1: Context Gathering (MANDATORY FIRST)

### 1.1 Read Project Guidelines
- [ ] Read `.claude/CLAUDE.md` - Problem-Solving Philosophy section
- [ ] Read `.cursorrules` if exists
- [ ] Quote relevant guidance that applies to this issue
- [ ] Identify anti-patterns to avoid (from guidelines)

### 1.2 Define the Symptom Precisely
Answer these questions explicitly:
- **Observable Problem**: What exactly is wrong? (be specific)
- **Location**: Where does it manifest? (UI, API, database, etc.)
- **Expected vs Actual**: What should happen vs what's happening?
- **Scope**: Is this isolated or systemic?

### 1.3 Map All Instances
Create complete inventory:
- [ ] List every file/function that calculates/handles this value
- [ ] List every API endpoint that provides this data
- [ ] List every UI component that displays this value
- [ ] Document the complete data flow (source → transformations → destination)

**OUTPUT REQUIRED**: Present findings before proceeding to Phase 2.

---

## Phase 2: Root Cause Investigation (NO SOLUTIONS YET)

### 2.1 Apply "5 Whys" - Document Each Level

```
Symptom: [Observable problem from Phase 1.2]

Why #1: [Immediate cause - what directly causes the symptom?]
Evidence: [Code location, logic, or behavior]

Why #2: [Why does #1 happen? Go deeper]
Evidence: [Code location, logic, or behavior]

Why #3: [Why does #2 happen? Dig further]
Evidence: [Code location, logic, or behavior]

Why #4: [Why does #3 happen? Approaching root]
Evidence: [Code location, logic, or behavior]

Why #5: [ROOT CAUSE - fundamental architectural/design issue]
Evidence: [Code location, logic, or behavior]
```

**CRITICAL**: Continue asking "why" until you reach an architectural or design decision, not just a code-level cause.

### 2.2 Anti-Pattern Detection Checklist

Run through project's anti-pattern checklist:

- [ ] **Duplicate Calculations**: Same value calculated in multiple places with different logic?
- [ ] **Multiple Sources of Truth**: Same data coming from different endpoints/services?
- [ ] **Inconsistent Logic**: Different validation/transformation rules for same data?
- [ ] **Patches/Workarounds**: Try-catch blocks, null checks, or conditionals masking deeper issues?
- [ ] **Client-Side Fixes for Server Problems**: Frontend compensating for backend issues?
- [ ] **Architectural Duplication**: Redundant endpoints, services, or components?

**For each checked item**: Document the specific code locations.

### 2.3 Determine Ground Truth

Answer these questions:
- **Which implementation is canonical/correct?** [Identify by file:line]
- **Which implementations should be eliminated?** [List all]
- **What should be the single source of truth?** [Specify]
- **Why does duplication exist?** [Historical reason, intentional design, or accident?]

**OUTPUT REQUIRED**: Present complete root cause analysis before proceeding to Phase 3.

---

## Phase 3: Solution Design (USER DECISION GATE)

### 3.1 State Root Cause Clearly

**Root Cause Statement**: [One sentence describing the fundamental issue]

**Evidence Summary**: [Key findings from Phase 2]

### 3.2 Impact Analysis

**Files that need changes**:
- [List all files with required modifications]

**Code to be deleted**:
- [List endpoints, functions, or files to remove]

**Potential risks**:
- [What could break? What depends on code being removed?]

### 3.3 Propose Architectural Solutions

Present 2-3 solution approaches:

**Option 1: [Name - e.g., "Eliminate duplicate endpoint"]**
- Changes: [Brief description]
- Pros: [Benefits]
- Cons: [Drawbacks]
- Alignment with guidelines: [How it addresses root cause]

**Option 2: [Alternative approach]**
- Changes: [Brief description]
- Pros: [Benefits]
- Cons: [Drawbacks]
- Alignment with guidelines: [How it addresses root cause]

**Recommended Approach**: [Which option and why]

### 3.4 **STOP - Wait for User Approval**

**DO NOT PROCEED TO PHASE 4 WITHOUT USER CONFIRMATION**

Ask user:
- "Does this root cause analysis align with your understanding?"
- "Should I proceed with [recommended approach]?"
- "Are there constraints or considerations I'm missing?"

---

## Phase 4: Implementation (ONLY AFTER USER APPROVAL)

### 4.1 Implementation Checklist
- [ ] Implement approved solution
- [ ] Remove duplicate code/endpoints
- [ ] Update all consumers to use single source of truth
- [ ] Delete unused files
- [ ] Verify no remaining references to deleted code

### 4.2 Verification
- [ ] Confirm consistency across all affected areas
- [ ] Check for any remaining anti-patterns
- [ ] Validate data flow matches expected architecture

### 4.3 Documentation
- [ ] Update relevant documentation
- [ ] Note breaking changes if any
- [ ] Document the single source of truth for future reference

---

## Red Flags - Abort and Reassess

If you find yourself doing ANY of these, STOP and return to Phase 2:

❌ Copying code from one location to another
❌ Adding conditional logic to "synchronize" values
❌ Creating a second calculation of the same value
❌ Implementing a workaround instead of fixing the root cause
❌ Adding try-catch to suppress errors without understanding them
❌ Making client-side compensations for server-side issues

**These are symptoms you haven't found the root cause yet.**

---

## Success Criteria

A proper fix should:
- ✓ Eliminate duplication, not add synchronization
- ✓ Consolidate to single source of truth
- ✓ Remove code, not add complexity
- ✓ Address the architectural issue, not just the symptom
- ✓ Prevent the issue from recurring

---

## Example: Good vs Bad

**BAD (Patch)**:
```
Problem: ACWR values don't match between endpoints
Solution: Add recalculation logic to both endpoints to sync them
→ Still have duplication, just "synced" duplication
```

**GOOD (Root Cause Fix)**:
```
Problem: ACWR values don't match between endpoints
Root Cause: Two redundant endpoints calculating same data
Solution: Eliminate one endpoint, use single source of truth
→ Duplication removed, impossible to diverge
```

---

## Notes

- This process should take time - rushing leads to patches
- User questioning your approach is a feature, not a bug
- If you're not deleting code, question whether you've found the root cause
- Architectural fixes often involve removal, not addition
