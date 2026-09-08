# Aevrynd Engine Journey hosting workflow

- This checkout owns the public site at `https://aevrynd-engine-journey.peca12968.chatgpt.site` (`appgprj_6a9f65e01f788191b67dea346af8e074`).
- After every validated website change, build and deploy the updated Site in the same task unless the user explicitly requests local-only work.
- Keep the public Site aligned with the MVC/IIS presentation while preserving its D1-backed analytics and hosting-specific implementation.
- Treat the online URL as the primary user-facing test and delivery URL.
