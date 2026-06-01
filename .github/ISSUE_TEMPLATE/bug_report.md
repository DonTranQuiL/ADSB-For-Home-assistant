---
name: 🐛 Bug report
about: Report a problem or unexpected behavior in SkyRadar Fusion
title: "[BUG] <Brief description of the issue>"
labels: bug
assignees: ''
---

## 🛑 Checklist
Before submitting, please confirm:
- [ ] I am using the latest version of SkyRadar Fusion.
- [ ] I have checked the existing open and closed issues.
- [ ] I have enabled debug logging for this integration.
- [ ] I have included the relevant logs below.

## 📝 Describe the bug
A clear and concise description of what the bug is.

## ⚙️ Environment & Configuration
Please provide your environment details to help us reproduce the issue:
- **Home Assistant Version:** (e.g., 2026.5.x)
- **SkyRadar Fusion Version:** (e.g., v2.0.0)
- **Installation Method:** (HACS / Manual)
- **Tracking Mode:** (Zone / Additional Tracked)
- **FR24 Enrichment Enabled:** (Yes / No)
- **Zero-Bloat Memory/Recorder Excluded:** (Yes / No)

## 🔄 To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. Configure '...'
4. See error

## 🎯 Expected behavior
A clear and concise description of what you expected to happen.

## 💥 Actual behavior
Describe what actually happened.

## 📸 Screenshots
If applicable, add screenshots of your Lovelace dashboard or integration configuration to help explain your problem.

## 📋 Logs
Please paste all relevant logs from `Settings → System → Logs`. 

*Tip: To enable debug logging, add the following to your `configuration.yaml`, restart, and trigger the issue again:*

```yaml
logger:
  default: info
  logs:
    custom_components.skyradar_fusion: debug