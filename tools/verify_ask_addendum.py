"""Check the new addendum without rewriting any pre-existing evidence."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('evidence/ask-addendum-20261017')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    capture = json.loads((OUT/'capture-receipt.json').read_text())
    speech = json.loads((OUT/'speech-verification.json').read_text())
    edit = json.loads((OUT/'edit-receipt.json').read_text())
    video = OUT/'decisiondebt-ask-graph-addendum-4k.mp4'
    source = Path(edit['output'])
    if source != video:
        assert not video.exists()
        source.rename(video)
    # This new receipt uses the shared demo-v3 renderer, but this capture has no
    # private/local-admin setup. State the omissions specific to this public take.
    edit['output'] = str(video)
    edit['omitted'] = 'Initial page load; chronological public question and export scenes are retained.'
    edit['public_readonly_capture'] = True
    (OUT/'edit-receipt.json').write_text(json.dumps(edit,indent=2)+'\n')
    metadata = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)]))
    v = next(s for s in metadata['streams'] if s['codec_type']=='video')
    a = next(s for s in metadata['streams'] if s['codec_type']=='audio')
    assert 45 <= float(metadata['format']['duration']) <= 60
    assert (v['width'],v['height'],v['r_frame_rate']) == (3840,2160,'30/1')
    assert a['codec_name']=='aac' and capture['passed'] and speech['passed']
    assert not capture['screenshots_used_as_video']
    assert capture['health_before']['graph_revision']==capture['health_after']['graph_revision']==16
    assert all(r['method']=='GET' and r['status']==200 for r in capture['requests'])
    answers = capture['answers']
    assert [a['status'] for a in answers]==['answered','answered','ambiguous','unsupported']
    assert answers[0]['row_count']==1 and answers[1]['row_count']==12
    assert answers[1]['counts']=={'services':12,'projects':12}
    assert any(s['name']=='Directory Sync' and s['depth']==6 for s in answers[1]['truncation_examples'])
    assert not answers[3]['query_trace']
    assert any(s['name']=='Billing API' for s in answers[2]['suggestions'])
    with (OUT/'decode-check.txt').open('w') as log:
        subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(video),'-f','null','-'],stdout=log,stderr=log,check=True)
    (OUT/'qa').mkdir(exist_ok=True)
    for sec,name in [(9,'owner-cypher'),(11,'owner-executed-cypher'),(21,'impact-cypher'),(31,'typo-suggestion'),(39,'unsupported'),(51,'markdown-ticket')]:
        target=OUT/'qa'/(name+'.jpg')
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n','-ss',str(sec),'-i',str(video),'-frames:v','1','-q:v','2',str(target)],check=True)
    before = json.loads(Path('work/ask-addendum-20261017/preservation-before.json').read_text())
    assert all(Path(name).exists() and sha(Path(name))==digest for name,digest in before.items())
    (OUT/'preservation.json').write_text(json.dumps({'checked_at':datetime.now(timezone.utc).isoformat(),
        'scope':'All pre-existing evidence/media files except the ignored actively written test server log',
        'unchanged_files':len(before),'sha256':before,'passed':True},indent=2)+'\n')
    manifest = {'created_at':datetime.now(timezone.utc).isoformat(),'base_commit':'fbca13e25781403296067fb6724356443f3da09c',
        'branch':'codex/ask-graph-video-addendum','live_url':capture['source_url'],'graph_revision':16,
        'pipeline':{'source':'Continuous native Chromium compositor capture; 3840x2160, 30 fps',
            'same_pipeline_as':'evidence/demo-v3','capture_tool':'tools/record_ask_addendum.cjs',
            'renderer':'tools/render_recorded_demo.py','narration_tool':'tools/narrate_ask_addendum.py',
            'voice':'Deepgram aura-2-thalia-en','recognition':'Deepgram nova-3',
            'screenshots_used_as_video':False,'speech_speed_multiplier':1},
        'file':str(video),'sha256':sha(video),'metadata':metadata,'duration_seconds':float(metadata['format']['duration']),
        'recording_actor':'Codex automation, not participant personal verification',
        'public_app_llm_calls':0,'public_app_requests':'GET only; Markdown exported client-side',
        'old_main_video':'https://youtu.be/_a0vrYwOlME','old_main_video_modified':False,
        'answers':[{'question':a['question'],'status':a['status'],'rows':a['row_count'],'query_ms':a['query_ms']} for a in answers],
        'chapters':[{'id':s['id'],'title':s['chapter'],'start_seconds':s['start_seconds'],'duration_seconds':s['duration_seconds']} for s in edit['segments']],
        'capture_receipt':'capture-receipt.json','edit_receipt':'edit-receipt.json','speech_receipt':'speech-verification.json',
        'captions':'captions.en.srt','ticket_export':capture['export'],'preservation_receipt':'preservation.json',
        'youtube_receipt':'youtube-upload-receipt.json','passed':True}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'file':str(video),'seconds':manifest['duration_seconds'],'sha256':manifest['sha256'],'prior_files_unchanged':len(before)}))


if __name__=='__main__':
    main()
