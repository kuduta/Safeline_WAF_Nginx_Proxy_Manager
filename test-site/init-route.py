"""Install the local fixture route once; preserve unrelated NPM custom config."""
from pathlib import Path
import re

target = Path('/data/nginx/custom/http.conf')
fixture = Path('/fixtures/npm.conf').read_text(encoding='utf-8-sig')
existing = target.read_text(encoding='utf-8-sig') if target.exists() else ''
if re.search(r'(?m)^\s*server_name\s+waf-test\.localhost\s*;', existing):
    print('Test route already present; preserved existing configuration.')
else:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        # Exclusive creation preserves an earlier backup rather than overwriting it.
        backup = target.with_name('http.conf.before-test-route')
        if not backup.exists():
            with backup.open('x', encoding='utf-8') as handle:
                handle.write(existing)
    target.write_text(existing.rstrip() + '\n\n' + fixture, encoding='utf-8')
    print('Installed local test route; unrelated configuration preserved.')
