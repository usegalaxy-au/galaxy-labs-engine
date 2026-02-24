"""Collect workflow invocation data from Nginx logs and Galaxy database.

This script will receive a stream of Galaxy's Nginx logs through stdin.
It will extract IDs of invoked workflows, and then:

- Decode that StoredWorkflow ID using Galaxy's IdEncodingHelper algorithm
- Query the Galaxy (Postgresql) database with SQLAlchemy to extract the name
  and UUID of the StoredWorkflow instance
- If possible, also extract the user ID so we can keep track of user count
- Append the invocation data to a CSV file, along with the domain name of the
  request

Example Nginx log line:

POST /api/workflows/<WORKFLOW_ID>/invocations HTTP/1.1" 200 215 \
"https://genome.usegalaxy.org.au/workflows/run?id=e4d20320d61c4f83"



Usage:
    tail -f nginx_access.log \
    | python extract_workflow_invocations.py -o invocations.csv

Environment variables (can be set in .env file):
    GALAXY_ID_SECRET       - Galaxy's id_secret for decoding encoded IDs
    GALAXY_DATABASE_URL    - SQLAlchemy connection string for Galaxy's database
"""

import argparse
import codecs
import csv
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from Crypto.Cipher import Blowfish
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

LOG_FORMAT = '%(levelname)s: %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    'datetime',
    'domain',
    'workflow_id',
    'workflow_name',
    'workflow_uuid',
    'user_id',
]

# Regex patterns for Nginx combined log format
INVOCATION_PATTERN = re.compile(
    r'POST /api/workflows/([a-f0-9]+)/invocations'
)
DATETIME_PATTERN = re.compile(
    r'\[(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})'
)
DATETIME_FORMAT = '%d/%b/%Y:%H:%M:%S'
DOMAIN_PATTERN = re.compile(
    r'https?://([^/"\s]+)'
)

WORKFLOW_QUERY = text("""
    SELECT sw.id, sw.name, sw.user_id, w.uuid
    FROM stored_workflow sw
    LEFT JOIN workflow w ON sw.latest_workflow_id = w.id
    WHERE sw.id = :id
""")


def decode_galaxy_id(encoded_id: str, id_cipher: Blowfish) -> int:
    """Decode a Galaxy hex-encoded ID to an integer database ID.

    Replicates Galaxy's IdEncodingHelper.decode_id algorithm:
    hex decode -> Blowfish ECB decrypt -> strip padding -> int.
    """
    raw = codecs.decode(encoded_id, 'hex')
    decrypted = id_cipher.decrypt(raw)
    return int(decrypted.decode('utf-8').lstrip('!'))


def parse_log_line(line: str) -> dict | None:
    """Extract workflow invocation data from an Nginx log line.

    Returns a dict with 'encoded_id', 'datetime', and 'domain' keys,
    or None if the line does not match a workflow invocation request.
    """
    inv_match = INVOCATION_PATTERN.search(line)
    if not inv_match:
        return None

    dt_match = DATETIME_PATTERN.search(line)
    if not dt_match:
        logger.warning("No datetime found in line: %s", line.strip())
        return None
    dt = datetime.strptime(dt_match.group(1), DATETIME_FORMAT)

    domain_match = DOMAIN_PATTERN.search(line)
    domain = domain_match.group(1) if domain_match else 'unknown'

    return {
        'encoded_id': inv_match.group(1),
        'datetime': dt.strftime('%Y-%m-%d %H:%M:%S'),
        'domain': domain,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-o', '--output',
        required=True,
        type=Path,
        help='CSV output file path (appends if file exists)',
    )
    args = parser.parse_args()

    id_secret = os.environ.get('GALAXY_ID_SECRET')
    database_url = os.environ.get('GALAXY_DATABASE_URL')

    if not id_secret:
        logger.error("GALAXY_ID_SECRET environment variable is required")
        sys.exit(1)
    if not database_url:
        logger.error("GALAXY_DATABASE_URL environment variable is required")
        sys.exit(1)

    id_cipher = Blowfish.new(
        id_secret.encode('utf-8'),
        mode=Blowfish.MODE_ECB,
    )
    engine = create_engine(database_url)

    write_header = not args.output.exists()

    with (
        engine.connect() as conn,
        args.output.open('a', newline='') as csvfile,
    ):
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(CSV_COLUMNS)

        for line in sys.stdin:
            parsed = parse_log_line(line)
            if not parsed:
                continue

            try:
                workflow_id = decode_galaxy_id(
                    parsed['encoded_id'], id_cipher)
            except (ValueError, TypeError) as e:
                logger.warning(
                    "Failed to decode ID '%s': %s",
                    parsed['encoded_id'], e,
                )
                continue

            result = conn.execute(
                WORKFLOW_QUERY,
                {'id': workflow_id},
            ).fetchone()

            if not result:
                logger.warning(
                    "StoredWorkflow %d not found in database",
                    workflow_id,
                )
                continue

            _, name, user_id, uuid = result
            writer.writerow([
                parsed['datetime'],
                parsed['domain'],
                workflow_id,
                name,
                str(uuid) if uuid else '',
                user_id,
            ])
            csvfile.flush()


if __name__ == '__main__':
    main()
