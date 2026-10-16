"""Edit continuous 4K browser video with close-ups and separately generated narration.

Consumes capture-receipt.json and deepgram-receipt.json in a new output directory.
No screenshot is used as video input, and the original capture is preserved.
"""

import argparse
import hashlib
import json
import math
import subprocess
import wave
from datetime import datetime
from pathlib import Path


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)
    ]))


def expression(knots, component):
    result = f"{knots[-1][component]:.6f}"
    for a, b in reversed(list(zip(knots, knots[1:]))):
        if b[0] <= a[0]:
            continue
        # Cosine ease between camera keyframes; holds use identical values.
        t = f"(1-cos(PI*(on/{30}-{a[0]:.6f})/{b[0]-a[0]:.6f}))/2"
        value = f"{a[component]:.6f}+({b[component]-a[component]:.6f})*({t})"
        result = f"if(lt(on/{30},{b[0]:.6f}),{value},{result})"
    return result


def camera(actions, start, end):
    knots = [[0.0, 1.0, 1920.0, 1080.0]]
    for action in actions:
        if action.get("action") != "editorial_focus" or not action.get("box"):
            continue
        when = action["capture_seconds"]
        if not start <= when < end:
            continue
        box = action["box"]
        x, y, width, height = (box[k] for k in ("x", "y", "width", "height"))
        if height > 1900:
            height = 1600
        if "owner" in action["label"] and width < 1500:
            y += height * 0.25
            height *= 0.7
        frame_width = max(width * 1.17, height * 1.17 * 16 / 9)
        zoom = max(1.0, min(1.9, 3840 / max(frame_width, 1)))
        cx, cy = x + width / 2, y + height / 2
        half_w, half_h = 1920 / zoom, 1080 / zoom
        cx = max(half_w, min(3840 - half_w, cx))
        cy = max(half_h, min(2160 - half_h, cy))
        t = max(knots[-1][0], when - start)
        if t > knots[-1][0]:
            knots.append([t, *knots[-1][1:]])
        finish = min(t + 1.3, end - start)
        if finish > t:
            knots.append([finish, zoom, cx, cy])
    return knots


def run(command, log):
    with log.open("w") as output:
        subprocess.run(command, stdout=output, stderr=output, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("evidence/demo-v3"))
    parser.add_argument("--work", type=Path, default=Path("work/demo-4k/render"))
    args = parser.parse_args()
    directory, scratch = args.directory, args.work
    scratch.mkdir(parents=True, exist_ok=True)
    capture = json.loads((directory / "capture-receipt.json").read_text())
    speech = json.loads((directory / "deepgram-receipt.json").read_text())
    assert capture["passed"] and not capture["screenshots_used_as_video"]
    source = Path(capture["raw_video_path"])
    metadata = probe(source)
    stream = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    assert (stream["width"], stream["height"]) == (3840, 2160)
    created = metadata["format"].get("tags", {}).get("creation_time")
    if not created:
        raise RuntimeError("Native recording is missing its wall-clock creation timestamp")
    epoch = datetime.fromisoformat(capture["page_created_at"].replace("Z", "+00:00")).timestamp()
    source_epoch = datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp()
    offset = epoch - source_epoch
    edit = {
        "format": "Edited continuous native 4K Chromium compositor recording",
        "source": str(source), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_metadata": metadata, "wall_clock_offset_seconds": offset,
        "output_size": [3840, 2160], "fps": 30,
        "screenshots_used_as_video": False,
        "closeups": "Digital reframing of live video frames captured at native 3840x2160; no still-image montage",
        "omitted": "Initial load and private local-admin setup; chronological application actions otherwise retained",
        "segments": [],
    }
    total = 0.0
    for index, scene in enumerate(capture["scenes"]):
        start = scene["capture_seconds"]
        end = capture["scenes"][index+1]["capture_seconds"] if index+1 < len(capture["scenes"]) else scene["end_capture_seconds"]
        if scene["id"] == "06-agent":
            end = capture["private_auth_start"]["capture_seconds"]
        frames = math.floor((end - start) * 30)
        duration = frames / 30
        audio = next(s for s in speech["segments"] if s["id"] == scene["id"])
        assert duration > audio["duration_seconds"] + 0.25
        knots = camera(capture["actions"], start, end)
        z, cx, cy = (expression(knots, i) for i in (1, 2, 3))
        vf = f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,({cx})-iw/zoom/2))':y='max(0,min(ih-ih/zoom,({cy})-ih/zoom/2))':d=1:s=3840x2160:fps=30,setsar=1,format=yuv420p"
        target = scratch / (scene["id"] + ".mp4")
        command = ["ffmpeg", "-hide_banner", "-nostdin", "-n", "-ss", f"{start+offset:.6f}", "-i", str(source), "-an", "-vf", vf, "-frames:v", str(frames), "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-threads", "4", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", str(target)]
        run(command, scratch / (scene["id"] + ".log"))
        item = {"id": scene["id"], "chapter":scene["chapter"], "source_start_seconds": start+offset, "source_end_seconds": start+offset+duration, "start_seconds":total, "duration_seconds":duration, "frames":frames, "camera_keyframes":knots, "narration_file":audio["path"], "narration_delay_seconds":0.25, "rendered_clip":str(target)}
        edit["segments"].append(item)
        total += duration
        (directory / "edit-receipt.json").write_text(json.dumps(edit, indent=2) + "\n")
        print(json.dumps({"rendered":scene["id"], "duration_seconds":duration, "timeline_seconds":total}), flush=True)

    with wave.open(str(directory / "narration.wav"), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(48000)
        for segment in edit["segments"]:
            size = round(segment["duration_seconds"] * 48000)
            lead = 12000
            with wave.open(segment["narration_file"], "rb") as audio:
                assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1,2,48000)
                data = audio.readframes(audio.getnframes())
            tail = size - lead - len(data)//2
            assert tail >= 0
            output.writeframes(b"\0" * lead * 2 + data + b"\0" * tail * 2)

    listing = scratch / "concat.txt"
    listing.write_text("".join("file '" + str(Path(s["rendered_clip"]).resolve()) + "'\n" for s in edit["segments"]))
    final = directory / "decisiondebt-demo-4k-narrated.mp4"
    run(["ffmpeg", "-hide_banner", "-nostdin", "-n", "-f", "concat", "-safe", "0", "-i", str(listing), "-i", str(directory / "narration.wav"), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-metadata:s:a:0", "language=eng", "-movflags", "+faststart", "-shortest", str(final)], scratch / "final-mux.log")
    edit["output"] = str(final)
    edit["duration_seconds"] = total
    edit["sha256"] = hashlib.sha256(final.read_bytes()).hexdigest()
    edit["output_metadata"] = probe(final)
    (directory / "edit-receipt.json").write_text(json.dumps(edit, indent=2) + "\n")
    print(json.dumps({"complete":True, "file":str(final), "duration_seconds":total, "bytes":final.stat().st_size}), flush=True)


if __name__ == "__main__":
    main()
