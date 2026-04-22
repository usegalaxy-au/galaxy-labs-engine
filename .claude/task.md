# AI-generated lab content

I'd like you to build a new feature for this "Bootstrap a lab" feature:
./app/labs_engine/labs/bootstrap.py

I'd like you to add an "upload markdown" field that will allow the user to express their desired Lab in markdown format. Please include a template markdown file that they can download.

I'd like you to extend the endpoint for this request so that it will use the prompts and code in ./generate (you can copy to the appropriate location) to request the generation of the desired Lab Content using the OpenAI completions API (or whatever OpenAI API seems appropriate). Assume that the required secrets for this are defined in the application's .env file.

You should call the generate/fetch_tool_inputs.py code as a module and pass the returned data to the OpenAI API as context for creating the sections.yml data.

The endpoint currently returns a zip archive containing generated lab content, so I'd like you to include your AI-generated Lab Content in this archive, in the appropriate structure. Advice on the structure should be obtained from the OpenAI response. This may be tricky to orchestrate, but requesting section.yaml, template and base/server.yml files separately should make it easier to inject the returned content into the appropriate file/folder structure.
