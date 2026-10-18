"""Build an offline-friendly GitHub Pages HTML file with a bundled data fallback."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sp=json.loads((root/'data/spots.json').read_text('utf-8'))
# Keep the initial HTML lightweight on mobile; the full catalog loads over JSON.
fallback=[spot for spot in sp if not spot.get('candidate')]
if not fallback:
    fallback=sp[:120]
live=json.loads((root/'data/live.json').read_text('utf-8'))
embedded=json.dumps({'spots':fallback,'live':live},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
template=(root/'scripts/index.template.html').read_text('utf-8')
assert '__EMBEDDED_DATA__' in template
(root/'index.html').write_text(template.replace('__EMBEDDED_DATA__',embedded),'utf-8')
print('Built lightweight index.html with',len(fallback),'offline spot fallbacks;',len(sp),'total catalog spots')
