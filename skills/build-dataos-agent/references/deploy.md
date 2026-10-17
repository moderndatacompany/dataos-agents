# DataOS deployment

Use the operator's authenticated CLI context; verify hostname and tenant before writes.

```bash
dataos-ctl tenant list
dataos-ctl resource get -t compute -a
dataos-ctl develop stack versions
dataos-ctl user get --id "$AGENT_ID"
# When authorized and absent:
dataos-ctl user create --user_id "$AGENT_ID" --name "$AGENT_ID" --type application
dataos-ctl resource apply -f "$MANIFEST" --lint --disable-interpolation
dataos-ctl resource apply -f "$MANIFEST" --disable-interpolation
dataos-ctl resource get -i "$SERVICE_ID" -d
dataos-ctl resource get runtime -i "$SERVICE_ID"
dataos-ctl resource log -i "$SERVICE_ID" --tailLines 80
```

Use a Service with a compatible container Stack, selected compute and application `runAsUser`. Supply the model harness and required tools via images/init containers/sidecars. Project the application identity, platform connection and named Secrets; decode encoded Secret projection fields. Keep operator credentials outside the container.

Operator run-as access, agent compute use, resource lifecycle, named Secret metadata/governance/resolution and Depot use are distinct checks. Vulcan packages additionally need managed state/object-store credentials. Check the package's complete access contract before model execution.

Linux namespaces may be unavailable inside the container. Choose an authorized supported execution boundary. Inspect actual startup/tool results; manifest acceptance alone does not establish readiness.
