
import torch
import numpy as np
import cv2

from pathlib import Path
from PIL import Image


class BackgroundRemover:
    def __init__(self):
        self.device = torch.device("cpu")
        self.model = None

    def load_model(self):
        if self.model is not None:
            return

        print("Loading RVM MobileNetV3...")

        self.model = torch.hub.load(
            "PeterL1n/RobustVideoMatting",
            "mobilenetv3",
            pretrained=True,
            trust_repo=True,
        )

        self.model.eval()
        self.model.to(self.device)

        print("RVM model ready!")

    @torch.inference_mode()
    def remove_background_from_frame(self, frame):
        self.load_model()

        # OpenCV BGR -> RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert image into PyTorch tensor
        src = torch.from_numpy(rgb.copy())
        src = src.permute(2, 0, 1).float() / 255.0

        # RVM input: [B, T, C, H, W]
        src = src.unsqueeze(0).unsqueeze(0).to(self.device)

        h, w = rgb.shape[:2]

        # Reduce inference resolution for CPU efficiency
        downsample_ratio = min(512 / max(h, w), 1.0)

        # Initial recurrent states
        rec = [None] * 4

        # AI inference
        fgr, pha, *rec = self.model(
            src,
            *rec,
            downsample_ratio
        )

        # Extract foreground and alpha
        foreground = fgr[0, 0].cpu().numpy()
        alpha = pha[0, 0, 0].cpu().numpy()

        # Convert to uint8
        foreground = np.clip(foreground.transpose(1, 2, 0), 0, 1)
        alpha = np.clip(alpha, 0, 1)

        # Make RGBA image
        foreground = (foreground * (alpha[:, :, None] > 0)).astype(np.float32)

        rgba = np.dstack([
            foreground,
            alpha
        ])

        rgba = (np.clip(rgba, 0, 1) * 255).astype(np.uint8)

        return Image.fromarray(rgba, mode="RGBA")

    def process_first_frame(self, video_path, output_path):
        video_path = Path(video_path)
        output_path = Path(output_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cap = cv2.VideoCapture(str(video_path))

        if not cap.isOpened():
            raise ValueError("Unable to open video file")

        try:
            success, frame = cap.read()

            if not success:
                raise ValueError("Unable to read first video frame")

            result = self.remove_background_from_frame(frame)
            result.save(output_path, format="PNG")

            return {
                "success": True,
                "output": str(output_path),
                "width": result.width,
                "height": result.height,
                "format": "RGBA PNG",
            }

        finally:
            cap.release()


background_remover = BackgroundRemover()
