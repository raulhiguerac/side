---                                                          
name: gen-commit
description: Use this skill to generate a production ready commit message based on the current session changes                                                   
argument-hint: optional scope or extra context                                                             
disable-model-invocation: true                            
---

Review the last commits of the repo and copy their structure and style.

Then:
1. Run `git diff` and `git status` to see what changed
2. Stage the relevant files (never .env or secrets)
3. Write a commit message following the repo's style
4. Never commit to the repo, only write the commit message

## Commit message format

Follow this exact structure (taken from the repo's commits):

```
<type>(<scope>): <short summary — comma-separated topics>

- <bullet: what was added/changed and why, one logical unit per line>
- <bullet: ...>
```

Rules:
- First line: `feat|fix|refactor|chore(scope): summary` — keep under 80 chars
- Use em dash (—) in the summary to separate the main topic from secondary ones
- Bullets: one per logical change. Lead with the verb (Add, Fix, Wire, Implement, Remove, Extract).
- Bullets must be specific: name the class/file/method affected, not just "updated X"
- Group related changes into one bullet when they move together (e.g. port + adapter + UC for the same feature)
- Do not add a trailing period on bullets
- Do not wrap bullets in backticks unless referencing a specific symbol