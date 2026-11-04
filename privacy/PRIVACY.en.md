# Diagnostic Information and Privacy

[日本語](../PRIVACY.md) | [English](PRIVACY.en.md) | [简体中文](PRIVACY.cn.md)

## Basic Policy

IN-Q V2 does not send diagnostic information externally until the user explicitly submits a bug report.

The body text and attachments posted to GitHub Issues will be public on the internet. Please review the contents on IN-Q's confirmation screen and GitHub's posting screen before submitting.

## Items Scheduled to be Included in Public Diagnostic Information

- IN-Q core and plugin versions
- MHW version or build
- State transitions around the time of occurrence
- Quest ID, stage, camp, number of participants
- Timeouts, exceptions, and internal processing failures
- MOD loader version
- List of installed MOD filenames (only when explicitly selected by the user)

## Items Not Collected or Sent

- Steam authentication information
- Save data itself
- Chat message body
- Absolute paths containing Windows usernames
- IP addresses
- Passwords, API keys, tokens
- Other authentication information

## Submission Method

Diagnostic information is formatted into a reviewable format for the user before sending. The user performs the final submission action on the GitHub posting screen opened by IN-Q. Developer GitHub credentials are never embedded in IN-Q.
