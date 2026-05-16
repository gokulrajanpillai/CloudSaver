# Monetization Validation

CloudSaver should validate willingness to pay before expanding Pro, AI, hosted, or Business
surface area. The first paid story should be trust, convenience, and support.

## Offers To Test

### Free Source Preview

Includes:

- Source install.
- Local scans.
- Storage dashboard.
- Duplicate candidates.
- Recommended keep copy.
- Review folder moves.
- Restore manifests.
- JSON and CSV exports.

Validation question:

> Does the free preview deliver enough value that users complete the safe cleanup loop and
> repeat scans?

### Paid Convenience Build

Hypothesis:

> Users who trust the source preview will pay a small one-time fee for signed, easy-to-install
> builds and update convenience.

Potential price tests:

- $19 one-time signed build.
- $39 one-time signed build with one year of updates.
- Pay-what-you-want sponsor-supported build.

Do not sell this until:

- Checksums are published.
- Unsigned/signed status is explicit.
- The install path is easier than source install.
- Refund/support expectations are documented.

### Commercial Support

Hypothesis:

> Small professional users and teams will pay for setup help, report interpretation, and
> cleanup planning before they pay for generic software subscriptions.

Potential price tests:

- $99 cleanup consultation.
- $299/year individual pro support.
- $999/year small team support.

Support can include:

- Install/setup help.
- Report interpretation.
- Review workflow guidance.
- Deployment notes for teams.
- Redacted business report customization.

Support must not include:

- Access to private files.
- Hosted storage.
- Silent deletion.
- Guaranteed recovery.
- Secret telemetry.

## Pilot Questions

Ask every pilot:

- Would you pay $19-$39 once for a signed build?
- Would you pay $79/year for updates, advanced reports, and support?
- Would your team pay for setup/report interpretation?
- Which part would your organization reimburse?
- What trust proof would you need before paying?

## Decision Gates

Proceed to signed-build work when:

- At least 5 external users ask for easier installs or signed builds.
- At least 3 users say they would pay a concrete price.
- No unresolved restore/safety issue remains.

Proceed to commercial support when:

- At least 3 small-team or professional users request report interpretation or setup help.
- The redacted report workflow is useful in pilot reviews.
- Support boundaries are documented before money changes hands.

Do not proceed to broad Pro subscription until:

- Repeat usage within 30 days is visible.
- Paid users ask for recurring value.
- The product has a clear update/support cadence.
