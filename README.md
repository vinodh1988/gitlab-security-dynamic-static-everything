# GitLab security reporting lab

An intentionally vulnerable Flask application for GitLab security training. Use an isolated lab with no real credentials or sensitive data. Infrastructure files are scan fixtures; do not deploy them.

Project: https://gitlab.com/firstorg-india/first-project-security

## Enabled pipeline

The pipeline now enables security scanning directly through official GitLab templates. It targets current GitLab.com (GitLab 19.0+ templates) and GitLab Ultimate or a trial for the complete graphical reporting experience.

| Feature | Job | GitLab report artifact | Dashboard category |
| --- | --- | --- | --- |
| Python SAST | `semgrep-sast` | `gl-sast-report.json` / `sast` | SAST |
| Terraform/Kubernetes IaC | `kics-iac-sast` | `gl-sast-report.json` / `sast` | SAST (IaC analyzer) |
| Secret detection | `secret_detection` | `gl-secret-detection-report.json` / `secret_detection` | Secret detection |
| Dependency scanning and SBOM | `dependency-scanning` | `gl-dependency-scanning-report.json` / `dependency_scanning`, CycloneDX SBOMs | Dependency scanning |
| Container scanning | `container_scanning` | `gl-container-scanning-report.json` / `container_scanning` | Container scanning |
| Browser DAST | `dast` | `gl-dast-report.json` / `dast` | DAST |
| API security | `api_security` | `gl-api-security-report.json` / `dast` | DAST (API scanner) |
| API fuzzing | `apifuzzer_fuzz` | `gl-api-fuzzing-report.json` / `api_fuzzing` | API fuzzing |

Reports and scanner commands come from the official templates. Findings are produced by actual analyzers; none are fabricated. IaC and API security share report categories with SAST and DAST respectively, so eight jobs do not imply eight distinct dashboard categories.

The build stage packages the app, exports its resolved Python dependency graph, and publishes `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA`. The test stage runs application smoke tests and static/container scans. The dast and fuzz stages each start a fresh app service at `http://lab-target:5000` for dynamic testing. No public deployment or external target URL is required.

Branch and merge request pipelines are supported. Default-branch pipelines are explicitly retained because the dashboard uses their results. Scanner execution errors fail visibly instead of being allowed to fail silently. Vulnerability findings generally do not fail scanner jobs by themselves.

## GitLab prerequisites

- Ultimate or a suitable trial in the project's namespace. YAML cannot grant a license or unlock the security dashboard.
- Linux AMD64 Docker executor runner with at least 4 GB RAM; allow enough memory and job timeout for browser/API scanning.
- Privileged Docker-in-Docker support for `build_container`, with `/certs/client` shared between the job and service for TLS. GitLab-hosted Linux runners normally support this; check your selected runner. Windows shell executors are unsupported by this pipeline.
- Project Container Registry enabled. Runner must be able to pull this project's private commit image as a service using GitLab's job credentials.
- Network access to Docker Hub, PyPI, GitLab analyzer images, advisory services, and the GitLab dependency-scanning API.
- Runner support for per-job networks (`FF_NETWORK_PER_BUILD=true`). Dynamic targets run only on their job networks and are removed with the jobs.

Remove conflicting project/group variables such as `SAST_DISABLED`, `SECRET_DETECTION_DISABLED`, `DEPENDENCY_SCANNING_DISABLED`, `CONTAINER_SCANNING_DISABLED`, `DAST_DISABLED`, `APISEC_DISABLED`, or `API_FUZZING_DISABLED`. Project/group variables take precedence over this YAML. Also remove stale `CS_IMAGE`, scanner URL overrides, and variables disabling default-branch scans. Do not override the lab's scan URLs with a production target: active DAST and fuzzing are enabled.

## Run and confirm graphical results

1. Commit this project to the default branch (or merge the configuration there).
2. Open **Build > Pipeline editor > Validate** and validate the expanded configuration on your GitLab instance.
3. Run **Build > Pipelines > New pipeline** against the default branch.
4. Confirm `build_container` publishes the commit image, then confirm all eight scanner jobs run successfully. A skipped, failed, or license-excluded job does not establish security coverage.
5. In the pipeline's **Security** tab, check that each scanner's findings were ingested. Check the job artifacts and logs if GitLab reports a missing or invalid report.
6. Open **Secure > Security configuration**. GitLab determines enabled status from report artifacts in the latest default-branch pipeline.
7. Open **Secure > Vulnerability report** to filter findings by scanner and report type. Open **Secure > Security dashboard** for severity charts and trends. Allow GitLab to finish report ingestion after the pipeline completes.

