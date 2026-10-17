# Agent package contract

Separate two directories:

- `deploy/`: installer, Service template, access configuration and runtime dependency lock. Used by the operator's coding agent.
- `runtime/`: task instructions, task-specific skills, tool wrappers and searchable documentation. Included in the running agent.

Operator configuration supplies environment/tenant, application identity, model/Secret references, Git destination, compute, sources and owned resource scope. Credential values enter privately into platform Secrets.

Installer responsibilities: verify target, identify existing resources, report missing access, render manifests, apply authorized changes and inspect startup. Preserve existing configuration on conflicts. A CLI binary does not confer permissions.

Use DataOS CLI or its MCP server for supported operations. Missing integrations belong in code adapters. Keep provider versions, image versions and engine adapters in build configuration. Reuse compatible installed tools; refresh and test dependencies deliberately.

For shared agents, the operator explicitly defines who may invoke the service and which sources/results that audience may access. An application identity does not automatically inherit caller permissions.

Public platform documentation: https://v2.dataos.info/ .
