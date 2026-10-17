# Application identity and permissions

The app user is a DataOS application identity for this agent Service. It must exist before the Service starts; manual creation is optional.

The installer reads `agent_id`, reuses an existing application identity or creates it during `--apply`. It rejects a name belonging to another user type. Planning creates nothing. The Service uses `runAsUser`; DataOS projects its runtime credential. Operator login credentials stay outside the container.

## Admin setup permissions

The installing admin needs permission to inspect/create application identities, read/create the declared policies, inspect configured resources and Secrets, create credential Secrets when absent, and deploy the Service. The package also grants the configured operator run-as, schema-read and private agent-ingress access.

## App user runtime permissions

| Capability | Access in the template |
|---|---|
| Compute and sources | Read/use configured compute; read/resolve configured Depot and its source credentials. |
| Credentials | Read configured model/Git Secrets and Vulcan managed state/object-store Secrets, including metadata/governance/resolver gates. |
| Product lifecycle | Tenant/type lifecycle gates, product-prefix read/update/delete, resource apply/status/runtime/log access and schema reads. |
| Verification | Product queries and catalog discovery. |

The exact declarations are in `access.template.json`; inspect the rendered `access.json`. This bootstrap bundle includes tenant-level and HTTP gates alongside named scopes; it is not a verified minimum-permission set. Policy comparison does not prove every operation is authorized.

Product retry/unquarantine and automatic catalog registration remain operator handoffs. The agent receives no IAM/grant-management permission. All callers currently share its application identity; per-caller authorization and credential rotation are not automated.
