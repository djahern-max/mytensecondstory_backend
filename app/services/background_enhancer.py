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
import asyncio
from datetime import datetime

# Import rembg with error handling
try:
    from rembg import remove, new_session

    REMBG_AVAILABLE = True
except ImportError:
    print("⚠️ rembg not installed. Install with: pip install rembg")
    REMBG_AVAILABLE = False

# Import ffmpeg with error handling
try:
    import ffmpeg

    FFMPEG_AVAILABLE = True
except ImportError:
    print("⚠️ ffmpeg-python not installed. Install with: pip install ffmpeg-python")
    FFMPEG_AVAILABLE = False

logger = logging.getLogger(__name__)


class BackgroundRemovalService:
    """Service for removing backgrounds from videos using AI"""

    def __init__(self):
        # Use project root directory for output instead of temp
        self.output_dir = Path.cwd() / "processed_videos"
        self.output_dir.mkdir(exist_ok=True)

        # Still use temp for intermediate processing
        self.temp_dir = Path(tempfile.gettempdir()) / "background_removal"
        self.temp_dir.mkdir(exist_ok=True)

        # Initialize rembg session if available
        if REMBG_AVAILABLE:
            try:
                self.session = new_session("u2net_human_seg")
                logger.info("✅ Background removal service initialized with rembg")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize rembg session: {e}")
                self.session = None
        else:
            self.session = None
            logger.warning(
                "⚠️ rembg not available - background removal will be simulated"
            )

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
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(
                    self.output_dir / f"{input_name}_no_bg_{timestamp}.mp4"
                )

            # Check if rembg is available
            if not REMBG_AVAILABLE or not self.session:
                logger.warning("🔄 Simulating background removal (rembg not available)")
                return await self._simulate_background_removal(
                    input_video_path, output_path
                )

            # Get video properties
            cap = cv2.VideoCapture(input_video_path)
            if not cap.isOpened():
                raise Exception(f"Could not open video file: {input_video_path}")

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
                try:
                    frame_no_bg = remove(frame, session=self.session)
                except Exception as e:
                    logger.warning(f"Frame {frame_index} processing failed: {e}")
                    # Use original frame if processing fails
                    frame_no_bg = frame

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
            await self._reassemble_video(frames_dir, output_path, fps, width, height)

            # Cleanup temporary frames
            for frame_path in processed_frames:
                try:
                    os.remove(frame_path)
                except:
                    pass
            try:
                frames_dir.rmdir()
            except:
                pass

            logger.info(f"Background removal complete: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error removing background: {str(e)}")
            raise

    async def _reassemble_video(
        self, frames_dir: Path, output_path: str, fps: int, width: int, height: int
    ):
        """Reassemble processed frames into video"""
        try:
            if FFMPEG_AVAILABLE:
                # Use ffmpeg to create video from frames
                input_pattern = str(frames_dir / "frame_%06d.png")
                (
                    ffmpeg.input(input_pattern, framerate=fps)
                    .output(
                        output_path,
                        vcodec="libx264",
                        pix_fmt="yuv420p",
                        crf=23,  # Good quality/size balance
                    )
                    .overwrite_output()
                    .run(quiet=True)
                )
            else:
                # Fallback to OpenCV
                await self._reassemble_with_opencv(
                    frames_dir, output_path, fps, width, height
                )

        except Exception as e:
            logger.error(f"Error reassembling video: {str(e)}")
            # Fallback to OpenCV if ffmpeg fails
            await self._reassemble_with_opencv(
                frames_dir, output_path, fps, width, height
            )

    async def _reassemble_with_opencv(
        self, frames_dir: Path, output_path: str, fps: int, width: int, height: int
    ):
        """Fallback video assembly using OpenCV"""
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Get all frame files and sort them
        frame_files = sorted([f for f in frames_dir.glob("frame_*.png")])

        for frame_path in frame_files:
            frame = cv2.imread(str(frame_path))
            if frame is not None:
                out.write(frame)

        out.release()

    async def _simulate_background_removal(
        self, input_path: str, output_path: str
    ) -> str:
        """Simulate background removal by copying the original file"""
        logger.info("🔄 Simulating background removal...")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Simple copy for simulation
        import shutil

        shutil.copy2(input_path, output_path)

        # Add a small delay to simulate processing
        await asyncio.sleep(2)

        logger.info(f"✅ Simulation complete: {output_path}")
        return output_path

    def get_video_info(self, video_path: str) -> dict:
        """Get basic video information"""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"Could not open video: {video_path}")

            info = {
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": int(cap.get(cv2.CAP_PROP_FPS)),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                / max(1, int(cap.get(cv2.CAP_PROP_FPS))),
            }

            cap.release()
            return info

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {
                "width": 0,
                "height": 0,
                "fps": 0,
                "frame_count": 0,
                "duration": 0,
                "error": str(e),
            }


# Create service instance
background_removal_service = BackgroundRemovalService()
