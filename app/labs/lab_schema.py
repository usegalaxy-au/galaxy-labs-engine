"""Schema for validating Galaxy Lab content."""

import re
from enum import Enum
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    field_validator,
    StrictStr,
)
from pydantic.types import Annotated
from typing import Any, Optional, Union


def soft_coerce_str(v: Any) -> str:
    if isinstance(v, (int, float, bool)):
        return str(v)
    return v


FlexibleStr = Annotated[
    StrictStr,
    BeforeValidator(soft_coerce_str),
]

MarkdownStr = Annotated[
    FlexibleStr,
    Field(description='Markdown or HTML formatted string.'),
]


class ItemInput(BaseModel):
    """An expected dataset input for a Galaxy tool."""
    datatypes: Optional[list[FlexibleStr]] = []
    label: Optional[FlexibleStr] = ''


class IconEnum(str, Enum):
    """Define material icon types for buttons."""
    run = 'run'            # play_arrow
    tutorial = 'tutorial'  # school
    social = 'social'      # group
    help = 'help'          # help
    view = 'view'          # visibility


class TabContentEnum(str, Enum):
    """Define the type of content in a tab item."""
    subsections = 'subsections'


class TabItem(BaseModel):
    """Validate Galaxy Lab section tab item.

    In the UI this will be rendered as an "accordion" item.
    """
    title_md: MarkdownStr
    description_md: MarkdownStr
    button_link: Optional[FlexibleStr] = None
    button_tip: Optional[FlexibleStr] = None
    button_md: Optional[MarkdownStr] = None
    button_icon: Optional[IconEnum] = None
    view_link: Optional[FlexibleStr] = None
    view_tip: Optional[FlexibleStr] = None
    view_md: Optional[MarkdownStr] = None
    view_icon: Optional[IconEnum] = None
    exclude_from: Optional[list[FlexibleStr]] = []
    inputs: Optional[list[ItemInput]] = None

    @field_validator(
        'title_md', 'description_md', 'button_md', 'view_md',
        mode='before',
    )
    def validate_md(cls, value):
        return html_tags(value)


class TabSubsection(BaseModel):
    """Validate Galaxy Lab section tab subsection."""
    id: FlexibleStr
    title: FlexibleStr
    content: list[TabItem]
    exclude_from: Optional[list[FlexibleStr]] = []


class SectionTab(BaseModel):
    """Validate Galaxy Lab section tab."""
    id: FlexibleStr
    title: Optional[FlexibleStr] = None
    content: Optional[
        Union[
            list[TabItem],
            dict[TabContentEnum, list[TabSubsection]]
        ]
    ] = None
    heading_md: Optional[MarkdownStr] = None
    exclude_from: Optional[list[FlexibleStr]] = []

    @field_validator('heading_md', mode='before')
    def validate_md(cls, value):
        return html_tags(value)


class LabSectionSchema(BaseModel):
    """Validate Galaxy Lab section."""
    id: FlexibleStr
    title: FlexibleStr
    tabs: list[SectionTab]
    exclude_from: Optional[list[FlexibleStr]] = []


class LabSchema(BaseModel, extra='allow'):
    """Validate Galaxy Lab content."""
    site_name: FlexibleStr
    lab_name: FlexibleStr
    nationality: Optional[FlexibleStr] = ''
    galaxy_base_url: FlexibleStr
    subdomain: FlexibleStr
    root_domain: FlexibleStr
    sections: list[FlexibleStr] | FlexibleStr
    header_logo: Optional[FlexibleStr] = None
    custom_css: Optional[FlexibleStr] = None
    intro_md: Optional[FlexibleStr] = None
    conclusion_md: Optional[FlexibleStr] = None
    footer_md: Optional[FlexibleStr] = None


def html_tags(value: str) -> str:
    """Validate markdown content."""
    if "<" not in value:
        return value
    # Remove self closing tags
    value = (
        re.sub(r'(<.*?/>)|(<img.*?>)', '', value, flags=re.MULTILINE)
        .replace('<br>', '')
        .replace('<hr>', '')
    )
    # Enumerate open/close tags
    open_tags = re.findall(r'<[^/][\s\S]*?>', value, flags=re.MULTILINE)
    close_tags = re.findall(r'</[\s\S]*?>', value, flags=re.MULTILINE)
    assert len(open_tags) == len(close_tags), (
        f'Unclosed HTML tag in section content:\n{value}')
    return value
