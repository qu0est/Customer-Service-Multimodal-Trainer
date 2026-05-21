from pydantic import BaseModel


class ModerationResult(BaseModel):
    rationale: str


class TextModerationResult(ModerationResult):
    contains_pii: bool
    is_unfriendly: bool
    is_unprofessional: bool


class ImageModerationResult(ModerationResult):
    contains_pii: bool
    is_disturbing: bool
    is_low_quality: bool


class VideoModerationResult(ModerationResult):
    contains_pii: bool
    is_disturbing: bool
    is_low_quality: bool


class AudioModerationResult(ModerationResult):
    transcription: str
    contains_pii: bool
    is_unfriendly: bool
    is_unprofessional: bool
