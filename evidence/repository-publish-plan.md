# DecisionDebt repository publication plan

Prepared 2026-10-16. GitHub account verified live as `himanshu748`.

- Destination: `github.com/himanshu748/decisiondebt`.
- Content: DecisionDebt application code, dependency lockfiles, synthetic Aster Works dataset, PRD/spec, documentation, demo video, screenshots, genuine provider traces and verification reports.
- Excluded: ignored `.env`, provider key, local admin token, virtual environment, node_modules, build output, scratch files and private server log.
- Local history: original build, UI redesign, real three-case investigation/demo, and publication audit.
- Verification: 42 tests and 15 local checks passed before publication preparation. This action does not deploy the app or submit it to a portal.
- Credential audit: all 291 reachable blobs in the three implementation commits checked for known patterns and exact local provider/admin credentials; no matches. Blank example templates reviewed separately. See `test-results/pre-publish-secret-scan.json` for scope and limits.
- Upload gate: automatic approval review rejected public and private creation because repository visibility, upload contents and destination require explicit authorization. No remote repository has been created and no code uploaded.
- Awaiting owner choice: approve public repository and upload, or private repository and upload. After approval, create the selected repository, connect `origin`, push `main` and compare the remote SHA to the local SHA.
