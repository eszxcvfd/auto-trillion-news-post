# Exec Plan

## Goal

Create the future session-onboarding slice so the operator can log into a
supported platform from the local Web UI once, save that session locally, and
reuse it for later posting runs.

## Scope

In scope:

- define the Web UI login and session-refresh contract for supported platforms
- persist application-managed local session state per platform
- expose session readiness or `login-required` state in the UI
- reuse saved sessions from later posting flows
- keep session handling separate from workbook truth and posting-decision logic

Out of scope:

- cloud-hosted auth or remote session brokers
- storing raw passwords or secrets for unattended credential login
- bypassing captcha or platform verification controls
- adding new platform support outside the accepted rollout

## Risk Classification

Risk flags:

- Auth
- Audit/security
- External systems
- Public contracts
- Existing behavior
- Weak proof
- Multi-domain

Hard gates:

- auth/session lifecycle changes
- external provider behavior
- changing local runtime or storage assumptions for platform sessions

## Work Phases

1. Discovery of current session assumptions across CLI, posting core, and Web
   UI plans.
2. Design of Web UI onboarding, local session storage, and session-health
   checks.
3. Validation planning for safe login flows and session reuse proof.
4. Implementation of UI-triggered login and session persistence.
5. Verification against FR-08 and FR-13 session expectations.
6. Harness update for proof status and follow-up decisions.

## Stop Conditions

Pause for human confirmation if:

- the login flow requires storing credentials beyond session state
- a platform requires unsupported verification patterns that break the local
  operator model
- the session boundary starts to depend on a specific developer browser profile
- validation would need to weaken security or observability expectations
