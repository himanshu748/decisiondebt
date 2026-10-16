# DecisionDebt repository publication plan

Prepared 2026-10-16. GitHub account verified live as `himanshu748`.

- Destination: `github.com/himanshu748/decisiondebt`.
- Content: DecisionDebt application code, dependency lockfiles, synthetic Aster Works dataset, PRD/spec, documentation, demo video, screenshots, genuine provider traces and verification reports.
- Excluded: ignored `.env`, provider key, local admin token, virtual environment, node_modules, build output, scratch files and private server log.
- Local history: original build, UI redesign, real three-case investigation/demo, and publication audit.
- Verification: 42 tests and 15 local checks passed before publication preparation. This action does not deploy the app or submit it to a portal.
- Credential audit: all 291 reachable blobs in the three implementation commits checked for known patterns and exact local provider/admin credentials; no matches. Blank example templates reviewed separately. See `test-results/pre-publish-secret-scan.json` for scope and limits.
- Owner authorization: explicitly approved public repository creation and upload of the named contents to `himanshu748/decisiondebt`; credentials remain excluded.
- Remote repository: https://github.com/himanshu748/decisiondebt (public), created under the authenticated owner account and connected as `origin`.
- Publish procedure: commit this documentation, push `main`, then compare GitHub's default branch SHA and `git ls-remote` with the local SHA. No deployment or portal submission is included.
