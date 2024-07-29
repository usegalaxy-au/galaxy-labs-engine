"""Schema for validating Galaxy Lab content."""

import re
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from pydantic.types import Annotated
from typing import Optional, Union


def html_tags(v: str) -> str:
    """Validate markdown content."""
    if "<" not in v:
        return v
    # Remove self closing tags
    v = (
        re.sub(r'(<.*?/>)|(<img.*?>)', '', v, flags=re.MULTILINE)
        .replace('<br>', '')
        .replace('<hr>', '')
    )
    # Enumerate open/close tags
    open_tags = re.findall(r'<[^/][\s\S]*?>', v, flags=re.MULTILINE)
    close_tags = re.findall(r'</[\s\S]*?>', v, flags=re.MULTILINE)
    assert len(open_tags) == len(close_tags), (
        f'Unclosed HTML tag in section content:\n{v}')
    return v


MarkdownStr = Annotated[
    str,
    Field(description='Markdown or HTML formatted string.'),
]


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
    button_link: Optional[str] = None
    button_tip: Optional[str] = None
    button_md: Optional[MarkdownStr] = None
    button_icon: Optional[IconEnum] = None
    view_link: Optional[str] = None
    view_tip: Optional[str] = None
    view_md: Optional[MarkdownStr] = None
    view_icon: Optional[IconEnum] = None
    exclude_from: Optional[list[str]] = []

    @field_validator(
        'title_md', 'description_md', 'button_md', 'view_md',
        mode='before',
    )
    def validate_md(cls, value):
        return html_tags(value)


class TabSubsection(BaseModel):
    """Validate Galaxy Lab section tab subsection."""
    id: str
    title: str
    content: list[TabItem]


class SectionTab(BaseModel):
    """Validate Galaxy Lab section tab."""
    id: str
    title: Optional[str] = None
    content: Optional[
        Union[
            list[TabItem],
            dict[TabContentEnum, list[TabSubsection]]
        ]
    ] = None
    heading_md: Optional[MarkdownStr] = None

    @field_validator('heading_md', mode='before')
    def validate_md(cls, value):
        return html_tags(value)


class LabSectionSchema(BaseModel):
    """Validate Galaxy Lab section."""
    id: str
    tabs: list[SectionTab]


class LabSchema(BaseModel):
    """Validate Galaxy Lab content."""
    site_name: str
    lab_name: str
    nationality: str
    galaxy_base_url: str
    subdomain: str
    root_domain: str
    sections: list[str] | str
    header_logo: Optional[str] = None
    custom_css: Optional[str] = None
    intro_md: Optional[str] = None
    conclusion_md: Optional[str] = None
    footer_md: Optional[str] = None
