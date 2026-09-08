# AevryndWeb project workflow

- After completing any local development change, build the solution and publish it to the local IIS site at `http://localhost:8081/`.
- Verify the updated page and affected APIs on that IIS URL before reporting the change ready.
- Treat the local IIS deployment as the user's acceptance-test build. Wait for the user to finish testing before any later external deployment or release step.

