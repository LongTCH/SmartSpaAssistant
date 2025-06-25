from typing import Optional

from pydantic import BaseModel, Field


class SettingDetailsDto(BaseModel):
    """Settings DTO."""

    chat_wait_seconds: Optional[float] = Field(
        None,
        description="Number of seconds to wait between chat responses",
        example=2.5,
        ge=0,
    )
    max_script_retrieval: Optional[int] = Field(
        None,
        description="Maximum number of scripts to retrieve at once",
        example=10,
        ge=1,
    )
    reaction_message: Optional[str] = Field(
        None,
        description="Default reaction message for user interactions",
        example="Thank you for your message!",
    )
    identity: Optional[str] = Field(
        None, description="Bot identity description", example="I am a helpful assistant"
    )
    instructions: Optional[str] = Field(
        None,
        description="Instructions for bot behavior",
        example="Be helpful and polite in all interactions",
    )


class SettingUpdateDto(BaseModel):
    """DTO for updating settings configuration."""

    chat_wait_seconds: Optional[float] = Field(
        None,
        description="Number of seconds to wait between chat responses",
        example=2.5,
        ge=0,
    )
    max_script_retrieval: Optional[int] = Field(
        None,
        description="Maximum number of scripts to retrieve at once",
        example=10,
        ge=1,
    )
    reaction_message: Optional[str] = Field(
        None,
        description="Default reaction message for user interactions",
        example="Thank you for your message!",
    )
    identity: Optional[str] = Field(
        None, description="Bot identity description", example="I am a helpful assistant"
    )
    instructions: Optional[str] = Field(
        None,
        description="Instructions for bot behavior",
        example="Be helpful and polite in all interactions",
    )
