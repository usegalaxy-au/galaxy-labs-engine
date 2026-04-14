# Galaxy Lab Content Documentation Summary

This document summarises how Galaxy Lab content folders work. Use this as
authoritative guidance when generating Lab content.

## Content folder structure

A Lab content folder contains:

```
base.yml                  # Default variables and file references
usegalaxy.org.yml         # Per-server variable overrides
usegalaxy.eu.yml
usegalaxy.org.au.yml
CONTRIBUTORS              # Plain-text list of GitHub usernames
templates/
  intro.md                # Introductory text (Markdown or HTML)
  conclusion.md           # Conclusion text
  footer.md               # Footer content
static/
  custom.css              # Optional custom styles
  logo.svg                # Header logo image
sections/
  section_1.yml           # One YAML file per page section
  section_2.yml
```

## base.yml

Defines default variables used across the Lab. Any key set here can be
referenced in Markdown/HTML templates as `{{ variable_name }}`. Important
properties:

- `site_name`, `lab_name` – displayed in headers and templates.
- `galaxy_base_url` – base URL for tool/workflow links (templated per server).
- `subdomain`, `root_domain` – used to build URLs.
- `header_logo`, `custom_css`, `intro_md`, `footer_md`, `conclusion_md` –
  relative paths to content files.
- `sections` – ordered list of section YAML filenames (relative paths).
- `toc: true` – adds a floating table-of-contents button.
- `support_url` - the user support URL for the current server (defaults to https://help.usegalaxy.org in base.yml)

If a video URL has been requested, including it as a `video_url` will render it automatically into the intro component. Do not hard-code this into a template.

## Server override files (e.g. usegalaxy.org.au.yml)

Inherit everything from `base.yml` and override server-specific values:

```yaml
site_name: "Australia"
galaxy_base_url: https://genome.usegalaxy.org.au
root_domain: usegalaxy.org.au
```

If a feedback form has been requested, including a `feedback_url` variable will create it automatically. Do not hard-code this into a template.

## Templates (intro.md, conclusion.md, footer.md)

- Markdown **or** HTML is accepted.
- Variables from base.yml / server.yml are available: `{{ lab_name }}`,
  `{{ galaxy_base_url }}`, etc.
- Templates should be **server-agnostic**. Use variables for anything that
  differs between servers. Any links with domains containing "usegalaxy." should probably be templated.

## Section YAML files

Each section file describes one collapsible section on the page, composed of
tabs. Each tab contains a heading and a list of expandable "accordion" items.

### Linking to tools

Use the `buttons` list (preferred) with an `icon` or `label_md`:

```yaml
buttons:
  - icon: run
    tip: Run FastQC
    link: "{{ galaxy_base_url }}/?tool_id=toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc"
```

Always strip the version number from the end of tool URLs. Available icons:
`run`, `tutorial`, `social`, `help`, `view`.

### Linking to workflows

Use TRS import links for cross-server compatibility:

```yaml
buttons:
  - icon: run
    link: "{{ galaxy_base_url }}/workflows/trs_import?trs_server=workflowhub.eu&run_form=true&trs_id=222"
    tip: Import to Galaxy
  - icon: view
    link: https://workflowhub.eu/workflows/222
    tip: View in WorkflowHub
```

### Linking to tutorials/learning resources

```yaml
buttons:
  - icon: tutorial
    link: "https://training.galaxyproject.org/training-material/..."
    tip: View tutorial
```

Or with a label:

```yaml
buttons:
  - label_md: More info
    link: "https://..."
```

### Tool inputs

Describe required data inputs so users know what to prepare:

```yaml
inputs:
  - label: Sequencing data for analysis
    datatypes:
      - fasta
      - fastq
      - bam
```

### Subsections

Tabs can optionally split content into named subsections:

```yaml
content:
  subsections:
    - id: qc_tools
      title: Quality Control
      content:
        - title_md: FastQC
          ...
```

### Excluding items from specific servers

Any item can be hidden on certain servers:

```yaml
- title_md: Quota requests
  description_md: ...
  exclude_from:
    - usegalaxy.org
```

### Example of invalid YAML

Be careful with string values that contain special characters:

```yaml
# Bad:
label: A new tool: something new to use

# Good:
label: "A new tool: something new to use"
```

## Variables

Any key defined in base.yml or a server.yml can be referenced in templates
and section YAML values as `{{ key_name }}`.

## Images

Use standard Markdown `![alt](path)` or HTML `<img>` tags. Relative paths
resolve against the content folder root.
