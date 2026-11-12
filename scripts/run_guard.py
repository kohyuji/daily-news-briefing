"""An ignored, exclusive cross-run lock. Never silently displace an active run."""
import argparse,json,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('action',choices=['acquire','release'])
parser.add_argument('--run-id',required=True)
args=parser.parse_args()
lock=ROOT/'.ops/run.lock'
if args.action=='acquire':
    try:
        with lock.open('x',encoding='utf-8') as f:
            json.dump({'run_id':args.run_id,'started_at':datetime.now(timezone(timedelta(hours=9))).isoformat()},f)
    except FileExistsError:
        raise SystemExit('Another run or unfinished lock exists: '+lock.read_text(encoding='utf-8'))
else:
    if lock.exists():
        data=json.loads(lock.read_text(encoding='utf-8'))
        if data['run_id']!=args.run_id:raise SystemExit('Lock owner differs; release refused')
        lock.unlink()
print(args.action+': '+args.run_id)
