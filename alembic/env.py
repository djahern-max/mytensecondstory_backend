"""
Background removal service using rembg for video processing
"""

import os
import cv2
import numpy as np
from typing import Optional, Tuple
import tempfile
import logging
from pathlib import Path
from rembg import remove, new_session
import ffmpeg

logger = logging.getLogger(__name__)


class BackgroundRemovalService:
    """Service for removing backgrounds from videos using AI"""

    def __init__(self):
        # Initialize rembg session with human-optimized model
        self.session = new_session("u2net_human_seg")
        self.temp_dir = Path(tempfile.gettempdir()) / "background_removal"
        self.temp_dir.mkdir(exist_ok=True)

    async def remove_background_from_video(
        self, input_video_path: str, output_path: Optional[str] = None
    ) -> str:
        """
        Remove background from video file

        Args:
            input_video_path: Path to input video
            output_path: Optional custom output path

        Returns:
            Path to processed video with transparent background
        """
        try:
            if not output_path:
                input_name = Path(input_video_path).stem
                output_path = str(self.temp_dir / f"{input_name}_no_bg.mp4")

            # Get video properties
            cap = cv2.VideoCapture(input_video_path)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            logger.info(
                f"Processing video: {width}x{height}, {fps}fps, {frame_count} frames"
            )

            # Create temporary directory for frames
            frames_dir = self.temp_dir / f"frames_{os.urandom(8).hex()}"
            frames_dir.mkdir(exist_ok=True)

            processed_frames = []
            frame_index = 0

            # Process each frame
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Remove background from frame
                frame_no_bg = remove(frame, session=self.session)

                # Save processed frame
                frame_path = frames_dir / f"frame_{frame_index:06d}.png"
                cv2.imwrite(str(frame_path), frame_no_bg)
                processed_frames.append(str(frame_path))

                frame_index += 1

                # Progress logging
                if frame_index % 30 == 0:  # Log every 30 frames
                    progress = (frame_index / frame_count) * 100
                    logger.info(f"Processing progress: {progress:.1f}%")

            cap.release()

            # Reassemble video from processed frames
            await self._reassemble_video(
                processed_frames, output_path, fps, width, height
            )

            # Cleanup temporary frames
            for frame_path in processed_frames:
                try:
                    os.remove(frame_path)
                except:
                    pass
            frames_dir.rmdir()

            logger.info(f"Background removal complete: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error removing background: {str(e)}")
            raise

    async def _reassemble_video(
        self, frame_paths: list, output_path: str, fps: int, width: int, height: int
    ):
        """Reassemble processed frames into video"""
        try:
            # Use ffmpeg to create video from frames
            (
                ffmpeg.input(
                    str(self.temp_dir / "frames_*" / "frame_%06d.png"), framerate=fps
                )
                .output(
                    output_path,
                    vcodec="libx264",
                    pix_fmt="yuv420p",
                    crf=23,  # Good quality/size balance
                )
                .overwrite_output()
                .run(quiet=True)
            )
        except Exception as e:
            logger.error(f"Error reassembling video: {str(e)}")
            # Fallback to OpenCV if ffmpeg fails
            await self._reassemble_with_opencv(
                frame_paths, output_path, fps, width, height
            )

    async def _reassemble_with_opencv(
        self, frame_paths: list, output_path: str, fps: int, width: int, height: int
    ):
        """Fallback video assembly using OpenCV"""
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        for frame_path in sorted(frame_paths):
            frame = cv2.imread(frame_path)
            if frame is not None:
                out.write(frame)

        out.release()

    def get_video_info(self, video_path: str) -> dict:
        """Get basic video information"""
        cap = cv2.VideoCapture(video_path)

        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": int(cap.get(cv2.CAP_PROP_FPS)),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            / int(cap.get(cv2.CAP_PROP_FPS)),
        }

        cap.release()
        return info


# Create service instance
background_removal_service = BackgroundRemovalService()
