import json
from typing import List, Literal

from pydantic import BaseModel, Field, field_validator


class ColumnConfigSchema(BaseModel):
    """Schema for individual column configuration"""

    column_name: str = Field(
        ..., min_length=1, description="Column name cannot be empty"
    )
    column_type: Literal[
        "String", "Text", "Integer", "Numeric", "Boolean", "DateTime"
    ] = Field(..., description="Column type must be one of the valid types")
    description: str = Field(
        ..., min_length=1, description="Column description cannot be empty"
    )
    is_index: bool = Field(
        default=False, description="Whether this column should be indexed"
    )

    @field_validator("column_name")
    @classmethod
    def validate_column_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError("Column description cannot be empty")
        return v.strip()


class SheetCreateSchema(BaseModel):
    """Schema for sheet creation validation"""

    name: str = Field(..., min_length=1, description="Sheet name cannot be empty")
    description: str = Field(
        ..., min_length=1, description="Sheet description cannot be empty"
    )
    column_config: List[ColumnConfigSchema] = Field(
        ..., min_length=1, description="Column configuration must be a non-empty list"
    )
    status: str = Field(default="published", description="Status of the sheet")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Sheet name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError("Sheet description cannot be empty")
        return v.strip()

    @field_validator("column_config")
    @classmethod
    def validate_column_config(cls, v):
        if not v:
            raise ValueError("Column configuration must be a non-empty list")
        return v


def parse_and_validate_column_config(
    column_config_str: str,
) -> List[ColumnConfigSchema]:
    """
    Parse and validate column configuration from JSON string

    Args:
        column_config_str: JSON string of column configuration

    Returns:
        List[ColumnConfigSchema]: Validated column configuration

    Raises:
        ValueError: If validation fails
    """
    if not column_config_str:
        raise ValueError("Column configuration is required")

    try:
        parsed_config = json.loads(column_config_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid column configuration JSON format")

    if not isinstance(parsed_config, list) or len(parsed_config) == 0:
        raise ValueError("Column configuration must be a non-empty list")

    # Validate each column configuration
    validated_columns = []
    for i, col in enumerate(parsed_config):
        try:
            validated_col = ColumnConfigSchema(**col)
            validated_columns.append(validated_col)
        except Exception as e:
            raise ValueError(f"Column {i+1}: {str(e)}")

    return validated_columns


def validate_sheet_creation_data(
    name: str, description: str, column_config: str, status: str = "published"
) -> SheetCreateSchema:
    """
    Validate complete sheet creation data

    Args:
        name: Sheet name
        description: Sheet description
        column_config: JSON string of column configuration
        status: Sheet status

    Returns:
        SheetCreateSchema: Validated sheet data

    Raises:
        ValueError: If validation fails
    """
    # Parse and validate column configuration
    validated_columns = parse_and_validate_column_config(column_config)

    # Create and validate complete sheet data
    sheet_data = {
        "name": name,
        "description": description,
        "column_config": validated_columns,  # Keep as ColumnConfigSchema objects
        "status": status,
    }

    return SheetCreateSchema(**sheet_data)
