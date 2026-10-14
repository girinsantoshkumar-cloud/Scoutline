# Jenkins setup

## Agent prerequisites

Use a dedicated, controlled Jenkins build agent with:

- Git
- Python 3.12 and venv support
- Node.js 20 and npm
- Docker Engine plus Docker Compose v2
- `gitleaks` v8+
- `trivy`
- Network access to pull base images and dependencies

Do not expose the Jenkins controller publicly without authentication, authorization, TLS, and network restrictions. Do not give an internet-facing controller unrestricted host Docker socket access; use a restricted build agent.

## Create the pipeline

1. Push this branch to your repository after reviewing it locally.
2. In Jenkins, choose **New Item → Pipeline**.
3. Select **Pipeline script from SCM**, choose Git, enter the repository URL and the authorized credentials if the repository is private.
4. Set the branch to `feat/production-readiness` for review, or the approved branch after merge.
5. Keep credentials in Jenkins Credentials; do not add API keys to the Jenkinsfile or source tree.
6. Run **Build Now** and inspect each stage and the JUnit report.

## Pipeline stages

Checkout, backend tests, frontend production build, Compose/Prometheus/Grafana configuration validation, production image builds tagged with the full commit SHA, Gitleaks, and Trivy HIGH/CRITICAL vulnerability scans.

The pipeline deliberately does **not** deploy. A deployment stage should be added only after the target environment, secret store, migration order, rollback plan, and health-check URL are defined.

## Expected behavior

- A failing backend test should fail the backend stage and the build.
- A frontend TypeScript/build error should fail the frontend stage.
- A secret finding or HIGH/CRITICAL image finding should fail the security stage.
- Missing tools or Docker permissions should fail the relevant stage rather than be reported as a pass.

The pipeline installs frontend dependencies with pinned package versions. Commit a reviewed lockfile and switch to `npm ci` as a follow-up hardening step.
