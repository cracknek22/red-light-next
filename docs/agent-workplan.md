# Red Light Next Agent Workplan

## Agent 1 — Architect / Lead
Owns architecture, module boundaries, acceptance criteria, and integration decisions.

## Agent 2 — Backend/Core Agent
Owns router, serialization, settings, errors, logging, HTTP client, cache abstractions.

## Agent 3 — Provider/Scraper Agent
Owns provider interfaces, debrid integrations, Easynews, external scraper adapter, source sorting/filtering.

## Agent 4 — Frontend/Kodi UI Agent
Owns Kodi menus, setup wizard, provider status screens, No Results diagnostics, source result windows, settings UI.

## Agent 5 — Security/Updater Agent
Owns redaction, updater hardening, safe ZIP extraction, manifest/hash checks, static security gates.

## Agent 6 — Repo/Build/CI Agent
Owns packaging, addon.xml validation, repo metadata generation, checksums, test/build commands.

## Agent 7 — QA/Integration Agent
Owns smoke tests, integration tests, manual Kodi test plan, regression matrix, final readiness report.

## Milestone 1 Definition of Done

- pytest passes.
- static scan passes.
- router has no exec-based dispatch.
- serialization writes JSON only.
- redaction masks representative secrets.
- safe_zip blocks zip-slip paths.
