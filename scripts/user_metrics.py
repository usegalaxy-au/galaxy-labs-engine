"""Analyse Nginx log files to extract user metrics.

Expects a filtered access log including only lines matching ALL of:
    - grep -v 'https://usegalaxy'
    - grep '/welcome'

"""

import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
from datetime import datetime
from pathlib import Path


DATA_DIR = Path('~/Downloads/labs_nginx_logs').expanduser()
VISITS_PATH = DATA_DIR / 'labs-welcome-combined.log'
CSV_VISITS = DATA_DIR / 'lab_visits.csv'
BOTS_PATTERNS = [
    r'googlebot/[\d.]+',
    r'ahrefsbot/[\d.]+',
    r'bitsightbot/[\d.]*',
    r'bingbot/[\d.]+   ',
    r'search\.marginalia\.nu',
    r'\(.*?Android.*?\)\s.*?googlebot/[\d.]+',
]
LABS_TO_PLOT = [
    'https://genome.usegalaxy.org.au',
    'https://proteomics.usegalaxy.org.au',
    'https://singlecell.usegalaxy.org.au',
    'https://microbiology.usegalaxy.org.au',
]


def count_lab_visits():
    visits = defaultdict(lambda: defaultdict(int))
    with VISITS_PATH.open() as f:
        for line in f:
            lab = get_lab_name(line)
            if not lab:
                continue
            dt = datetime.strptime(
                re.search(
                    r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}',
                    line,
                ).group(0),
                '%d/%b/%Y:%H:%M:%S',
            )
            visits[lab][dt] += 1
    return visits


def get_lab_name(line):
    """Determine if the line represents a genuine visit."""
    lab_name = re.search(
        r'https://\w+\.usegalaxy\.org\.au',
        line,
    )
    if not lab_name:
        return None

    if re.search(r'\b(?:' + '|'.join(BOTS_PATTERNS) + r')\b', line):
        return None

    return lab_name.group(0)


def plot_visits(lab_visits, name):
    dates = sorted(lab_visits.keys())
    counts = [lab_visits[date] for date in dates]
    plt.figure(figsize=(16, 6))
    plt.bar(dates, counts)
    plt.gcf().autofmt_xdate()  # Auto rotate date labels
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.title(f'{name.title()} Lab visits')
    plt.tight_layout()
    plt.savefig(DATA_DIR / f'{name}_lab_visits.png')


def main():
    visits = count_lab_visits()
    with CSV_VISITS.open('w') as f:
        f.write('lab,datetime,count\n')
        for lab, dt in visits.items():
            for date, count in dt.items():
                datestr = date.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f'{lab},{datestr},{count}\n')

    for url in LABS_TO_PLOT:
        subdomain = url.split('//')[1].split('.')[0]
        plot_visits(visits[url], subdomain)


if __name__ == '__main__':
    main()
