"""Restore reviewed local Listening editions without rerunning OCR or changing history."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[1];LIB=ROOT/'library'

def main():
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    base=LIB/'preparation/listening/overrides';count=0
    for kind in ('tests','keys','transcripts'):
        files=sorted((base/kind).glob('*.json'))
        if len(files)!=32:raise SystemExit(f'Missing reviewed {kind}: expected32, found{len(files)}. Copy your local library first.')
        (LIB/'listening'/kind).mkdir(parents=True,exist_ok=True)
        for source in files:
            target=LIB/'listening'/kind/source.name;data=source.read_bytes();json.loads(data)
            if args.check:
                if not target.exists() or hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(data).digest():raise SystemExit(f'Edition differs: {target}')
            else:target.write_bytes(data)
            count+=1
    print(json.dumps({'files':count,'byteIdentical':True,'checkedOnly':args.check}))

if __name__=='__main__':main()
