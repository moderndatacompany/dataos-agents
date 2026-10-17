---
name: build-dataos-agent
description: Package and deploy an agent on DataOS using a model runtime, application identity, configured tools, documentation and platform connections. Used by the operator’s coding agent.
---

Build the agent requested by the operator. Keep its deployment machinery outside its runtime instructions.

1. Reuse a supplied agent package; otherwise create one following [the package contract](references/package.md).
2. Collect operator configuration: target environment, model credential, Git destination and approved platform connections. Reuse existing setup.
3. Inspect available tools/stacks and their documentation. Resolve compatible versions in build configuration, not behavior instructions.
4. Follow [DataOS deployment](references/deploy.md): run package checks, resolve prerequisites and deploy within the operator's authorization.
5. Verify model invocation and required tool capabilities. Deliver the reusable package, configuration and invocation instructions.

This skill builds agents. Each deployed agent receives only its own task instructions, skills, tools and documentation. Source interviewing and product-building behavior belong to that agent's package.
