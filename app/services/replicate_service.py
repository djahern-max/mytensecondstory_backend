import replicate
import os


class ReplicateVideoService:
    def __init__(self):
        self.client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

    def remove_background(
        self, video_file_path: str, background_type: str = "green-screen"
    ):
        """
        Remove background from video using Replicate - simple green screen removal
        """
        try:
            with open(video_file_path, "rb") as video_file:
                output = self.client.run(
                    "nateraw/video-background-remover:ac5c138171b04413a69222c304f67c135e259d46089fc70ef12da685b3c604aa",
                    input={"video": video_file},
                )

            return {
                "success": True,
                "output_url": str(output),
                "message": "Background removed successfully - green screen created",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to remove background",
            }


# Create service instance
replicate_service = ReplicateVideoService()
