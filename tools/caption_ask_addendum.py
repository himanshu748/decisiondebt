"""Verify Deepgram speech and place real word timestamps on the addendum edit."""
import difflib
import hashlib
import json
import re
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import dotenv_values

OUT = Path('evidence/ask-addendum-20261017')


def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def timestamp(seconds):
    millis = round(seconds*1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{millis:03}'


def main():
    speech = json.loads((OUT/'deepgram-receipt.json').read_text())
    key = dotenv_values('work/ask-addendum-20261017/deepgram.env')['DEEPGRAM_API_KEY']
    checks = []
    (OUT/'speech-checks').mkdir(exist_ok=True)
    with httpx.Client(timeout=90) as client:
        for segment in speech['segments']:
            raw_path = OUT/'speech-checks'/(segment['id']+'.json')
            if not raw_path.exists():
                response = client.post('https://api.deepgram.com/v1/listen',
                    params=[('model','nova-3'),('language','en'),('punctuate','true'),('smart_format','true'),
                        ('keyterm','DecisionDebt'),('keyterm','FalkorDB'),('keyterm','Billing API'),('keyterm','Deepgram')],
                    headers={'Authorization':'Token '+key,'Content-Type':'audio/wav'},
                    content=Path(segment['path']).read_bytes())
                if response.status_code != 200:
                    print(json.dumps({'segment':segment['id'],'status':response.status_code}))
                    raise SystemExit(1)
                raw_path.write_text(json.dumps(response.json(),indent=2)+'\n')
            data = json.loads(raw_path.read_text())
            alternative = data['results']['channels'][0]['alternatives'][0]
            similarity = difflib.SequenceMatcher(None,normalize(segment['text']),normalize(alternative['transcript'])).ratio()
            checks.append({'id':segment['id'],'request_id':data['metadata']['request_id'],
                'audio_sha256':hashlib.sha256(Path(segment['path']).read_bytes()).hexdigest(),
                'script_transcript_similarity':round(similarity,6),'transcript':alternative['transcript'],
                'hash_matches_narration':hashlib.sha256(Path(segment['path']).read_bytes()).hexdigest()==segment['sha256'],
                'words':len(alternative['words'])})
            print(json.dumps({'segment':segment['id'],'similarity':round(similarity,4)}),flush=True)
    if '--transcribe-only' in sys.argv:
        return
    edit = json.loads((OUT/'edit-receipt.json').read_text())
    cues = []
    for part in edit['segments']:
        words = json.loads((OUT/'speech-checks'/(part['id']+'.json')).read_text())['results']['channels'][0]['alternatives'][0]['words']
        offset = part['start_seconds']+part['narration_delay_seconds']
        current = []
        for word in words:
            current.append(word)
            text = ' '.join(w.get('punctuated_word',w['word']) for w in current)
            if len(current)>=9 or len(text)>67 or current[-1]['end']-current[0]['start']>4.1 or text.endswith(('.','?','!')):
                cues.append((offset,current));current=[]
        if current:cues.append((offset,current))
    subs=[]
    for index,(offset,words) in enumerate(cues):
        text=' '.join(w.get('punctuated_word',w['word']) for w in words)
        for a,b in [('Decision Debt','DecisionDebt'),('decision debt','DecisionDebt'),('Deep Gram','Deepgram'),
                    ('off gateway','Auth Gateway'),('Directory sync','Directory Sync')]:
            text=text.replace(a,b)
        end=offset+words[-1]['end']+.08
        if index+1<len(cues):end=min(end,cues[index+1][0]+cues[index+1][1][0]['start']-.01)
        assert end<edit['duration_seconds'], 'Caption exceeds video'
        subs.append(f'{index+1}\n{timestamp(offset+words[0]["start"])} --> {timestamp(end)}\n'+textwrap.fill(text,width=44)+'\n')
    (OUT/'captions.en.srt').write_text('\n'.join(subs).rstrip()+'\n')
    unsupported = next(c for c in checks if c['id']=='04-unsupported')['transcript'].lower()
    ending = next(c for c in checks if c['id']=='05-ticket')['transcript'].lower()
    validations = {
        'source_audio_hashes_match':all(c['hash_matches_narration'] for c in checks),
        'script_transcript_similarity_above_point_nine':all(c['script_transcript_similarity']>.9 for c in checks),
        'unsupported_no_query_negation_present':'no query' in unsupported,
        'ending_discloses_voice_provider':'deepgram' in normalize(ending),
        'public_no_model_statement_present':'no model' in ending,
    }
    receipt={'checked_at':datetime.now(timezone.utc).isoformat(),'provider':'Deepgram','asr_model':'nova-3',
        'method':'Per-segment recognition of actual narration audio; source hashes verified, real word times shifted onto edited clips',
        'checks':validations,'passed':all(validations.values()),'caption_cues':len(cues),
        'caption_text_changes':'Brand orthography only, including Auth Gateway misrecognized as off gateway; raw provider transcripts retained.',
        'source_transcriptions':checks}
    (OUT/'speech-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if not receipt['passed']:raise SystemExit('Speech verification requires inspection')


if __name__ == '__main__':
    main()
