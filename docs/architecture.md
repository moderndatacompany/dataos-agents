# Separate building an agent from using it

| Component | Used by | Responsibility |
|---|---|---|
| Build DataOS Agent skill | Admin's coding agent | Package, configure and deploy an agent on DataOS. |
| Productization agent package | Installer and runtime | Deployable code, dependencies, tools, docs and product-building behavior. |
| Running productization agent | Business users | Discover sources, gather business meaning, build, deploy, monitor and iterate on products. |

The package has two directories. `deploy/` stays with the installer; `runtime/` enters the container. The runtime never receives instructions to deploy itself.

The admin configures the shared product repository, credentials, compute, accessible Depots and product scope once. Model API credentials enter during setup. Business users provide requirements and choose among relevant discovered sources.

Reusable code handles rendering, prerequisite checks, credential projection and installation. Existing DataOS CLI/MCP and Vulcan CLI handle supported operations. Only missing integrations need new adapters. Documentation provides syntax; the business skill provides judgment and conversation.

The future Agent Builder Stack packages the common installation mechanism. Agent types supply different runtime bundles. We are packaging only productization now.

The portable kit includes both the generic builder skill and the productization package. Offline rendering is checked; revised runtime initialization and a fresh install require live verification. The original product trial remains an assisted proof.
