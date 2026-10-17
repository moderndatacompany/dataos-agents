#!/usr/bin/env bash
# Invoke as the lab's Codex command, with a DataOS-projected credential file.
set +x
set -euo pipefail
umask 077
export GIT_ASKPASS=/etc/dataos/work/git-askpass
export GIT_TERMINAL_PROMPT=0

readonly key_file=/run/showcase-model/openai-api-key
export CODEX_HOME=/etc/dataos/work/showcase-codex
unset OPENAI_API_KEY CODEX_API_KEY CODEX_ACCESS_TOKEN
mkdir -p "$CODEX_HOME"
chmod 700 "$CODEX_HOME"

if [[ ! -s "$key_file" ]]; then
  printf '%s\n' 'OpenAI credential is not projected. Complete the private key setup first.' >&2
  exit 1
fi

# This home is container-local; no personal account cache is copied into it.
cp /etc/dataos/work/agent-config.toml "$CODEX_HOME/config.toml"

if ! /etc/dataos/work/bin/codex login --with-api-key < "$key_file" >/dev/null 2>&1; then
  printf '%s\n' 'OpenAI API authentication failed; credential and client output withheld.' >&2
  exit 1
fi
exec /etc/dataos/work/bin/codex "$@"
