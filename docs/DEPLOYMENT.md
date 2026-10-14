# Deployment guide

## Before deploying

- Complete PostgreSQL persistence and durable job processing. They are not yet implemented in this branch; current user, session, search, and result state is in-memory.
- Run backend tests, frontend build, Compose validation, Prometheus rule validation, Gitleaks, and Trivy successfully.
- Configure provider secrets in the target platform's secret store.
- Choose a deployment target and provide an authenticated health-check URL.
- Configure TLS, ingress/network policy, log collection, backups, and alert notifications.
- Decide how database migrations will run before application rollout once migrations exist.

## Build immutable images

The Jenkinsfile tags images with the full Git commit SHA. For a manual build:

```bash
IMAGE_TAG="$(git rev-parse HEAD)"
docker build -t scoutline-backend:"$IMAGE_TAG" ./backend
docker build -t scoutline-frontend:"$IMAGE_TAG" ./frontend
```

Push to a private registry only after configuring registry authentication. Do not use `latest` as the only release identifier.

## Local production-like run

See [LOCAL_SETUP.md](LOCAL_SETUP.md). The included Compose configuration is a local production-like topology, not a claim that a cloud deployment has been performed.

## Rollback

1. Identify the last known-good immutable image tag.
2. Update the deployment's backend and frontend image references to that tag (or redeploy the prior commit).
3. Roll out the previous images and check the frontend, `/api/ready`, logs, and Prometheus target health.
4. If persistent storage/migrations are added later, follow the tested migration rollback/forward-fix procedure; do not blindly reverse destructive schema changes.
5. Record the incident and inspect the failing build, image scan, or alert before retrying.

No remote deployment is configured or performed by this repository change.
