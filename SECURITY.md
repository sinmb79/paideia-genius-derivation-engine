# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| `0.2.x` | Yes |
| `< 0.2.0` | No |

## Security Boundary

This package is designed for public-safe profile artifact generation. It does not perform network calls, store API keys, store OAuth tokens, or persist hidden chain-of-thought.

The engine masks common provider token patterns before export, including OpenAI-style `sk-*`, GitHub `gh*_*`, Slack `xox*`, Google `ya29.*`, and `Bearer ...` values. This is a safety net, not a full DLP system.

## Reporting

If you find a security issue, open a private report through GitHub Security Advisories when available. If advisories are unavailable, open a minimal public issue without including secrets, personal training records, or raw private reasoning traces.

## Public Examples

Repository examples must remain synthetic. Do not commit real training records, private user data, API keys, OAuth tokens, or raw reasoning traces.
