#!/usr/bin/env bash
# Regenerate the self-contained standalone.html from disposition_lens.jsx.
# Run after editing the component (e.g. the dog-avatar work).
set -e
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - <<'PY'
jsx = open("disposition_lens.jsx").read()
prelude = ('const { useState, useEffect, useRef, useCallback, useMemo } = React;\n'
           'window.DISPOSITION_API_URL = window.DISPOSITION_API_URL || "http://localhost:8000";\n')
src = prelude + "\n" + jsx
tpl = open("standalone.template.html").read()
open("standalone.html","w").write(tpl.replace("__SRC__", src))
print("standalone.html regenerated from disposition_lens.jsx")
PY
