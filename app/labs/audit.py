"""Tool auditing functionality using bioblend."""

import logging
import re
import concurrent.futures
from urllib.parse import parse_qs, urlparse
from typing import List, Dict, Tuple

from bioblend.galaxy import GalaxyInstance

from django.conf import settings
from django.template import (
    RequestContext,
    Template,
)

from labs.cache import WebCache

logger = logging.getLogger('django')


def perform_template_audit(
    template_str: str,
    context: Dict,
    request=None
) -> Tuple[str, Dict]:
    """Perform tool audit on template and return updated template and context.

    Args:
        template_str: The rendered HTML template string
        context: Template context dictionary
        request: Django request object (optional)

    Returns:
        Tuple of (updated_template_str, updated_context)
    """
    # Check if audit is requested
    if not request or 'audit' not in request.GET:
        return template_str, context

    # Add audit flag to context
    context['audit'] = True

    # Extract tool links from the template
    tool_links = extract_tool_links(template_str)

    if tool_links:
        galaxy_url = context.get('galaxy_base_url')
        if galaxy_url:
            try:
                # Perform the audit
                audit_results = audit_tools_concurrent(
                    galaxy_url, tool_links
                )

                # Add audit results to context
                context['audit'] = True
                context['audit_results'] = audit_results
                context['audit_summary'] = {
                    'total_tools': len(tool_links),
                    'working_tools': sum(
                        1 for r in audit_results.values() if r['exists']
                    ),
                    'broken_tools': sum(
                        1 for r in audit_results.values() if not r['exists']
                    ),
                }

            except Exception as e:
                logger.error(f"Error during tool auditing: {e}")
                # Continue with audit error
                context['audit'] = True
                context['audit_error'] = str(e)
        else:
            logger.warning("No galaxy_base_url found for tool auditing")
            # Still show audit interface with warning
            context['audit'] = True
            context['audit_error'] = "No Galaxy server URL found"
    else:
        # No tool links found, still show audit interface
        context['audit'] = True
        context['audit_results'] = {}
        context['audit_summary'] = {
            'total_tools': 0,
            'working_tools': 0,
            'broken_tools': 0,
        }

    template_str = add_audit_template_tags(template_str)
    t = Template(template_str)
    template_str = t.render(RequestContext(request, context))

    return template_str, context


def add_audit_template_tags(template_str: str) -> str:
    """Add audit-specific template tags to the template string.

    Insert audit_tags after the first </section>

    Args:
        template_str: The rendered HTML template string
    """
    audit_tags = """
    {% if audit %}
    {% include 'labs/snippets/audit.html' %}
    {% endif %}
    """
    index = template_str.find("</section>")
    if index != -1:
        template_str = (
            template_str[: index + len("</section>")]
            + audit_tags
            + template_str[index + len("</section>") :]
        )
    return template_str


def extract_tool_links(html_content: str) -> List[Dict[str, str]]:
    """Extract all tool links from HTML content.

    Args:
        html_content: The final rendered HTML template string

    Returns:
        List of dicts with 'url', 'tool_id', and 'link_text' keys
    """
    tool_links = []

    # Find all href attributes that contain tool_id=
    href_pattern = r'href="([^"]*tool_id=[^"]*)"'
    matches = re.findall(href_pattern, html_content)

    for url in matches:
        # Parse the URL to extract tool_id
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        if 'tool_id' in query_params:
            tool_id = query_params['tool_id'][0]

            # Find the link text by looking for the actual <a> tag
            link_pattern = rf'<a[^>]*href="{re.escape(url)}"[^>]*>([^<]*)</a>'
            link_match = re.search(link_pattern, html_content)
            link_text = link_match.group(1).strip() if link_match else tool_id

            tool_links.append({
                'url': url,
                'tool_id': tool_id,
                'link_text': link_text or tool_id
            })

    return tool_links


def check_tool_exists(
    galaxy_url: str,
    tool_id: str,
    api_key: str = None
) -> Tuple[str, bool, str]:
    """Check if a tool exists on the Galaxy server.

    Args:
        galaxy_url: Base URL of the Galaxy server
        tool_id: Tool ID to check
        api_key: Optional API key for authentication

    Returns:
        Tuple of (tool_id, exists, error_message)
    """
    # Create cache key for this tool check
    cache_key = f"{galaxy_url}?tool_id={tool_id}"

    # Try to get cached result
    cached_result = WebCache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"Cache HIT for tool check: {tool_id}")
        return cached_result

    logger.debug(f"Cache MISS for tool check: {tool_id}")
    try:
        # Create Galaxy instance
        gi = GalaxyInstance(galaxy_url, key=api_key)

        # Try to get tool information
        try:
            gi.tools.show_tool(tool_id)
            result = (tool_id, True, "")
        except Exception as e:
            # Tool doesn't exist or is not accessible
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                result = (tool_id, False, "Tool not found")
            else:
                result = (
                    tool_id,
                    False,
                    f"Error checking tool: {error_msg}"
                )

    except Exception as e:
        result = (tool_id, False, f"Connection error: {str(e)}")

    # Cache the result
    WebCache.put(cache_key, result, timeout=settings.BIOBLEND_CACHE_TTL)

    return result


def audit_tools_concurrent(
    galaxy_url: str,
    tool_links: List[Dict[str, str]],
    api_key: str = None,
    max_workers: int = 10
) -> Dict[str, Dict]:
    """Audit all tool links using ThreadPoolExecutor for concurrency.

    Args:
        galaxy_url: Base URL of the Galaxy server
        tool_links: List of tool link dictionaries
        api_key: Optional API key for authentication
        max_workers: Maximum number of concurrent workers

    Returns:
        Dict mapping tool_id to audit results
    """
    if not tool_links:
        return {}

    results = {}

    # Use ThreadPoolExecutor to run blocking bioblend calls concurrently
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:
        # Submit all tool checks
        future_to_tool = {
            executor.submit(
                check_tool_exists,
                galaxy_url,
                tool_link['tool_id'],
                api_key
            ): tool_link
            for tool_link in tool_links
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_tool):
            tool_link = future_to_tool[future]
            try:
                tool_id, exists, error_message = future.result()
                results[tool_id] = {
                    'tool_id': tool_id,
                    'url': tool_link['url'],
                    'link_text': tool_link['link_text'],
                    'exists': exists,
                    'error': error_message
                }
            except Exception as e:
                logger.error(
                    f"Error checking tool {tool_link['tool_id']}: {e}"
                )
                results[tool_link['tool_id']] = {
                    'tool_id': tool_link['tool_id'],
                    'url': tool_link['url'],
                    'link_text': tool_link['link_text'],
                    'exists': False,
                    'error': f"Unexpected error: {str(e)}"
                }

    return results
