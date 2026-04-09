# How to build a Galaxy Lab

You are tasked with building a Galaxy Lab content folder, which is a collection of Markdown, HTML and YAML content used by the Galaxy Labs Engine to render a web page. The content that you will be building has been provided in Markdown format (we'll call this the reference markdown), and your task is to translate that into the required "Lab content" format.

Refer to this for a simplified example of a Lab Content folder:
https://github.com/usegalaxy-au/galaxy-labs-engine/tree/dev/app/labs_engine/labs/static/labs/content/simple

Refer to this for Lab content which self-documents the process of building Lab content: \
https://github.com/usegalaxy-au/galaxy-labs-engine/tree/dev/app/labs_engine/labs/static/labs/content/docs

Schema specification for the YAML section*.yml files:
https://github.com/usegalaxy-au/galaxy-labs-engine/tree/dev/app/labs_engine/labs/lab_schema.py

- The intro should be written to templates/intro.md
- The conclusion should be written to templates/conclusion.md
- The footer should be written to templates/footer.md
- Each section should be written to a sections/section_N.yml file
- Default variable definitions should be written to base.yml
- Per-server variable overrides should be written for each server to ${hostname}.yml. If servers have not been specified, please write files for:
    - usegalaxy.org
    - usegalaxy.eu
    - usegalaxy.org.au
- Links to galaxy (e.g. tool URLs, workflow import URLs) should be templated with `{{ galaxy_server_url }}` to ensure they are compatible across different servers.
- Do not add any tools, sections or tabs that are not prescribed in the reference markdown.
- Do not alter intro, conclusion or footer text except to introduce required Markdown/HTML formatting and style (e.g. inserting a picture, if required).
