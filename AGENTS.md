# Aevrynd Engine Journey hosting workflow

- This checkout owns the public site at `https://aevrynd-engine-journey.peca12968.chatgpt.site` (`appgprj_6a9f65e01f788191b67dea346af8e074`).
- After every validated website change, build and deploy the updated Site in the same task unless the user explicitly requests local-only work.
- Keep the public Site aligned with the MVC/IIS presentation while preserving its D1-backed analytics and hosting-specific implementation.
- Treat the online URL as the primary user-facing test and delivery URL.

## Character development goal

- For character work, including automatic goal continuations, first read `docs/character-continuous-goal.md`, the asset manifest, and the latest iteration evidence. The user redesigned this goal on 2026-10-19; follow its current v7 workflow and acceptance rules instead of the older goal text's workflow. First handle the user's current request, then follow visible improvement to one complete working character, bounded single-defect rounds, integration of retained studies, resource checkpoints, and ineffective-method stop rules. Deliver actual full-head/body views each production round and track appearance/function/contact/runtime separately. Prompt maintenance does not start a model iteration.
- Offline character studies and goal-document edits are not website changes. Keep studies separate from formal runtime and public preview assets; follow the goal document's promotion and user-acceptance requirements.
