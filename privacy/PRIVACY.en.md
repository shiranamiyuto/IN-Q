# Diagnostic Information and Privacy

[日本語](../PRIVACY.md) | [English](PRIVACY.en.md) | [简体中文](PRIVACY.zh.md)

## Basic Policy

IN-Q V2 does not transmit diagnostic information externally until the user explicitly executes a bug report.

The body and attachments posted to GitHub Issues will be made public on the internet. Please review the content on IN-Q's confirmation screen and GitHub's posting screen before sending.

## Items Scheduled to be Included in Public Diagnostic Information

- IN-Q core and plugin versions
- MHW version or build
- State transitions around the time of occurrence
- Quest ID, stage, camp, and number of participants
- Timeouts, exceptions, and internal processing failures
- MOD loader version
- List of installed MOD file names (only when explicitly selected by the user)

## Items Not Collected or Transmitted

- Steam authentication information
- Save data itself
- Chat message text
- Absolute paths including Windows usernames
- IP addresses
- Passwords, API keys, and tokens
- Other authentication information

## Transmission Method

Diagnostic information is formatted into a format that the user can review before sending. The user performs the final submission operation on the GitHub submission screen opened by IN-Q. Developer GitHub credentials are never embedded in IN-Q.
