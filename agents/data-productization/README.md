# Data productization agent package

Operator files live in `deploy/`; only `runtime/` enters the running agent. The admin supplies Git repository/credentials, model API key, compute, Depots and access during setup. Actual users only discuss requirements and send the agent off to build.

Copy `environment.example.json`, select your environment connections and Git destination, then run:

```bash
python3 install.py environment.json --cli-config "$DATAOS_CONFIG_DIRECTORY"
python3 install.py environment.json --cli-config "$DATAOS_CONFIG_DIRECTORY" --apply
```

The first command plans; the second creates a missing application identity, adds the declared access and submits the Service. Existing model/Git Secrets are reused; absent Secrets require private entry. The operator must already be authenticated. An inaccessible Secret is a blocker, not permission to overwrite it.

This package contains the tested OpenAI/Codex + DataOS CLI + Vulcan/Postgres sidecar runtime, readable wrapper/bridge source, model/Git projections, business skill, CLI templates and relevant Vulcan docs. Git is a shared collection: one folder per product. Complete documentation remains available at https://v2.dataos.info/ .

`deploy/runtime.lock.json` records replaceable build dependencies. Select compatible newer versions there, including the CLI lab capability this runtime transport uses. For another engine, supply its image and connection projection. Direct container execution requires explicit operator authorization in configuration.

Installer rendering is tested offline. A fresh installation and the revised default prompt still require live verification. Submission is not readiness: inspect Service logs/runtime, verify model/CLI/Vulcan/Git, and verify product deployment/query/quality/catalog. Product-scoped retry/catalog gaps from the original trial remain unresolved. Shared multi-user conversation isolation and a product UI are subsequent work.
