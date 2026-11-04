# Diagnostic Information and Privacy

[日本語](../PRIVACY.md) | [English](PRIVACY.en.md) | [简体中文](PRIVACY.cn.md)

## Basic Policy

IN-Q V2 does not send diagnostic information externally until the user explicitly executes a bug report.

The body text and attachments posted to GitHub Issues will be public on the internet. Please review the contents on IN-Q's confirmation screen and GitHub's posting screen before sending.

## Items Scheduled to be Included in Public Diagnostic Information

- IN-Q core and plugin versions
- MHW version or build
- State transitions around the time of occurrence
- Quest ID, stage, camp, number of participants
- Timeouts, exceptions, internal processing failures
- MOD loader version
- List of installed MOD file names (only when explicitly selected by the user)

## Items Not Collected or Sent

- Steam credentials
- Save data itself
- Chat body text
- Absolute paths including Windows usernames
- IP addresses
- Passwords, API keys, tokens
- Other authentication information

## Transmission Method

Diagnostic information is formatted into a format that the user can review before sending. The user performs the final submission operation on the GitHub posting screen opened by IN-Q. Developer GitHub credentials will not be embedded in IN-Q.
