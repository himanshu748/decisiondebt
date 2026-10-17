"""Generate the addendum with demo-v3's Deepgram voice and audio settings."""
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

OUT = Path('evidence/ask-addendum-20261017')
SEGMENTS = [
    ('01-owner', 'Live company question and source proof', 12,
     "This is Decision Debt's live, read-only company graph. Ask who owns Billing API. The answer cites its source span and exposes the executed Cypher, parameters, rows and timing."),
    ('02-impact', 'Bounded blast radius and executed Cypher', 13.5,
     'Replacing Auth Gateway reaches twelve services and twelve projects within five hops. The boundary is explicit: Directory Sync is one example at hop six. Here is the actual reverse dependency query.'),
    ('03-typo', 'Suggestions require confirmation', 9,
     'A misspelled Billing API offers a recorded name as a suggestion. No entity is selected until you confirm.'),
    ('04-unsupported', 'Unsupported request rejected', 8,
     'An unsupported request is rejected with the supported shapes. No query is run and no answer is guessed.'),
    ('05-ticket', 'Client-side Markdown ticket export', 12,
     'The Action Board exports an evidence-linked Markdown draft. Conflicting ownership stays unassigned for a human decision. Public mode uses deterministic Cypher, no model or exposed key. Narration by Deepgram.'),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    key = dotenv_values('work/ask-addendum-20261017/deepgram.env')['DEEPGRAM_API_KEY']
    receipt = {'provider':'Deepgram', 'model':'aura-2-thalia-en', 'encoding':'linear16',
               'sample_rate':48000, 'voice_disclosure':'AI-generated narration', 'segments':[]}
    # No automatic retries. A failed provider call requires inspection.
    with httpx.Client(timeout=90) as client:
        for id_, chapter, hold, text in SEGMENTS:
            target = OUT / (id_+'.wav')
            if target.exists():
                raise RuntimeError('Refusing to overwrite narration '+id_)
            started = datetime.now(timezone.utc).isoformat()
            before = time.monotonic()
            response = client.post('https://api.deepgram.com/v1/speak',
                params={'model':receipt['model'], 'encoding':'linear16', 'container':'wav', 'sample_rate':48000, 'speed':1.0},
                headers={'Authorization':'Token '+key}, json={'text':text})
            if response.status_code != 200:
                print(json.dumps({'segment':id_,'status':response.status_code,'request_id':response.headers.get('dg-request-id')}))
                raise SystemExit(1)
            target.write_bytes(response.content)
            metadata = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
                'format=duration,size:stream=codec_name,sample_rate,channels','-of','json',str(target)]))
            entry = {'id':id_,'chapter':chapter,'text':text,'hold_seconds':hold,'path':str(target),
                'requested_at':started,'status':response.status_code,'request_id':response.headers.get('dg-request-id'),
                'characters':len(text),'request_elapsed_seconds':round(time.monotonic()-before,3),
                'duration_seconds':float(metadata['format']['duration']),
                'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'audio_metadata':metadata}
            receipt['segments'].append(entry)
            (OUT/'deepgram-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print(json.dumps({'segment':id_,'duration_seconds':entry['duration_seconds']}),flush=True)
    expected = sum(max(s['hold_seconds'],s['duration_seconds']+.8) for s in receipt['segments'])
    assert 45 <= expected <= 59, expected
    print(json.dumps({'planned_seconds':expected,'segments':len(receipt['segments'])}))


if __name__ == '__main__':
    main()
