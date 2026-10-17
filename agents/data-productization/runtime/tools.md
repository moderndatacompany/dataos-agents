# Tool templates

Prefer the existing CLI MCP server: `dataos-ctl develop assist mcp run`. Register it with the harness and select relevant tools. Use its live schemas; inspect installed command help for shell equivalents.

```bash
# Discover resources visible to the configured identity.
dataos-ctl resource get -t depot -a
dataos-ctl resource get -t depot -n "$DEPOT" -d
dataos-ctl resource get -t vulcan -a
dataos-ctl develop stack versions

# In a new product folder: use Vulcan's scaffold, then configured connections.
vulcan init
vulcan info
vulcan lint
vulcan test
vulcan create_deploy_yaml

# Validate/deploy the generated manifest; inspect exact resource and children.
dataos-ctl resource apply -f "$MANIFEST" --lint --disable-interpolation
dataos-ctl resource apply -f "$MANIFEST" --disable-interpolation
dataos-ctl resource get -i "$RESOURCE_ID" -d
dataos-ctl resource get runtime -i "$RESOURCE_ID"
dataos-ctl resource log -i "$RESOURCE_ID" --tailLines 80
```

MCP equivalents include `dataos_resource_get`, `dataos_resource_apply`, `dataos_resource_runtime_get`, `dataos_resource_log` and `dataos_schema_validate`.

Read `vulcan init --help` for noninteractive scaffold options. Run only commands supported by the installed version. Generate deployment YAML with Vulcan; fill environment settings from service configuration.

Depot details identify connections, not every table. Use the configured source metadata tool or engine-aware read-only SQL through `vulcan fetchdf` where supported. `fetchdf` executes warehouse SQL; its credentials must enforce the intended source boundary.

Use available query/catalog tools for verification. The inspected DataOS CLI lacks a general query/Argus search command; resource status alone cannot verify those gates. A deployment adapter must expose missing operations as tools, or report them unavailable. Keep endpoint routing and authentication inside that adapter.
