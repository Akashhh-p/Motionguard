from pydantic import BaseModel, Field


class FrameDetectionRequest(BaseModel):
    image: str = Field(description="Base64 data URL or raw base64 JPEG/PNG frame.")
    source_type: str = "webcam"

