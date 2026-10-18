"""Build an offline-friendly GitHub Pages HTML file with a bundled data fallback."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sp=json.loads((root/'data/spots.json').read_text('utf-8'))
live=json.loads((root/'data/live.json').read_text('utf-8'))
embedded=json.dumps({'spots':sp,'live':live},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
template=(root/'scripts/index.template.html').read_text('utf-8')
assert '__EMBEDDED_DATA__' in template
(root/'index.html').write_text(template.replace('__EMBEDDED_DATA__',embedded),'utf-8')
print('Built index.html with',len(sp),'spot fallbacks')
