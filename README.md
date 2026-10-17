# DataOS Agents

Build and deploy agents on DataOS. The kit separates the operator’s agent-building skill from each deployed agent’s task behavior.

| Folder | Purpose |
|---|---|
| [skills/build-dataos-agent](skills/build-dataos-agent/SKILL.md) | Generic skill for the admin’s coding agent. |
| [agents/data-productization](agents/data-productization/README.md) | Productization agent runtime, business skill, CLI tools, Vulcan docs and external installer. |
| [dist/dataos-agent-kit.zip](dist/dataos-agent-kit.zip) | Self-contained kit for sharing without cloning. |

## Use with a coding agent

Clone this repository and open it in Codex or Claude Code. Say:

> Read skills/build-dataos-agent/SKILL.md. Use agents/data-productization to configure, deploy and verify a productization agent on my DataOS environment. Ask only for missing admin setup inputs and collect credentials privately.

The admin supplies Git destination/credentials, model API key, compute, Depots and permissions. Business users only discuss requirements and ask the running agent to build or update products.

For manual setup, follow the [package instructions](agents/data-productization/README.md). Keep credential values outside this repository; setup uses platform Secrets.

## Validation status

Six offline package checks pass. The earlier hosted runtime built a real product with operator assistance. A fresh installation of this revised package still needs live verification; it is not yet a proven one-click installer.

```bash
python3 -m unittest discover -s agents/data-productization/tests -v
```
