# AevryndWeb project workflow

- After completing any local development change, build the solution and publish it to the local IIS site at `http://localhost:8081/`.
- Verify the updated page and affected APIs on that IIS URL before reporting the change ready.
- Commit the validated MVC source and push `main` to the GitHub `AevryndWeb` origin before publishing the corresponding public Site. Confirm that the remote branch resolves to the pushed commit.
- After local verification, always synchronize the corresponding public site content and deploy it to `https://aevrynd-engine-journey.peca12968.chatgpt.site` in the same task, unless the user explicitly requests a local-only change.
- Preserve each platform's backend implementation: SQL Server for the MVC/IIS project and D1 for the hosted Sites project.
- Report the online URL as the primary test and delivery URL. Do not stop after the localhost deployment or wait for a separate testing round before publishing.
