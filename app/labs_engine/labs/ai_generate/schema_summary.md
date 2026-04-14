# Galaxy Lab Sections YAML Schema

This describes the Pydantic schema that validates section YAML files. Your
generated YAML **must** conform to this schema.

## LabSectionSchema (top-level of each section file)

| Field        | Type               | Required | Description                        |
|--------------|--------------------|----------|------------------------------------|
| id           | str                | yes      | Unique section identifier          |
| title        | str                | yes      | Display title for the section      |
| tabs         | list[SectionTab]   | yes      | One or more tabs within the section|
| exclude_from | list[str]          | no       | Server names to hide this section  |

## SectionTab

| Field        | Type                                          | Required | Description                           |
|--------------|-----------------------------------------------|----------|---------------------------------------|
| id           | str                                           | yes      | Unique tab identifier                 |
| title        | str                                           | no       | Display title for the tab             |
| heading_md   | str (Markdown/HTML)                           | no       | Introductory text above the items     |
| content      | list[TabItem] OR dict with `subsections` key  | no       | Accordion items or subsections        |
| exclude_from | list[str]                                     | no       | Server names to hide this tab         |

When `content` is a dict it must have the form:
```yaml
content:
  subsections:
    - id: ...
      title: ...
      content: [list of TabItem]
```

## TabItem (each accordion item)

| Field          | Type                 | Required | Description                                |
|----------------|----------------------|----------|--------------------------------------------|
| title_md       | str (Markdown/HTML)  | yes      | Accordion heading; inline MD OK            |
| description_md | str (Markdown/HTML)  | yes      | Body content; full Markdown/HTML OK        |
| buttons        | list[TabItemButton]  | no       | Action buttons (run, view, tutorial, etc.) |
| inputs         | list[ItemInput]      | no       | Expected data inputs for a tool            |
| exclude_from   | list[str]            | no       | Server names to hide this item             |

## TabItemButton

| Field    | Type            | Required | Description                              |
|----------|-----------------|----------|------------------------------------------|
| link     | str             | yes      | URL (use `{{ galaxy_base_url }}` prefix) |
| icon     | IconEnum or null| no       | One of: run, tutorial, social, help, view|
| label_md | str or null     | no       | Button text (if no icon)                 |
| tip      | str or null     | no       | Tooltip on hover                         |

**Constraint:** Every button must have either `icon` or `label_md` (or both).

## ItemInput

| Field     | Type       | Required | Description                              |
|-----------|------------|----------|------------------------------------------|
| label     | str        | no       | Human-readable name of the input         |
| datatypes | list[str]  | no       | Accepted Galaxy datatypes (e.g. fastq)   |

## TabSubsection

| Field        | Type            | Required | Description                          |
|--------------|-----------------|----------|--------------------------------------|
| id           | str             | yes      | Unique subsection identifier         |
| title        | str             | yes      | Display title                        |
| content      | list[TabItem]   | yes      | Accordion items in this subsection   |
| exclude_from | list[str]       | no       | Server names to hide this subsection |

## YAML formatting rules

- Quote any string containing colons, braces, or other special YAML chars.
- Use `>` (folded) or `|` (literal) block scalars for multi-line text.
- Indent consistently with 2 spaces.
- All tool URLs must use `{{ galaxy_base_url }}` instead of a hardcoded server.
- Strip version numbers from the end of tool IDs in URLs.
