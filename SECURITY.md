# Security Policy

## Supported Versions

CloudSaver is early-stage. Security fixes are applied to the default branch.

## Reporting A Vulnerability

Please do not open a public issue for vulnerabilities.

Use GitHub private vulnerability reporting:

https://github.com/gokulrajanpillai/CloudSaver/security/advisories/new

If private reporting is unavailable, open a minimal public issue asking for a maintainer
contact without including exploit details.

## Security Expectations

CloudSaver should:

- Keep scans local by default
- Avoid hidden network calls
- Avoid committing credentials, tokens, generated reports, or private file paths
- Never silently delete or overwrite user files
- Validate paths before writing generated files
