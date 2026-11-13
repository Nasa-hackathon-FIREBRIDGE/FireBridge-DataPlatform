# FireBridge-DataPlatform

CI/CD and deployment bootstrap for the replacement of `Nasa-hackathon-FIREBRIDGE/FireBridge-data-pipeline`.
Application source and its Git history have intentionally not been copied.

## Deployment behavior

Pushes to `main` run the CI/CD checks and verify the pinned-host, restricted SSH
connection to the existing production service. The initial scaffold does not
build or replace the running application. Once complete source code is added,
the same workflow runs application tests, builds and verifies the release,
then automatically activates it on the existing server after all checks pass.
Pull requests run checks without production credentials or deployment.

Production environment: `production`. Runtime root: `/opt/firebridge`.
Runtime credentials, data, databases and TLS stay on the server. Deployment keys
are environment secrets, never repository files. Existing release images and
backups remain available for rollback.

## Add application code

1. Clone this repository and work on `main` (or merge a development branch into `main`).
2. Copy the application source into this checkout. Preserve this repository's
   `.github/`, `.ci/`, `deploy/`, Dockerfiles and Nginx configuration when copying
   from the old repository; they contain the replacement repository identities.
3. Commit and push normally with `git push origin main`. Do not replace the
   initialized branch with the old repository history using a force push.
4. Follow the Actions run. Production changes only after the checks succeed.

The minimum source markers are listed in `.ci/scaffold.json`. A partial upload
fails explicitly. No markers means the pipeline waits for the first code push.

See `deploy/README.md` for service-specific validation and recovery details.
