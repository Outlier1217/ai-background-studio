
import subprocess
import tempfile

from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

from services.background_remover import background_remover


class VideoProcessor:

    MAX_DURATION = 360

    def __init__(self):
        self.device = torch.device("cpu")

    def prepare_background(self, image_path, width, height):
        image = Image.open(image_path).convert("RGB")

        bg = np.array(image)

        # Cover scaling: fill complete video frame
        scale = max(width / bg.shape[1], height / bg.shape[0])

        new_width = int(bg.shape[1] * scale)
        new_height = int(bg.shape[0] * scale)

        bg = cv2.resize(
            bg,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

        x = (new_width - width) // 2
        y = (new_height - height) // 2

        return bg[y:y + height, x:x + width]

    def process_video(self, input_path, background_path, output_path, progress_callback=None):

        input_path = Path(input_path)
        background_path = Path(background_path)
        output_path = Path(output_path)

        if not input_path.exists():
            raise FileNotFoundError("Input video not found")

        if not background_path.exists():
            raise FileNotFoundError("Background image not found")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(input_path))

        if not cap.isOpened():
            raise ValueError("Unable to open input video")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0 or total_frames <= 0:
            cap.release()
            raise ValueError("Invalid video metadata")

        duration = total_frames / fps

        if duration > self.MAX_DURATION:
            cap.release()
            raise ValueError("Video cannot exceed 6 minutes")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if width <= 0 or height <= 0:
            cap.release()
            raise ValueError("Invalid video dimensions")

        background = self.prepare_background(
            background_path,
            width,
            height
        )

        # Load AI model once
        background_remover.load_model()
        model = background_remover.model

        # RVM temporal states
        rec = [None] * 4

        downsample_ratio = min(
            512 / max(height, width),
            1.0
        )

        silent_video = output_path.with_name(
            output_path.stem + "_silent.mp4"
        )

        command = [
            "ffmpeg",
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}",
            "-r", str(fps),
            "-i", "-",
            "-an",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            str(silent_video)
        ]

        process = None
        processed_frames = 0

        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            with torch.inference_mode():

                while True:

                    success, frame = cap.read()

                    if not success:
                        break

                    rgb = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB
                    )

                    src = torch.from_numpy(rgb.copy())
                    src = src.permute(2, 0, 1).float() / 255.0

                    src = src.unsqueeze(0).unsqueeze(0)
                    src = src.to(self.device)

                    # AI inference with preserved temporal states
                    fgr, pha, *rec = model(
                        src,
                        *rec,
                        downsample_ratio
                    )

                    foreground = (
                        fgr[0, 0]
                        .permute(1, 2, 0)
                        .cpu()
                        .numpy()
                    )

                    alpha = (
                        pha[0, 0, 0]
                        .cpu()
                        .numpy()
                    )

                    # Composite foreground with custom background
                    result = (
                        foreground * alpha[:, :, None]
                        + (background / 255.0)
                        * (1.0 - alpha[:, :, None])
                    )

                    result = np.clip(
                        result * 255,
                        0,
                        255
                    ).astype(np.uint8)

                    result_bgr = cv2.cvtColor(
                        result,
                        cv2.COLOR_RGB2BGR
                    )

                    process.stdin.write(
                        result_bgr.tobytes()
                    )

                    processed_frames += 1

                    progress = round((processed_frames / total_frames) * 100)

                    if progress_callback:
                        progress_callback(progress, processed_frames, total_frames)

                    if processed_frames % 30 == 0:
                        print(f"Progress: {processed_frames}/{total_frames} ({progress:.1f}%)")

            process.stdin.close()
            return_code = process.wait()

            if return_code != 0:
                raise RuntimeError("FFmpeg video encoding failed")

            # Preserve original audio
            mux_command = [
                "ffmpeg",
                "-y",
                "-i", str(silent_video),
                "-i", str(input_path),
                "-map", "0:v:0",
                "-map", "1:a?",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                str(output_path)
            ]

            subprocess.run(
                mux_command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            silent_video.unlink(missing_ok=True)

            return {
                "success": True,
                "output": str(output_path),
                "width": width,
                "height": height,
                "fps": fps,
                "duration": round(duration, 2),
                "total_frames": total_frames,
                "processed_frames": processed_frames,
                "audio_preserved": True
            }

        finally:
            cap.release()

            if process is not None and process.poll() is None:
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
                process.terminate()
                process.wait()

            if silent_video.exists():
                silent_video.unlink()


video_processor = VideoProcessor()
