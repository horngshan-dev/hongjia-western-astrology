# SPDX-License-Identifier: AGPL-3.0-only
"""Create corresponding source from this standalone directory only."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXCLUDE={'build','dist','__pycache__','.git'}
def package():
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(x in EXCLUDE for x in p.relative_to(ROOT).parts) and p.name!='SOURCE_SHA256.json')
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (ROOT/'SOURCE_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'dist').mkdir(exist_ok=True)
    with tarfile.open(ROOT/'dist/source.tar.gz','w:gz') as t:
        for p in files+[ROOT/'SOURCE_SHA256.json']:t.add(p,arcname='hongjia-western/'+str(p.relative_to(ROOT)),recursive=False)
    return ROOT/'dist/source.tar.gz'
if __name__=='__main__':print(package())
