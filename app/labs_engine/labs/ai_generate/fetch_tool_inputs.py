"""Fetch required data inputs for Galaxy tools and format as Lab YAML.

Given a list of tool IDs, query the Galaxy API and extract each tool's
required data inputs (label + accepted datatypes). Output is formatted as
a YAML snippet ready to paste into a Lab section file's `inputs:` block.

This module can be used as a CLI (see generate/fetch_tool_inputs.py) or
imported from Python code via :func:`fetch_tools`.
"""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_SERVERS = [
    "https://usegalaxy.org",
    "https://usegalaxy.eu",
]
CURL_TIMEOUT = 60
MAX_WORKERS = 8


def fetch_tool(
    tool_id: str,
    servers: list[str],
) -> tuple[str, dict | None]:
    """Query each server in turn until one returns valid tool JSON."""
    for server in servers:
        url = f"{server}/api/tools/{tool_id}?io_details=true"
        try:
            result = subprocess.run(
                ["curl", "-sL", "--max-time", str(CURL_TIMEOUT), url],
                capture_output=True,
                text=True,
                timeout=CURL_TIMEOUT + 10,
            )
        except subprocess.TimeoutExpired:
            continue
        if result.returncode != 0 or not result.stdout:
            continue
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "inputs" in data:
            return (tool_id, data)
    return (tool_id, None)


def extract_required_data_inputs(inputs: list) -> list[dict]:
    """Recursively extract required data inputs from a Galaxy tool schema.

    Recurses into `repeat`, `section` and `conditional` inputs. Skips
    optional data inputs and non-data params. `data_collection` labels are
    suffixed with " (collection)" to indicate the expected input shape.
    """
    results = []
    for inp in inputs or []:
        itype = inp.get("type")
        if itype in ("data", "data_collection"):
            if inp.get("optional", False):
                continue
            label = inp.get("label") or inp.get("name") or ""
            if itype == "data_collection":
                label = f"{label} (collection)"
            results.append({
                "label": label,
                "datatypes": inp.get("extensions", []),
            })
        elif itype in ("repeat", "section"):
            results.extend(
                extract_required_data_inputs(inp.get("inputs", []))
            )
        elif itype == "conditional":
            for case in inp.get("cases", []):
                results.extend(
                    extract_required_data_inputs(case.get("inputs", []))
                )
    return results


def dedupe_inputs(inputs: list[dict]) -> list[dict]:
    """Remove duplicate inputs by (label, datatypes)."""
    seen = set()
    out = []
    for inp in inputs:
        key = (inp["label"], tuple(inp["datatypes"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(inp)
    return out


def format_tool_yaml(
    tool_id: str,
    data: dict | None,
) -> str:
    """Format a single tool's details as a YAML snippet."""
    if data is None:
        return f"{tool_id}:\n  NOT FOUND\n"

    description = (data.get("description") or "").strip()
    inputs = dedupe_inputs(
        extract_required_data_inputs(data.get("inputs", []))
    )

    lines = [f"{tool_id}:"]
    if description:
        lines.append(f"  description: {description}")
    if not inputs:
        lines.append("  inputs: []  # no required data inputs")
    else:
        lines.append("  inputs:")
        for inp in inputs:
            lines.append(f"    - label: {inp['label']}")
            if inp["datatypes"]:
                lines.append("      datatypes:")
                for dt in inp["datatypes"]:
                    lines.append(f"        - {dt}")
            else:
                lines.append("      datatypes: []")
    return "\n".join(lines) + "\n"


def fetch_tools(
    tool_ids: list[str],
    servers: list[str] = None,
) -> str:
    """Fetch metadata for multiple tool IDs and return a YAML snippet.

    This is the main public entry point for importing this module from
    other Python code (e.g. the AI lab generator).
    """
    servers = servers or DEFAULT_SERVERS
    if not tool_ids:
        return ""
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        results = list(
            ex.map(lambda t: fetch_tool(t, servers), tool_ids)
        )
    return "\n".join(
        format_tool_yaml(tool_id, data) for tool_id, data in results
    )


def load_tool_ids(sources: list[str]) -> list[str]:
    """Load tool IDs from files (if they exist) or treat as literal IDs."""
    tool_ids = []
    for src in sources:
        path = Path(src)
        if path.is_file():
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Allow "- tool_id" list format
                if line.startswith("- "):
                    line = line[2:].strip()
                tool_ids.append(line)
        else:
            tool_ids.append(src)
    return tool_ids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
    )
    parser.add_argument(
        "sources",
        nargs="+",
        help=(
            "Tool IDs, or paths to files containing tool IDs"
            " (one per line; '#' comments allowed)."
        ),
    )
    parser.add_argument(
        "--server",
        action="append",
        default=None,
        help=(
            "Galaxy server base URL to query (may be repeated)."
            f" Defaults to: {', '.join(DEFAULT_SERVERS)}"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tool_ids = load_tool_ids(args.sources)
    if not tool_ids:
        print("No tool IDs provided.", file=sys.stderr)
        return 1

    print(fetch_tools(tool_ids, servers=args.server))
    return 0


if __name__ == "__main__":
    sys.exit(main())
