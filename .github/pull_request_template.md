## Workload ID

<!-- Required. Every change must be traceable to a workload (use n/a only for repo maintenance). -->
Workload ID:

## What changed

## Checklist

- [ ] Synthetic data only; no customer names, data or code
- [ ] No hardcoded project IDs, regions, passwords (all in `.env.example` / Secret Manager)
- [ ] `pre-commit run --all-files` passes (gitleaks, terraform fmt, shellcheck)
- [ ] Dependencies locked (`requirements.txt`)
- [ ] Least-privilege service account
- [ ] README updated (thesis, KPIs, products and versions, cost estimate)

## Reviewer checklist (go/ce-customer-code-sharing)

- [ ] Apache 2.0 header (`Copyright <year> Google LLC`) in every new source file; README keeps the AS-IS notice
- [ ] No keys, passwords, tokens or service account keys
- [ ] No Google-confidential information; no internal links in code meant for a CSR repo
- [ ] Third-party code attributed; no GPL/copyleft or banned licenses
- [ ] Demo/sample code only: nothing for a customer's production environment, no customer code

## AI assistance

- [ ] This PR contains AI-generated code (Jetski, Antigravity, Gemini) and the author reviewed every line
