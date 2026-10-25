# Inherited source manifest (historical only)

The loose source-root `FULL_BACKUP_MANIFEST.json` was inherited from V12. It did not describe V16.1 or V17. The exact bytes are retained here as `INHERITED_V12_BACKUP_MANIFEST.json` (SHA-256 `eaaa284dec71493d2e68648e1a704f7411cf3e1ba591984582894086f3102415`) for provenance, not release identity.

V16.1 identity is established by its full archive and `tests/release/V16_1_RELEASE.json`. The current candidate identity is established by `tests/v17/CANDIDATE_MANIFEST.json`; the new full archive generates its own complete file manifest. No historical runtime asset was changed by this reconciliation.
