#!/usr/bin/env python3

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json

WORKSHOP_DIR = Path.home() / ".local/share/Steam/steamapps/workshop/content/431960"
VIDEOS_DIR = Path.home() / "Videos"
REALESRGAN = Path.home() / "Downloads/realesrgan/realesrgan-ncnn-vulkan"
TARGET_W, TARGET_H = 1920, 1080

def get_videos():
    wallpapers = []
    SUPPORTED = {".mp4", ".webm", ".jpg", ".jpeg", ".png", ".mkv", ".mov"}
    SKIP_TYPES = {"scene", "web", "application"}

    for folder in WORKSHOP_DIR.iterdir():
        if folder.is_dir():
            title = folder.name  # fallback
            project_file = folder / "project.json"

            if project_file.exists():
                try:
                    with open(project_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        title = data.get("title", folder.name)
                        wp_type = data.get("type", "").lower()
                        if wp_type in SKIP_TYPES:
                            continue
                except Exception:
                    pass

            for file in folder.iterdir():
                if file.suffix.lower() in SUPPORTED:
                    wallpapers.append((title, file))
                    break

    return sorted(wallpapers, key=lambda x: x[0].lower())

def preview(video):
    proc = subprocess.Popen([
        "mpv",
        "--no-audio",
        "--length=5",
        str(video)
    ])
    print("Previewing... (press q in the mpv window to skip)")
    proc.wait()

def get_resolution(video):
    result = subprocess.run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        str(video)
    ], capture_output=True, text=True)
    parts = result.stdout.strip().split(",")
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    return None, None

def upscale(video, workspace):
    w, h = get_resolution(video)
    if w is None:
        print("Could not determine resolution, skipping upscale.")
        return video

    if w >= TARGET_W and h >= TARGET_H:
        print(f"Already {w}x{h}, no upscale needed.")
        return video

    print(f"Source is {w}x{h}, upscaling to {TARGET_W}x{TARGET_H}...")

    tmp = Path(tempfile.mkdtemp())
    frames_dir = tmp / "frames"
    upscaled_dir = tmp / "upscaled"
    frames_dir.mkdir()
    upscaled_dir.mkdir()
    output = VIDEOS_DIR / f"wallpaper-ws{workspace+1}-upscaled.mp4"

    try:
        # Extract frames
        print("Extracting frames...")
        subprocess.run([
            "ffmpeg", "-i", str(video),
            str(frames_dir / "frame%04d.png")
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Pick the smallest scale factor that gets us to target resolution
        scale_needed = max(TARGET_W / w, TARGET_H / h)
        if scale_needed <= 2:
            model = "realesr-animevideov3-x2"
            scale_flag = "2"
        elif scale_needed <= 3:
            model = "realesr-animevideov3-x3"
            scale_flag = "3"
        else:
            model = "realesr-animevideov3-x4"
            scale_flag = "4"

        # Upscale frames with Real-ESRGAN
        print(f"Upscaling frames with {model} (this may take a moment)...")
        subprocess.run([
            str(REALESRGAN),
            "-i", str(frames_dir),
            "-o", str(upscaled_dir),
            "-n", model,
            "-s", scale_flag
        ], check=True)

        # Get fps from original
        fps_result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "csv=p=0",
            str(video)
        ], capture_output=True, text=True)
        fps = fps_result.stdout.strip() or "25"
        # Convert fraction like 25/1 to just numerator
        if "/" in fps:
            num, den = fps.split("/")
            fps = str(round(int(num) / int(den)))

        # Reassemble and scale to exact 1920x1080
        print("Assembling final video...")
        subprocess.run([
            "ffmpeg", "-y",
            "-framerate", fps,
            "-i", str(upscaled_dir / "frame%04d.png"),
            "-vf", f"scale={TARGET_W}:{TARGET_H}:flags=lanczos",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-threads", "0",
            str(output)
        ], check=True, stdin=subprocess.DEVNULL)

        print(f"Upscaled to {TARGET_W}x{TARGET_H}: {output.name}")
        return output

    except subprocess.CalledProcessError as e:
        print(f"Upscale failed: {e}. Using original file.")
        if output.exists():
            output.unlink()
        return video
    finally:
        shutil.rmtree(tmp)

