"""Cut excess chapter holds while preserving complete Deepgram speech, below 180s."""
import hashlib
import json
import subprocess
import wave
from datetime import datetime, timezone
from pathlib import Path
import finalize_demo_4k as captions

OUT = Path('evidence/demo-v3')
WORK = Path('work/demo-4k/under3')
WORK.mkdir(parents=True, exist_ok=True)

def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))

def run(args, name):
    with (WORK / (name + '.log')).open('w') as log:
        subprocess.run(['ffmpeg','-hide_banner','-nostdin','-n',*args],stdout=log,stderr=log,check=True)

def main():
    edit=json.loads((OUT/'edit-receipt.json').read_text())
    closing=json.loads((OUT/'closing-narration-receipt.json').read_text())
    source_speech=json.loads((OUT/'speech-verification-source.json').read_text())
    assert source_speech['passed']
    limits=[11,17.3,16.3,13.2,17.5,16,17,18.9,16.5,17,10.1,5.8]
    segments=[*edit['segments'],{'id':'12-closing','chapter':'Company Brain / Deepgram','rendered_clip':'work/demo-4k/render/12-closing.mp4','narration_file':closing['path']}]
    total=0
    parts=[]
    for segment, limit in zip(segments,limits):
        path=WORK/(segment['id']+'.mp4')
        # Every clip starts at its original IDR; only its tail is shortened.
        # The separate original narration is remuxed below without any speed change.
        if not path.exists():run(['-i',segment['rendered_clip'],'-map','0:v:0','-an','-t',str(limit),'-c:v','copy','-avoid_negative_ts','make_zero',str(path)],segment['id'])
        meta=probe(path)
        video=next(s for s in meta['streams'] if s['codec_type']=='video')
        # Stream-copy preserves B-frame decode lead; concat uses container duration.
        duration=float(meta['format']['duration'])
        with wave.open(segment['narration_file'],'rb') as wav:
            voice_duration=len(wav.readframes(wav.getnframes()))/(wav.getframerate()*wav.getsampwidth()*wav.getnchannels())
        assert voice_duration+.25 < duration
        parts.append({'id':segment['id'],'chapter':segment['chapter'],'source_clip':segment['rendered_clip'],'clip':str(path),'source_start_seconds':0,'start_seconds':total,'duration_seconds':duration,'narration_file':segment['narration_file'],'narration_delay_seconds':.25,'voice_duration_seconds':voice_duration,'clip_metadata':meta})
        total+=duration
    assert total<179, total
    narration=WORK/'narration.wav'
    with wave.open(str(narration),'wb') as out:
        out.setnchannels(1);out.setsampwidth(2);out.setframerate(48000)
        for p in parts:
            with wave.open(p['narration_file'],'rb') as w:
                assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,48000)
                data=w.readframes(w.getnframes())
            lead=12000;tail=round(p['duration_seconds']*48000)-lead-len(data)//2
            assert tail>=0
            out.writeframes(b'\0'*lead*2+data+b'\0'*tail*2)
    listing=WORK/'concat.txt'
    listing.write_text(''.join("file '"+str(Path(p['clip']).resolve())+"'\n" for p in parts))
    final=OUT/'decisiondebt-demo-4k-under3.mp4'
    run(['-f','concat','-safe','0','-i',str(listing),'-i',str(narration),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:a','aac','-b:a','192k','-ar','48000','-metadata:s:a:0','language=eng','-t',str(total),'-movflags','+faststart',str(final)],'mux')
    metadata=probe(final)
    assert float(metadata['format']['duration'])<180
    receipt={'created_at':datetime.now(timezone.utc).isoformat(),'format':'Under-three-minute edit of continuous native 3840x2160 Chromium compositor footage, with digital close-ups and complete Deepgram narration','reason':'User requested a cut under three minutes; official linked rules require a working demo but do not specify a duration cap','official_rules':'https://www.wemakedevs.org/hackathons/falkordb/rules','screenshots_used_as_video':False,'speech_speed_multiplier':1,'edits':'Removed trailing chapter holds and the navigation after the query chapter. All twelve narration takes remain complete. Chronological hard cuts between chapters.','source_capture_receipt':str(OUT/'capture-receipt.json'),'closeup_edit_receipt':str(OUT/'edit-receipt.json'),'segments':parts,'final_file':str(final),'metadata':metadata,'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'duration_seconds':float(metadata['format']['duration'])}
    (OUT/'under3-edit-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    cues=[]
    speech_parts=[]
    for part in parts:
        source=next(s for s in source_speech['source_transcriptions'] if s['id']==part['id'])
        assert hashlib.sha256(Path(part['narration_file']).read_bytes()).hexdigest()==source['audio_sha256']
        raw=json.loads((OUT/'speech-checks'/(part['id']+'.json')).read_text())
        words=raw['results']['channels'][0]['alternatives'][0]['words']
        offset=part['start_seconds']+.25
        current=[]
        for word in words:
            current.append(word)
            text=' '.join(w.get('punctuated_word',w['word']) for w in current)
            if len(current)>=9 or len(text)>67 or current[-1]['end']-current[0]['start']>4.1 or text.endswith(('.','?','!')):
                cues.append((offset,current));current=[]
        if current:cues.append((offset,current))
        speech_parts.append({**source,'start_seconds':offset})
    import textwrap
    subs=[]
    for i,(offset,words) in enumerate(cues):
        text=' '.join(w.get('punctuated_word',w['word']) for w in words)
        for old,new in [('Decision Debt','DecisionDebt'),('decision debt','DecisionDebt'),('Falkor DB','FalkorDB'),('Orion Auth','OrionAuth'),('Nova ID','NovaID'),('Deep Gram','Deepgram'),('AsterWORKS','Aster Works'),('Zokin Cache','Token Cache'),('billing a p one','Billing API')]:text=text.replace(old,new)
        end=offset+words[-1]['end']+.08
        if i+1<len(cues):end=min(end,cues[i+1][0]+cues[i+1][1][0]['start']-.01)
        assert end < float(metadata['format']['duration'])
        subs.append(f'{i+1}\n{captions.timestamp(offset+words[0]["start"])} --> {captions.timestamp(end)}\n'+textwrap.fill(text,width=44)+'\n')
    (OUT/'captions-under3.en.srt').write_text('\n'.join(subs)+'\n')
    speech={'checked_at':datetime.now(timezone.utc).isoformat(),'provider':'Deepgram','model':'nova-3','method':'Exact source narration SHA-256 verification and previously verified per-segment ASR word times shifted onto actual shortened clip durations','checks':{**source_speech['checks'],'all_source_audio_hashes_match':True,'all_twelve_takes_complete':True,'speech_playback_speed_unchanged':True},'passed':True,'caption_cues':len(cues),'source_transcriptions':speech_parts}
    (OUT/'speech-verification-under3.json').write_text(json.dumps(speech,indent=2)+'\n')
    print(json.dumps({'file':str(final),'duration_seconds':receipt['duration_seconds'],'timeline_seconds':total,'caption_cues':len(cues),'chapters':[{k:p[k] for k in ('id','start_seconds','duration_seconds')} for p in parts]}))

if __name__=='__main__':main()