Project links:

- [Pipelines](https://gitlab.com/firstorg-india/first-project-security/-/pipelines)
- [Security configuration](https://gitlab.com/firstorg-india/first-project-security/-/security/configuration)
- [Vulnerability report](https://gitlab.com/firstorg-india/first-project-security/-/security/vulnerability_report)
- [Security dashboard](https://gitlab.com/firstorg-india/first-project-security/-/security/dashboard)

Dashboard acceptance requires a successful default-branch scan, valid typed security report artifacts, a supported license/role, and detected vulnerabilities. Results from an unmerged feature branch alone do not populate the default-branch dashboard. Open vulnerabilities are the ones counted by dashboard charts. Scanning enabled is not a guarantee that each analyzer will detect every deliberately vulnerable example.

## Included detection targets

- Application: SQL injection, shell injection, template injection, reflected XSS, unsafe YAML loading, SSRF, arbitrary file access, and open redirect.
- Dependencies: deliberately older pinned Python packages.
- Secrets: synthetic, nonfunctional AWS-shaped values. Historic secret scanning is enabled so initial-commit fixtures are included. Rules or validity checks may suppress synthetic examples; never add a real secret to force a result.
- Containers: an older Python/Debian runtime, root execution, and vulnerable application packages.
- Infrastructure: public SSH ingress, disabled S3 public-access protection, privileged pod, and host access.
- API: `openapi.yaml` describes the users and YAML-import endpoints. Scanner target variables point to the temporary app service rather than the local-development URL in the specification.

Runtime Kubernetes scanning requires separate infrastructure and is not enabled. License inventory is not a vulnerability scanner. Detection counts vary with analyzer rules and advisory databases.

## Local application checks

```sh
python -m venv .venv
# Activate the virtual environment for your shell.
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python app.py
```

The local app binds to `127.0.0.1:5000`. With Docker installed, `docker compose up --build` also exposes only loopback. Functional tests deliberately preserve the training weaknesses.

## Troubleshooting

- **Cannot connect to Docker:** verify privileged services, shared TLS cert volume, and the Linux Docker executor.
- **Image not found / unauthorized:** confirm `build_container` passed, the registry is enabled, and `CS_IMAGE` matches the commit image tag. Dynamic service pulls also need registry access.
- **Dependency scan API error:** check Ultimate entitlement, GitLab version, API connectivity, and scanner logs. This uses the current v2 SBOM scanner, not the legacy Gemnasium integration.
- **Dynamic scan connection failure:** inspect the lab service logs and its port 5000 health check; confirm per-job networking. The scanners cannot use your laptop's localhost.
- **Empty or missing dashboard:** inspect default-branch job status, report ingestion errors, license, role, filters, and whether any findings are still open. A green application test job is not proof of a security scan.
- **Slow secret scan:** full-history scanning is enabled for this small lab. After a successful baseline, set `SECRET_DETECTION_HISTORIC_SCAN` to `false` for incremental scanning.

## Documentation

- [Security configuration](https://docs.gitlab.com/user/application_security/detect/security_configuration/)
- [Security dashboard prerequisites](https://docs.gitlab.com/user/application_security/security_dashboard/)
- [Vulnerability report](https://docs.gitlab.com/user/application_security/vulnerability_report/)
- [SBOM dependency scanning](https://docs.gitlab.com/user/application_security/dependency_scanning/dependency_scanning_sbom/)
- [Container scanning](https://docs.gitlab.com/user/application_security/container_scanning/)
- [IaC scanning](https://docs.gitlab.com/user/application_security/iac_scanning/)
- [DAST configuration](https://docs.gitlab.com/user/application_security/dast/browser/configuration/)
- [API security configuration](https://docs.gitlab.com/user/application_security/api_security_testing/configuration/enabling_the_analyzer/)
- [API fuzzing configuration](https://docs.gitlab.com/user/application_security/api_fuzzing/configuration/enabling_the_analyzer/)
