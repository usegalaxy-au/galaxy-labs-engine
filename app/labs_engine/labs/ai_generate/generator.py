"""Generate Galaxy Lab content from a Markdown reference using OpenAI.

Workflow:
1. Extract tool IDs from the user-supplied Markdown reference.
2. Look up each tool's description and required data inputs using the
   ``fetch_tool_inputs`` helper module (copied from ``generate/``).
3. Call the OpenAI API with the instructions, the reference Markdown and
   the tool metadata as context, asking it to return a JSON structure that
   describes the files to write into the Lab content folder.
4. Return that structure to the caller, which is responsible for writing
   the files into the output directory.
"""
import json
import logging
import re
from pathlib import Path

from django.conf import settings
# L268: from openai import OpenAI

import django_rq

from . import fetch_tool_inputs

logger = logging.getLogger('django')

PROGRESS_KEY_PREFIX = 'bootstrap:progress:'
PROGRESS_TTL = 600  # 10 minutes

PACKAGE_DIR = Path(__file__).parent
INSTRUCTIONS_PATH = PACKAGE_DIR / 'instructions.md'
DOCS_SUMMARY_PATH = PACKAGE_DIR / 'docs_summary.md'
SCHEMA_SUMMARY_PATH = PACKAGE_DIR / 'schema_summary.md'

EXAMPLE_LAB_DIR = (
    Path(__file__).resolve().parent.parent
    / 'static' / 'labs' / 'content' / 'simple'
)
EXAMPLE_FILES = {
    'base.yml': EXAMPLE_LAB_DIR / 'base.yml',
    'templates/intro.md': EXAMPLE_LAB_DIR / 'templates' / 'intro.md',
    'templates/conclusion.md': (
        EXAMPLE_LAB_DIR / 'templates' / 'conclusion.md'
    ),
    'templates/footer.md': EXAMPLE_LAB_DIR / 'templates' / 'footer.md',
    'section_1.yml': EXAMPLE_LAB_DIR / 'section_1.yml',
}
EXAMPLE_SERVER_YML = (
    "# Server-specific overrides (inherits everything from base.yml)\n"
    "\n"
    'site_name: "Australia"\n'
    "galaxy_base_url: https://genome.usegalaxy.org.au\n"
    "root_domain: usegalaxy.org.au\n"
)

OPENAI_MODEL = 'gpt-5'
OPENAI_TIMEOUT = 180

# Regex matches tool IDs like:
#   upload1
#   ebi_sra_main
#   interactive_tool_pavian
#   toolshed.g2.bx.psu.edu/repos/iuc/fastp/fastp
TOOLSHED_TOOL_RE = re.compile(
    r'toolshed(?:\.test)?\.g2\.bx\.psu\.edu/repos/[\w\-.]+/[\w\-.]+/[\w\-.]+'
)
BUILTIN_TOOL_RE = re.compile(
    r'(?:^|\s|-\s*|`)'
    r'([a-z][a-z0-9_]*[0-9a-z])'
    r'(?:\s|$|`)'
)
# Avoid false positives from plain English words in prose. Only treat a
# bare identifier as a tool ID if it looks like a Galaxy tool name.
BUILTIN_TOOL_PREFIXES = (
    'upload', 'interactive_tool_', 'ebi_', 'ucsc_', 'ncbi_',
)

SYSTEM_PROMPT = (
    "You are an expert Galaxy Lab content author. Given a reference"
    " Markdown description of a desired Galaxy Lab, you produce a complete"
    " Lab content folder that conforms to the Galaxy Labs Engine schema."
    " Follow the supplied instructions exactly. Respond with a single JSON"
    " object that matches the requested schema and nothing else."
)

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intro_md": {
            "type": "string",
            "description": (
                "Full Markdown content for templates/intro.md. This should be"
                " styled with Markdown syntax appropriate for the text"
                " content."
            ),
        },
        "conclusion_md": {
            "type": "string",
            "description": (
                "Full Markdown content for templates/conclusion.md. This"
                " should be styled with Markdown syntax appropriate for the"
                " text content."
            ),
        },
        "footer_md": {
            "type": "string",
            "description": (
                "Full Markdown content for templates/footer.md. This should be"
                " styled with Markdown syntax appropriate for the text"
                " content."
            ),
        },
        "base_yml": {
            "type": "string",
            "description": (
                "Full YAML content for base.yml. Must reference every"
                " section file listed in the 'sections' array below."
            ),
        },
        "servers": {
            "type": "array",
            "description": (
                "One entry per Galaxy server (usegalaxy.org,"
                " usegalaxy.eu, usegalaxy.org.au)."
            ),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": (
                            "Bare hostname like 'usegalaxy.org'."
                        ),
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "Full YAML content for <hostname>.yml."
                        ),
                    },
                },
                "required": ["hostname", "content"],
            },
        },
        "sections": {
            "type": "array",
            "description": (
                "Section YAML files to write under sections/. Order"
                " matches display order on the page."
            ),
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": (
                            "Relative filename under sections/, e.g."
                            " 'section_1.yml'."
                        ),
                    },
                    "content": {
                        "type": "string",
                        "description": "Full YAML content for the file.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
    "required": [
        "intro_md",
        "conclusion_md",
        "footer_md",
        "base_yml",
        "servers",
        "sections",
    ],
}


def publish_progress(job_id: str, message: str):
    """Write a progress message to Redis for the given job."""
    if not job_id:
        return
    conn = django_rq.get_connection('default')
    key = PROGRESS_KEY_PREFIX + job_id
    conn.set(key, message, ex=PROGRESS_TTL)


def get_progress(job_id: str) -> str:
    """Read the current progress message for a job, if any."""
    conn = django_rq.get_connection('default')
    value = conn.get(PROGRESS_KEY_PREFIX + job_id)
    if value is not None:
        return value.decode()
    return ''


