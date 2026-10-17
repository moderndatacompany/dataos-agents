#!/usr/bin/env python3
"""Append phase timing or raw Codex usage to JSONL; never record argv or output."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import time


def emit(path, record):
    record['ts_utc'] = datetime.now(timezone.utc).isoformat()
    with path.open('a') as stream:
        stream.write(json.dumps(record) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--phase', required=True)
    parser.add_argument('--log', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--cli-events', type=Path)
    parser.add_argument('--intervention', choices=['credential', 'approval', 'grant', 'retry', 'catalog', 'route-correction'])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    base = {'run_id': args.run_id, 'phase': args.phase}
    if args.intervention:
        emit(args.log, dict(base, event='manual.intervention', category=args.intervention))
    elif args.cli_events:
        events = [json.loads(line) for line in args.cli_events.read_text().splitlines() if line.strip()]
        usage = [e['usage'] for e in events if e.get('type') == 'turn.completed']
        emit(args.log, dict(base, event='model.cli_counter', raw_usage=usage,
                           accounting='raw_not_additive_billing_unverified'))
    else:
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command:
            parser.error('Provide a command after -- or --cli-events')
        emit(args.log, dict(base, event='phase.started'))
        start, code, timed_out = time.monotonic(), 127, False
        process = None
        try:
            process = subprocess.Popen(command, start_new_session=os.name == 'posix')
            code = process.wait(timeout=args.timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            code = 124 if isinstance(exc, subprocess.TimeoutExpired) else 130
            timed_out = code == 124
            if process is not None:
                if os.name == 'posix':
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                else:
                    process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    if os.name == 'posix':
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        process.kill()
                    process.wait()
        except OSError:
            pass
        emit(args.log, dict(base, event='phase.completed',
                           elapsed_ms=round((time.monotonic() - start) * 1000),
                           exit_code=code, timed_out=timed_out))
        raise SystemExit(code)
