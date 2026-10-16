"""Append the separately captured closing take and place verified word-timed captions."""

import hashlib
import json
import re
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("evidence/demo-v3")
WORK = Path("work/demo-4k/render")


def run(args, log):
    with (WORK / log).open("w") as output:
        subprocess.run(args, stdout=output, stderr=output, check=True)


def timestamp(value):
    value = round(value * 1000)
    hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000)
    seconds, millis = divmod(value, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def main():
    edit = json.loads((OUT / "edit-receipt.json").read_text())
    main_duration = float(edit["output_metadata"]["format"]["duration"])
    closing = json.loads((OUT / "closing-take-source.json").read_text())
    voice = json.loads((OUT / "closing-narration-receipt.json").read_text())
    source_speech = json.loads((OUT / "speech-verification-source.json").read_text())
    assert source_speech["passed"]
    duration = closing["duration_seconds"]
    clip = WORK / "12-closing.mp4"
    run([
        "ffmpeg", "-hide_banner", "-nostdin", "-n", "-ss", str(closing["source_offset_seconds"]),
        "-i", closing["raw_video"], "-i", voice["path"], "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "zoompan=z='1+min(on/180,1)*0.06':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=3840x2160:fps=30,setsar=1,format=yuv420p",
        "-frames:v", str(round(duration * 30)), "-c:v", "libx264", "-crf", "18", "-preset", "fast", "-threads", "4", "-r", "30",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-af", f"adelay=250,loudnorm=I=-16:TP=-1.5:LRA=11,apad=whole_dur={duration}",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-metadata:s:a:0", "language=eng", "-t", str(duration), "-movflags", "+faststart", str(clip),
    ], "closing-render.log")
    listing = WORK / "final-concat.txt"
    listing.write_text("".join("file '" + str(Path(p).resolve()) + "'\n" for p in (edit["output"], str(clip))))
    final = OUT / "decisiondebt-demo-4k-final.mp4"
    run(["ffmpeg", "-hide_banner", "-nostdin", "-n", "-f", "concat", "-safe", "0", "-i", str(listing), "-map", "0:v:0", "-map", "0:a:0", "-c", "copy", "-movflags", "+faststart", str(final)], "final-concat.log")
    metadata = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(final)]))
    receipt = {"format": "Continuous native 4K Chromium browser recording edited with close-ups, followed by a separately captured live closing take", "source_main": edit["source"], "main_edit_receipt": str(OUT / "edit-receipt.json"), "closing_take": closing, "closing_start_seconds": main_duration, "requested_main_duration_seconds": edit["duration_seconds"], "source_screenshots_used_as_video": False, "final_file": str(final), "sha256": hashlib.sha256(final.read_bytes()).hexdigest(), "metadata": metadata}
    (OUT / "final-edit-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")

    parts = [{"id": s["id"], "path": s["narration_file"], "start_seconds": s["start_seconds"] + 0.25} for s in edit["segments"]]
    parts.append({"id": "12-closing", "path": voice["path"], "start_seconds": main_duration + 0.25})
    cues = []
    for part in parts:
        source = next(p for p in source_speech["source_transcriptions"] if p["id"] == part["id"])
        assert hashlib.sha256(Path(part["path"]).read_bytes()).hexdigest() == source["audio_sha256"]
        raw = json.loads((OUT / "speech-checks" / (part["id"] + ".json")).read_text())
        words = raw["results"]["channels"][0]["alternatives"][0]["words"]
        current = []
        for word in words:
            current.append(word)
            text = " ".join(w.get("punctuated_word", w["word"]) for w in current)
            if len(current) >= 9 or len(text) > 67 or current[-1]["end"] - current[0]["start"] > 4.1 or text.endswith((".", "?", "!")):
                cues.append((part["start_seconds"], current)); current = []
        if current:
            cues.append((part["start_seconds"], current))
        part.update({"audio_sha256": source["audio_sha256"], "request_id": source["request_id"], "transcript": source["transcript"]})
    subtitles = []
    for index, (offset, words) in enumerate(cues, 1):
        text = " ".join(w.get("punctuated_word", w["word"]) for w in words)
        for old, new in [("Decision Debt", "DecisionDebt"), ("decision debt", "DecisionDebt"), ("Falkor DB", "FalkorDB"), ("Orion Auth", "OrionAuth"), ("Nova ID", "NovaID"), ("Deep Gram", "Deepgram"), ("AsterWORKS", "Aster Works"), ("Zokin Cache", "Token Cache"), ("billing a p one", "Billing API")]:
            text = text.replace(old, new)
        end = offset + words[-1]["end"] + 0.08
        if index < len(cues):
            next_offset, next_words = cues[index]
            end = min(end, next_offset + next_words[0]["start"] - 0.01)
        subtitles.append(f"{index}\n{timestamp(offset + words[0]['start'])} --> {timestamp(end)}\n" + textwrap.fill(text, width=44) + "\n")
    (OUT / "captions-final.en.srt").write_text("\n".join(subtitles) + "\n")
    speech = {"checked_at": datetime.now(timezone.utc).isoformat(), "provider": "Deepgram", "model": "nova-3", "method": "Reused verified per-segment word timestamps only after checking each narration file's exact SHA-256; shifted onto the new actual edit timeline", "checks": {**source_speech["checks"], "all_source_audio_hashes_match": True}, "passed": True, "caption_cues": len(cues), "source_transcriptions": parts}
    (OUT / "speech-verification-final.json").write_text(json.dumps(speech, indent=2) + "\n")
    print(json.dumps({"complete": True, "file": str(final), "duration_seconds": metadata["format"]["duration"], "bytes": final.stat().st_size, "caption_cues": len(cues)}))


if __name__ == "__main__":
    main()
