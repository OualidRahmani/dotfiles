#!/usr/bin/env python3
"""wallman — Wallpaper manager for per-workspace animated wallpapers."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

WORKSHOP_DIR = Path.home() / ".local/share/Steam/steamapps/workshop/content/431960"
VIDEOS_DIR   = Path.home() / "Videos"
REALESRGAN   = Path.home() / "Downloads/realesrgan/realesrgan-ncnn-vulkan"
TARGET_W, TARGET_H = 1920, 1080

SUPPORTED_EXTS = {".mp4", ".webm", ".jpg", ".jpeg", ".png", ".mkv", ".mov"}
SKIP_TYPES     = {"scene", "web", "application"}
CACHE_FILE     = VIDEOS_DIR / ".wallman_cache.json"

# ── Wallpaper discovery ───────────────────────────────────────────────────────

def get_videos():
    wallpapers = []
    for folder in WORKSHOP_DIR.iterdir():
        if not folder.is_dir():
            continue
        title = folder.name
        project = folder / "project.json"
        if project.exists():
            try:
                data = json.loads(project.read_text(encoding="utf-8"))
                title = data.get("title", folder.name)
                if data.get("type", "").lower() in SKIP_TYPES:
                    continue
            except Exception:
                pass
        for file in folder.iterdir():
            if file.suffix.lower() in SUPPORTED_EXTS:
                wallpapers.append((title, file))
                break
    return sorted(wallpapers, key=lambda x: x[0].lower())

# ── Current assignment ────────────────────────────────────────────────────────

def get_current_wallpaper(workspace):
    matches = list(VIDEOS_DIR.glob(f"current-wallpaper-{workspace + 1}.*"))
    if not matches:
        return None
    path = matches[0]
    return path.resolve().name if path.is_symlink() else path.name

def show_status():
    print("\nCurrent wallpaper assignments:\n")
    found = False
    for i in range(1, 10):
        matches = list(VIDEOS_DIR.glob(f"current-wallpaper-{i}.*"))
        if matches:
            path = matches[0]
            name = path.resolve().name if path.is_symlink() else path.name
            print(f"  Workspace {i}: {name}")
            found = True
    if not found:
        print("  No wallpapers assigned.")
    print()

# ── Preview ───────────────────────────────────────────────────────────────────

def preview(video):
    proc = subprocess.Popen(["mpv", "--no-audio", "--length=5", str(video)])
    print("Previewing... (press q to skip)")
    proc.wait()

# ── Resolution helpers ────────────────────────────────────────────────────────

def get_resolution(video):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True,
    )
    parts = result.stdout.strip().split(",")
    if len(parts) == 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return None, None

def get_fps(video):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True,
    )
    fps = result.stdout.strip() or "25"
    if "/" in fps:
        num, den = fps.split("/")
        fps = str(round(int(num) / int(den)))
    return fps

# ── Upscaling ─────────────────────────────────────────────────────────────────

def upscale(video, workspace):
    w, h = get_resolution(video)
    if w is None:
        print("Could not determine resolution, skipping upscale.")
        return video

    if w >= TARGET_W and h >= TARGET_H:
        print(f"Already {w}x{h}, no upscale needed.")
        return video

    print(f"Source is {w}x{h}, upscaling to {TARGET_W}x{TARGET_H}...")

    scale_needed = max(TARGET_W / w, TARGET_H / h)
    if scale_needed <= 2:
        model, scale_flag = "realesr-animevideov3-x2", "2"
    elif scale_needed <= 3:
        model, scale_flag = "realesr-animevideov3-x3", "3"
    else:
        model, scale_flag = "realesr-animevideov3-x4", "4"

    tmp         = Path(tempfile.mkdtemp())
    frames_dir  = tmp / "frames"
    upscaled_dir = tmp / "upscaled"
    frames_dir.mkdir()
    upscaled_dir.mkdir()
    output = VIDEOS_DIR / f"wallpaper-ws{workspace + 1}-upscaled.mp4"

    try:
        print("Extracting frames...")
        subprocess.run(
            ["ffmpeg", "-i", str(video), str(frames_dir / "frame%04d.png")],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        print(f"Upscaling with {model}...")
        subprocess.run(
            [str(REALESRGAN), "-i", str(frames_dir), "-o", str(upscaled_dir),
             "-n", model, "-s", scale_flag],
            check=True,
        )

        print("Assembling final video...")
        subprocess.run(
            ["ffmpeg", "-y", "-framerate", get_fps(video),
             "-i", str(upscaled_dir / "frame%04d.png"),
             "-vf", f"scale={TARGET_W}:{TARGET_H}:flags=lanczos",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-threads", "0",
             str(output)],
            check=True, stdin=subprocess.DEVNULL,
        )
        print(f"Done: {output.name}")
        return output

    except subprocess.CalledProcessError as e:
        print(f"Upscale failed: {e}. Using original.")
        if output.exists():
            output.unlink()
        return video
    finally:
        shutil.rmtree(tmp)

# ── Cache ─────────────────────────────────────────────────────────────────────

def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            pass
    return {}

def save_cache(cache):
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        print(f"Warning: could not save cache: {e}")

def upscale_with_cache(video, workspace, cache):
    key = str(video.resolve())
    if key in cache:
        cached = Path(cache[key])
        if cached.exists():
            print(f"Using cached version: {cached.name}")
            return cached
        del cache[key]

    result = upscale(video, workspace)
    if result != video:
        cache[key] = str(result)
        save_cache(cache)
    return result

# ── Assignment ────────────────────────────────────────────────────────────────

def assign(video, workspace):
    ext    = video.suffix.lower()
    target = VIDEOS_DIR / f"current-wallpaper-{workspace + 1}{ext}"

    for old in VIDEOS_DIR.glob(f"current-wallpaper-{workspace + 1}.*"):
        old.unlink()

    os.symlink(video, target)
    print(f"Assigned to workspace {workspace + 1}")

    subprocess.run(
        [str(Path.home() / ".local/bin/restart-wallpaper")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

# ── Fastfetch image ───────────────────────────────────────────────────────────

def assign_to_fetch(image_path):
    target_dir  = Path.home() / "Pictures/fastfetch"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_link = target_dir / "current_fetch.jpg"
    if target_link.exists():
        target_link.unlink()
    os.symlink(image_path, target_link)
    print(f"Terminal image assigned: {image_path.name}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--status":
        show_status()
        sys.exit(0)

    if len(sys.argv) != 2:
        print("Usage: wallman <workspace-number>")
        print("       wallman --status")
        sys.exit(1)

    try:
        workspace = int(sys.argv[1]) - 1
        if workspace < 0:
            raise ValueError
    except ValueError:
        print("Workspace must be a positive integer.")
        sys.exit(1)

    wallpapers = get_videos()
    if not wallpapers:
        print("No video wallpapers found.")
        sys.exit(1)

    cache = load_cache()

    while True:
        current = get_current_wallpaper(workspace)
        print(f"\nWorkspace {workspace + 1} currently: {current or '(none)'}")
        print("\nAvailable wallpapers:\n")
        for i, (title, _) in enumerate(wallpapers):
            print(f"  [{i}] {title}")
        print("\n  [-1] Exit\n")

        while True:
            try:
                choice = int(input("Select wallpaper number: "))
                if choice == -1:
                    print("Exiting.")
                    sys.exit(0)
                if 0 <= choice < len(wallpapers):
                    break
                print(f"Enter 0–{len(wallpapers) - 1}, or -1 to exit.")
            except ValueError:
                print("Invalid input.")

        selected = wallpapers[choice][1]
        print("\nPreviewing...")
        preview(selected)

        if input("Use this wallpaper? (y/n): ").lower() == "y":
            selected = upscale_with_cache(selected, workspace, cache)
            assign(selected, workspace)
            break
        print("\nGoing back...\n")


if __name__ == "__main__":
    main()
