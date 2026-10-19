# Aevrynd Engine Journey hosting workflow

- This checkout owns the public site at `https://aevrynd-engine-journey.peca12968.chatgpt.site` (`appgprj_6a9f65e01f788191b67dea346af8e074`).
- After every validated website change, build and deploy the updated Site in the same task unless the user explicitly requests local-only work.
- Keep the public Site aligned with the MVC/IIS presentation while preserving its D1-backed analytics and hosting-specific implementation.
- Treat the online URL as the primary user-facing test and delivery URL.

## Character development goal

- For character work, including automatic goal continuations, first read `docs/character-continuous-goal.md`, the asset manifest, and the latest iteration evidence. The user redesigned this goal on 2026-10-20; follow its current v12 main prompt and acceptance rules instead of the older goal text's workflow. First handle the user's current request. Reconcile actual files and unregistered results before following an old continuation. Start production from actual complete-character views, choose the main defect, falsify cheaply, then produce, integrate, and verify the affected scope. Distinguish visible improvement, functional unblocking, useful research, and rejection; fewer technical failures do not establish better appearance. Retained research must state its production purpose and minimum integration step. Stop failed methods and repeated minor-only progress; reassess the complete character rather than perpetuating sunk-cost research. Deliver actual full-head/body evidence and matched candidate A/B when a complete candidate exists, stating early rejection honestly. Track appearance/function/contact/runtime separately. Prompt maintenance does not start a model iteration; female acceptance remains required before male work.
- Offline character studies and goal-document edits are not website changes. Keep studies separate from formal runtime and public preview assets; follow the goal document's promotion and user-acceptance requirements.
