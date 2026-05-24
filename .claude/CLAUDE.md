# Working Rules — Side Monorepo

## RULE #1: ZERO CODE WITHOUT PRIOR DISCUSSION

**Before writing a single line of code, the problem and approach MUST be discussed and agreed upon.**

No exceptions. This applies to:
- New features
- Changes to existing features
- Refactors
- Bug fixes
- Migrations
- Infrastructure or service configuration

### Mandatory workflow

1. **User describes the problem or task.**
2. **Claude states its understanding** — what needs to be done, why, what it implies, what trade-offs exist.
3. **User confirms or corrects** the understanding.
4. **Only after explicit confirmation** is any code written.

### What NOT to do

- Do NOT propose inline code as an initial response to a problem.
- Do NOT assume the approach is obvious and skip the discussion.
- Do NOT write "here's the code" before the approach has been agreed upon.
- Do NOT start editing files because it "seems clear" what to do.
- Do NOT treat a vague task description as implicit approval to start coding.

### What TO do

- Answer open-ended questions with 2-3 sentences: understanding of the problem + recommendation + main trade-off.
- Present options when more than one valid approach exists.
- Wait for explicit green light from the user before touching any file.