class AIGenerationError(Exception):
    """Raised when AI lab generation fails."""


def extract_tool_ids(markdown: str) -> list[str]:
    """Return a de-duplicated list of Galaxy tool IDs found in the text."""
    found = []
    seen = set()

    def add(tid):
        if tid and tid not in seen:
            seen.add(tid)
            found.append(tid)

    for match in TOOLSHED_TOOL_RE.findall(markdown):
        add(match)

    for line in markdown.splitlines():
        stripped = line.strip().lstrip('-*').strip().strip('`').strip()
        if not stripped:
            continue
        # Skip URLs and already-matched toolshed IDs.
        if '://' in stripped or '/' in stripped:
            continue
        # Only a single token allowed.
        if ' ' in stripped:
            continue
        if not re.fullmatch(r'[a-z][a-z0-9_]*[0-9a-z]', stripped):
            continue
        if (
            stripped.startswith(BUILTIN_TOOL_PREFIXES)
            or re.search(r'\d', stripped)
        ):
            add(stripped)

    return found


def _read_context_files() -> str:
    """Read documentation, schema and example files into a prompt section."""
    parts = []

    # Documentation summary
    parts.append("# Documentation summary")
    parts.append(DOCS_SUMMARY_PATH.read_text())

    # Schema summary
    parts.append("# Sections YAML schema")
    parts.append(SCHEMA_SUMMARY_PATH.read_text())

    # Example files from the "simple" lab
    parts.append("# Example Lab content files")
    parts.append(
        "Below are real files from a working Galaxy Lab. Use these as"
        " structural templates. Reproduce the formatting, indentation and"
        " YAML conventions exactly."
    )
    for label, path in EXAMPLE_FILES.items():
        if path.exists():
            parts.append(f"\n## Example: {label}")
            parts.append(f"```\n{path.read_text().rstrip()}\n```")

    # Example server override file
    parts.append("\n## Example: usegalaxy.org.au.yml")
    parts.append(f"```yaml\n{EXAMPLE_SERVER_YML.rstrip()}\n```")

    return "\n".join(parts)


def build_user_prompt(
    lab_name: str,
    reference_md: str,
    tool_metadata_yaml: str,
    instructions: str,
) -> str:
    """Compose the user prompt for the OpenAI request."""
    context = _read_context_files()
    parts = [
        "# Task",
        (
            "Produce a complete Galaxy Lab content folder for a Lab named"
            f' "{lab_name}" based on the reference below. Use the tool'
            " metadata as authoritative information about each tool's"
            " description and required inputs."
        ),
        "",
        "# Instructions",
        instructions,
        "",
        context,
        "",
        "# Reference (user-supplied Markdown)",
        reference_md,
    ]
    if tool_metadata_yaml.strip():
        parts += [
            "",
            "# Tool metadata (YAML, pre-fetched from the Galaxy API)",
            "```yaml",
            tool_metadata_yaml,
            "```",
        ]
    parts += [
        "",
        (
            "Return JSON matching the provided schema. Fill every field."
            " Use valid YAML in all *_yml / content fields. Quote strings"
            " containing colons, braces or other non-alphanumeric chars."
            " Template any Galaxy links with '{{ galaxy_base_url }}'."
            " Do NOT wrap template variables in"
            " '{% verbatim %}...{% endverbatim %}' tags - just use the"
            " double-brace syntax literally (e.g. {{ galaxy_base_url }})."
        ),
    ]
    return "\n".join(parts)


def call_openai(
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """Call the OpenAI Responses API and return parsed JSON."""
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        raise AIGenerationError(
            "OPENAI_API_KEY is not configured in Django settings."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AIGenerationError(
            "The 'openai' package is not installed."
        ) from exc

    client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)
    logger.info("Calling OpenAI Responses API to generate Lab content")
    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=system_prompt,
            input=user_prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "galaxy_lab_content",
                    "strict": True,
                    "schema": RESPONSE_SCHEMA,
                },
            },
        )
    except Exception as exc:
        raise AIGenerationError(
            f"OpenAI request failed: {exc}"
        ) from exc

    content = response.output_text
    if not content:
        raise AIGenerationError(
            "OpenAI returned an empty response."
        )
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIGenerationError(
            f"OpenAI returned invalid JSON: {exc}"
        ) from exc


def generate_lab_content(
    lab_name: str,
    reference_md: str,
    job_id: str = '',
) -> dict:
    """Generate Galaxy Lab content from a reference Markdown document.

    Returns a dict matching :data:`RESPONSE_SCHEMA` which the caller can
    use to write files into a Lab content folder.

    If *job_id* is supplied, progress updates are written to Redis so the
    web frontend can display them in real time.
    """
    instructions = INSTRUCTIONS_PATH.read_text()
    tool_ids = extract_tool_ids(reference_md)
    logger.info(
        "Extracted %d tool IDs from reference Markdown",
        len(tool_ids),
    )
    publish_progress(
        job_id,
        f"Extracted {len(tool_ids)} tool IDs from reference",
    )

    publish_progress(job_id, "Fetching tool metadata from Galaxy API")
    tool_metadata_yaml = fetch_tool_inputs.fetch_tools(tool_ids)
    publish_progress(job_id, "Building prompt for OpenAI")

    user_prompt = build_user_prompt(
        lab_name=lab_name,
        reference_md=reference_md,
        tool_metadata_yaml=tool_metadata_yaml,
        instructions=instructions,
    )

    publish_progress(
        job_id,
        "Sending request to OpenAI (this could take 5 minutes - please keep"
        " this tab open)")
    result = call_openai(SYSTEM_PROMPT, user_prompt)
    publish_progress(job_id, "AI content generated — building ZIP archive")
    return result
