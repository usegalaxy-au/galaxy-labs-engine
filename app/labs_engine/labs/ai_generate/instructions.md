# How to build a Galaxy Lab

You are tasked with building a Galaxy Lab content folder, which is a collection of Markdown, HTML and YAML content used by the Galaxy Labs Engine to render a web page. The content that you will be building has been provided in Markdown format (we'll call this the "reference"), and your task is to translate that into the required "Lab content" format.

Refer to this for a simplified example of a Lab Content folder:
https://github.com/usegalaxy-au/galaxy-labs-engine/tree/dev/app/labs_engine/labs/static/labs/content/simple

Refer to this for Lab content which self-documents the process of building Lab content: \
https://github.com/usegalaxy-au/galaxy-labs-engine/tree/dev/app/labs_engine/labs/static/labs/content/docs

Schema specification for the YAML section*.yml files:
https://github.com/usegalaxy-au/galaxy-labs-engine/tree/dev/app/labs_engine/labs/lab_schema.py

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
- Ensure that all YAML is valid e.g. quote strings containing non-alphanumeric chars
- Links to galaxy (e.g. tool URLs, workflow import URLs) should be templated with `{{ galaxy_base_url }}` to ensure they are compatible across different servers.
- Do not add any tools, sections or tabs that are not prescribed in the reference.
- Do not alter intro, conclusion or footer reference text except to introduce required Markdown/HTML formatting and style (e.g. inserting a picture, if required).
- Any content listed in the reference after the conclusion can just be included in conclusion.md. This template is just a catch-all for content between the sections and footer.
- All templates/*.md files should be server-agnostic. All content should be templated so that it displays appropriately on any server. For server-specific content (like an embedded footer snippet) you can set a server-specific template (e.g. usegalaxy.org.au/templates/footer.md) in the corresponding server.yml file (e.g. usegalaxy.org.au.yml).
- When writing a tab item for a tool:
    - Write a short description in the heading, not just the tool name
    - You can fetch the expected inputs from `{galaxy_base_url}/api/tools/{tool_id}?io_details=true` and use that information to write an `inputs` dict into the tab item YAMl, to describe required input data. Don't describe non-data input params or optional input data. Try usegalaxy.org first, and if that returns a 404 try usegalaxy.eu before giving up.
    - To fetch tool metadata in bulk, use the helper script `generate/fetch_tool_inputs.py`. It queries the Galaxy API for a list of tool IDs, recurses through `repeat`/`section`/`conditional` inputs, filters out optional and non-data params, and prints a YAML snippet (per tool: `description` and `inputs`) ready to paste into a section file. Run it from the project root with the project venv, e.g.:

        ```
        # One tool ID per line, '#' comments and '- ' list syntax allowed:
        ./venv/bin/python generate/fetch_tool_inputs.py path/to/tool_ids.txt

        # Or pass tool IDs directly as arguments:
        ./venv/bin/python generate/fetch_tool_inputs.py upload1 toolshed.g2.bx.psu.edu/repos/iuc/fastp/fastp

        # Override the servers to query (repeatable; defaults to usegalaxy.org then usegalaxy.eu):
        ./venv/bin/python generate/fetch_tool_inputs.py --server https://usegalaxy.org.au tool_ids.txt
        ```

        The script queries each configured server in order and falls back to the next on failure. Any tool that cannot be resolved is reported as `NOT FOUND` so you can follow up manually. Prefer this script over ad-hoc `curl` calls when processing more than one or two tools.
