"""RQ background tasks for Lab generation."""

import logging

from rq import get_current_job

from . import bootstrap

logger = logging.getLogger('django')


def run_bootstrap_lab(form_data: dict, output_dir: str) -> dict:
    """Generate a Lab ZIP archive in a background worker.

    Accepts a plain-dict payload (no Django UploadedFile objects — the
    caller must convert those to serializable equivalents before
    enqueuing) and the pre-determined *output_dir* path string so the
    worker writes to an agreed-upon location.

    Returns a dict with ``relpath`` (ZIP path relative to
    ``settings.INTERNAL_ROOT``) and ``lab_name`` for the download
    filename.
    """
    job = get_current_job()
    job_id = job.id if job else ''
    lab_name = form_data.get('lab_name', 'lab')

    logger.info(
        "RQ worker: generating Lab '%s' → %s",
        lab_name,
        output_dir,
    )
    try:
        relpath = bootstrap.lab(
            form_data,
            output_dir=output_dir,
            job_id=job_id,
        )
    except Exception:
        logger.exception(
            "RQ worker: Lab generation failed for '%s'", lab_name)
        raise
    return {
        'relpath': str(relpath),
        'lab_name': lab_name,
    }
