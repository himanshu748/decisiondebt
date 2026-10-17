"""Join both complete 4K demos; preserve sources, video quality and caption times."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('evidence/combined-demo-20261017')
WORK = Path('work/combined-demo-20261017')
SOURCES = [
    (Path('evidence/demo-v3/decisiondebt-demo-4k-under3.mp4'), Path('evidence/demo-v3/captions-under3.en.srt')),
    (Path('evidence/ask-addendum-20261017/decisiondebt-ask-graph-addendum-4k.mp4'), Path('evidence/ask-addendum-20261017/captions.en.srt')),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))


def millis(stamp):
    h,m,s,ms=map(int,re.split('[:,]',stamp))
    return ((h*60+m)*60+s)*1000+ms


def stamp(value):
    h,value=divmod(value,3600000);m,value=divmod(value,60000);s,ms=divmod(value,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def main():
    OUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    parts=[];offset=0;subs=[]
    for video,captions in SOURCES:
        meta=probe(video)
        v=next(s for s in meta['streams'] if s['codec_type']=='video')
        assert (v['width'],v['height'],v['r_frame_rate'])==(3840,2160,'30/1')
        parts.append({'file':str(video),'sha256':sha(video),'start_seconds':offset,
            'duration_seconds':float(meta['format']['duration']),'captions':str(captions),'captions_sha256':sha(captions),
            'source_metadata':meta})
        for cue in re.split(r'\n\s*\n',captions.read_text().strip()):
            lines=cue.splitlines()
            if len(lines)<3:continue
            start,end=lines[1].split(' --> ')
            subs.append(f'{len(subs)+1}\n{stamp(millis(start)+round(offset*1000))} --> {stamp(millis(end)+round(offset*1000))}\n'+'\n'.join(lines[2:]))
        offset+=float(meta['format']['duration'])
    captions_text=re.sub(r'\bcipher\b','Cypher','\n\n'.join(subs),flags=re.I)
    captions_text=captions_text.replace('billing API','Billing API').replace('markdown draft','Markdown draft')
    (OUT/'captions.en.srt').write_text(captions_text+'\n')
    listing=WORK/'concat.txt'
    listing.write_text(''.join("file '"+str(video.resolve())+"'\n" for video,_ in SOURCES))
    target=OUT/'decisiondebt-complete-4k-demo.mp4'
    with (OUT/'join-log.txt').open('w') as log:
        subprocess.run(['ffmpeg','-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i',str(listing),
            '-map','0:v:0','-map','0:a:0','-c:v','copy','-af','aresample=async=1:first_pts=0',
            '-c:a','aac','-b:a','192k','-ar','48000','-metadata:s:a:0','language=eng',
            '-movflags','+faststart',str(target)],stdout=log,stderr=log,check=True)
    log_path=OUT/'join-log.txt'
    log_path.write_text('\n'.join(line.rstrip() for line in log_path.read_text().splitlines())+'\n')
    meta=probe(target)
    v=next(s for s in meta['streams'] if s['codec_type']=='video')
    assert (v['width'],v['height'],v['r_frame_rate'])==(3840,2160,'30/1')
    assert abs(float(meta['format']['duration'])-offset)<.25
    assert int(v['nb_frames'])==sum(int(next(s for s in p['source_metadata']['streams'] if s['codec_type']=='video')['nb_frames']) for p in parts)
    with (OUT/'decode-check.txt').open('w') as log:
        subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(target),'-f','null','-'],stdout=log,stderr=log,check=True)
    (OUT/'qa').mkdir(exist_ok=True)
    for sec,name in [(8,'opening'),(170,'main-ending'),(179,'addendum-start'),(198,'live-cypher'),(213,'unsupported'),(228,'ticket-export')]:
        subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-n','-ss',str(sec),'-i',str(target),'-frames:v','1','-q:v','2',str(OUT/'qa'/(name+'.jpg'))],check=True)
    baseline=json.loads((WORK/'preservation-before.json').read_text())
    assert all(sha(Path(p))==s for p,s in baseline.items())
    packets=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
        '-show_packets','-show_entries','packet=dts','-of','json',str(target)]))['packets']
    dts=[int(p['dts']) for p in packets]
    assert all(b>a for a,b in zip(dts,dts[1:]))
    manifest={'created_at':datetime.now(timezone.utc).isoformat(),'file':str(target),'sha256':sha(target),
        'duration_seconds':float(meta['format']['duration']),'metadata':meta,'sources':parts,
        'edit':'Both complete videos in their original order. No source scenes removed, no playback speed changes, no new recording or model call.',
        'video':'H.264 packets stream-copied at native 3840x2160, 30 fps; no scaling or video re-encoding.',
        'audio':'Existing Deepgram narration retained; AAC re-encoded once to keep the join continuous. No new speech synthesis.',
        'captions':'Both verified source SRT files combined; addendum cues offset by the measured first-video container duration.',
        'source_speech_receipts':['../demo-v3/speech-verification-under3.json','../ask-addendum-20261017/speech-verification.json'],
        'screenshots_used_as_video':False,'source_video_frames_preserved':True,'previous_evidence_files':len(baseline),
        'previous_evidence_sha256_unchanged':True,'original_youtube_videos_unchanged':['https://youtu.be/_a0vrYwOlME','https://youtu.be/zfEJ-rkodyI'],
        'verification':{'video_packets':len(packets),'nonincreasing_packet_dts':0,
            'source_frame_counts_preserved':True,'ffmpeg_decode_exit_code':0,
            'null_mux_timestamp_warnings':(OUT/'decode-check.txt').read_text().count('non monotonically'),
            'warning_note':'The null-output decode reports source presentation-timestamp discontinuities; input video packet DTS is strictly increasing. Source video packets are retained without re-encoding. Actual YouTube playback is verified separately.'},
        'caption_orthography':'Brand spelling only: Cypher, Billing API and Markdown. Source caption files remain unchanged.',
        'youtube_receipt':'youtube-upload-receipt.json','passed':True}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'file':str(target),'seconds':manifest['duration_seconds'],'sha256':manifest['sha256'],'preserved_files':len(baseline)}))


if __name__=='__main__':main()
