---
name: wiki-capture
description: Distill the recent conversation (or provided text) into a markdown file under docs/sources/ to preserve a decision, finding, or author directive without storing a literal transcript. After capture, wiki-ingest can be run on the new file to propagate findings into the curated wiki.
argument-hint: optional topic descriptor (e.g. "wiki-pilot-decision")
disable-model-invocation: true
---

You will distill a conversation or text into a wiki source. **Never store literal transcripts** — extract only actionable content.

## Steps

1. **Identify what to capture:**
   - If `$ARGUMENTS` contains pasted text or a topic description, use that.
   - Otherwise, assume "recent conversation in this session" and summarize what was discussed.

2. **Ask the user** (only if not obvious from context):
   - **Service** the capture relates to: `analytics-service`, `properties-service`, `_shared`, etc.
   - **Descriptor** in kebab-case for the filename (e.g. `wiki-pilot-decision`, `mlflow-vs-bentoml`).

3. **Generate distilled content** with this structure. Aim for ~80% less text than the original conversation while keeping 100% of the actionable content.

   ```markdown
   ---
   title: <readable title>
   captured-from: conversation | pasted-text | external
   captured-on: YYYY-MM-DD
   participants: [author, claude]
   ---

   ## Context
   1-3 sentences explaining why this was discussed.

   ## Key conclusions
   - Decision or finding in one sentence.
   - Another decision.

   ## Open questions
   - Things left unresolved, if any.

   ## Next steps
   - Agreed actions, if any.
   ```

4. **Write** to `docs/sources/<service>/YYYY-MM-DD-<descriptor>.md`. Use today's date.

5. **Show the user** the generated content and the path.

6. **Immediately run `/wiki-ingest`** on the new file — do not wait for the user to ask. Invoke the wiki-ingest skill with the path of the file just created.

## Rules

- Don't copy the conversation literally. If the summary ends up nearly as long as the original, compress again.
- If the conversation has no actionable content or clear decision, tell the user and **do not create the file**. Zero sources is better than empty sources.
- Don't include sensitive info (credentials, personal data, secrets) even if it appeared in the chat.
- The file is **immutable** once created — if new info on the same topic appears later, create a new file with a later date rather than editing the old one.
