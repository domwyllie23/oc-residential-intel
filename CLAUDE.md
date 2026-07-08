# CLAUDE.md

Project-specific guidance for Claude Code working in this repository.

## MLS / CRMLS data — compliance boundary

Candice has CRMLS access. CRMLS's Rules & Regulations restrict redistribution of MLS data
(active listings, sold comps, and statistics derived from them) to permitted uses — they do not
permit posting MLS-derived content to a public, unauthenticated URL.

**This repo (`oc-residential-intel`) is public**, and `docs/` is served live on GitHub Pages.
That means:

- **Never write MLS/CRMLS-derived data, listings, or derived statistics into `docs/`, `outputs/`,
  or any file that gets committed to this repo.** This includes anything computed *from* MLS
  exports, not just raw listing data — a "median days on market for zip X" chart built from an
  MLS export is still MLS-derived.
- The public report and Pages site stay on the free public sources already wired up here: Zillow
  Research, Redfin Data Center, U.S. Census, Census Building Permits Survey. That boundary is not
  a limitation to work around — it's the compliance line.
- If/when Candice provides an MLS export (CRMLS or otherwise), analyze it freely for her — that's
  a legitimate internal use. But the output goes to a **private, non-public deliverable**: a local
  notebook/file she opens herself, a private repo, or a direct email/PDF — never a path under
  `docs/` in this repo, never a new public repo, never an Artifact shared beyond her.
- When in doubt about whether something counts as "MLS-derived," ask before publishing it
  anywhere public.

See also `data/reference/SOURCES.md` for the provenance of the (non-MLS) reference data already
in the project.
