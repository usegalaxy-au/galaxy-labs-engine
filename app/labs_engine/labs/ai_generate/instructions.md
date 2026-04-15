# How to build a Galaxy Lab

You are tasked with building a Galaxy Lab content folder, which is a collection of Markdown, HTML and YAML content used by the Galaxy Labs Engine to render a web page. The content that you will be building has been provided in Markdown format (we'll call this the "reference"), and your task is to translate that into the required "Lab content" format.

- Each section should be written to a section_N.yml file
- Default variable definitions should be written to base.yml
- Links to galaxy (e.g. tool URLs, workflow import URLs) should be templated with `{{ galaxy_base_url }}` to ensure they are compatible across different servers.
- Do not add any tools, sections or tabs that are not prescribed in the reference.
- Do not add additional text content to the intro, conclusion or footer reference text except to introduce required Markdown/HTML formatting and style (e.g. inserting a picture, if required).
- All markdown content should be written with appropriate markdown styling and syntax - use your intuition to include headers where appropriate.
- Any content listed in the reference after the conclusion can just be included in conclusion.md. This template is a catch-all for content between the sections and footer.
- All *_md content should be server-agnostic. All content should be templated so that it displays appropriately on any server. For server-specific content (like an embedded footer snippet) you can define a server-specific template as a string variable in the corresponding server.yml file (e.g. usegalaxy.org.au.yml).
- Your first pass over the reference material should identify any words, phrases or items that are likely server-specific and should therefore be templated.
- URLs in markdown should be formatted as Markdown links, not plain text
- Use class "btn btn-primary" for all HTML buttons
- When writing a tab item for a tool:
    - Write a short description in the heading, not just the tool name
    - Always quote the heading text to avoid YAML syntax errors
    - Use provided tool metadata to create `input` elements, if relevant. Do not create multiple inputs for single, interlaced and collection formats of the same "sequencing reads" type inputs. No input label should include "paired", "single", "interleaved", "first read", "second read" as these are all duplications of the same data input.