def assign(video, workspace):
    ext = video.suffix.lower()
    target = VIDEOS_DIR / f"current-wallpaper-{workspace+1}{ext}"

    # Remove any existing wallpaper with any extension
    for file in VIDEOS_DIR.glob(f"current-wallpaper-{workspace+1}.*"):
        file.unlink()

    os.symlink(video, target)

    print(f"Assigned to workspace {workspace+1}")

    subprocess.run(
        [str(Path.home() / ".local/bin/restart-wallpaper.sh")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

CACHE_FILE = VIDEOS_DIR / ".wallman_cache.json"

def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Warning: could not save cache: {e}")

def get_current_wallpaper(workspace):
    matches = list(VIDEOS_DIR.glob(f"current-wallpaper-{workspace+1}.*"))
    if not matches:
        return None
    path = matches[0]
    # If it's a symlink, resolve and return the name
    if path.is_symlink():
        return path.resolve().name
    return path.name

def show_status():
    print("\nCurrent wallpaper assignments:\n")
    found_any = False
    for i in range(1, 10):
        matches = list(VIDEOS_DIR.glob(f"current-wallpaper-{i}.*"))
        if matches:
            path = matches[0]
            name = path.resolve().name if path.is_symlink() else path.name
            print(f"  Workspace {i}: {name}")
            found_any = True
    if not found_any:
        print("  No wallpapers assigned.")
    print()

def upscale_with_cache(video, workspace, cache):
    cache_key = str(video.resolve())
    if cache_key in cache:
        cached_path = Path(cache[cache_key])
        if cached_path.exists():
            print(f"Using cached upscaled version: {cached_path.name}")
            return cached_path
        else:
            # Cache entry is stale, remove it
            del cache[cache_key]

    result = upscale(video, workspace)

    # Only cache if upscaling actually happened
    if result != video:
        cache[cache_key] = str(result)
        save_cache(cache)

    return result

def main():
    # Handle --status flag
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
    cache = load_cache()

    if not wallpapers:
        print("No video wallpapers found.")
        sys.exit(1)

    while True:
        # Show current assignment
        current = get_current_wallpaper(workspace)
        if current:
            print(f"\nWorkspace {workspace+1} currently: {current}")
        else:
            print(f"\nWorkspace {workspace+1} currently: (none)")

        # Show wallpaper list
        print("\nAvailable wallpapers:\n")
        for i, (title, _) in enumerate(wallpapers):
            print(f"  [{i}] {title}")
        print("\n  [-1] Exit\n")

        # Get choice
        while True:
            try:
                choice = int(input("Select wallpaper number: "))
                if choice == -1:
                    print("Exiting.")
                    sys.exit(0)
                if 0 <= choice < len(wallpapers):
                    break
                print(f"Please enter a number between 0 and {len(wallpapers) - 1}, or -1 to exit.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        selected = wallpapers[choice][1]

        print("\nPreviewing...")
        preview(selected)

        confirm = input("Use this wallpaper? (y/n): ").lower()
        if confirm == "y":
            selected = upscale_with_cache(selected, workspace, cache)
            assign(selected, workspace)
            break
        else:
            print("\nGoing back to selection...\n")
            # Loop continues, showing the list again

# FastFetch Code 

def assign_to_fetch(image_path):
    target_dir = Path.home() / "Pictures/fastfetch"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_link = target_dir / "current_fetch.jpg"
    
    if target_link.exists():
        target_link.unlink()
        
    os.symlink(image_path, target_link)
    print(f"New terminal image assigned: {image_path.name}")


if __name__ == "__main__":
    main()
