# How to build a Galaxy Lab

You are tasked with building a Galaxy Lab content folder, which is a collection of Markdown, HTML and YAML content used by the Galaxy Labs Engine to render a web page. The content that you will be building has been provided in Markdown format (we'll call this the "reference"), and your task is to translate that into the required "Lab content" format.

- Content should be written to a sub-folder "${lab_name}"
- The intro should be written to templates/intro.md
- The conclusion should be written to templates/conclusion.md
- The footer should be written to templates/footer.md
- Each section should be written to a sections/section_N.yml file
- Default variable definitions should be written to base.yml
- Per-server variable overrides should be written for each server to ${hostname}.yml. If servers have not been specified, please write the following server files:
    - usegalaxy.org.yml
    - usegalaxy.eu.yml
    - usegalaxy.org.au.yml
- Ensure that all YAML is valid e.g. quote strings containing non-alphanumeric chars. The following YAML string value should be quoted: `label: Something: great stuff!`
- Links to galaxy (e.g. tool URLs, workflow import URLs) should be templated with `{{ galaxy_base_url }}` to ensure they are compatible across different servers.
- Do not add any tools, sections or tabs that are not prescribed in the reference.
- Do not alter intro, conclusion or footer reference text except to introduce required Markdown/HTML formatting and style (e.g. inserting a picture, if required).
- Any content listed in the reference after the conclusion can just be included in conclusion.md. This template is just a catch-all for content between the sections and footer.
- All templates/*.md files should be server-agnostic. All content should be templated so that it displays appropriately on any server. For server-specific content (like an embedded footer snippet) you can set a server-specific template (e.g. usegalaxy.org.au/templates/footer.md) in the corresponding server.yml file (e.g. usegalaxy.org.au.yml).
- Your first pass over the reference material should identify any words, phrases or items that are likely server-specific and should therefore be templated.
- URLs in markdown should be formatted as links, not plain text
- Use class "btn btn-primary" for all buttons
- When writing a tab item for a tool:
    - Write a short description in the heading, not just the tool name
    - Use provided tool metadata to create `input` elements, if relevant. Do not create duplicate inputs for single, interlaced and collection formats for the same input dataset.
