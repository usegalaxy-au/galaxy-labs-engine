"""Analyse Nginx log files to extract user metrics."""

import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
from datetime import datetime
from pathlib import Path


DATA_DIR = Path('~/Downloads/nginx_logs').expanduser()
visits_path = DATA_DIR / 'labs-welcome.access.log'
csv_visits = DATA_DIR / 'lab_visits.csv'


def count_lab_visits():
    visits = defaultdict(lambda: defaultdict(int))
    with visits_path.open() as f:
        for line in f:
            dt = datetime.strptime(
                re.search(
                    r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}',
                    line,
                ).group(0),
                '%d/%b/%Y:%H:%M:%S',
            )
            match = re.search(
                r'https://\w+\.usegalaxy\.org\.au', line)
            if not match:
                continue
            lab = match.group(0)
            visits[lab][dt] += 1
    return visits


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
    with csv_visits.open('w') as f:
        f.write('lab,datetime,count\n')
        for lab, dt in visits.items():
            for date, count in dt.items():
                datestr = date.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f'{lab},{datestr},{count}\n')

    genome_visits = visits['https://genome.usegalaxy.org.au']
    proteomics_visits = visits['https://proteomics.usegalaxy.org.au']
    singlecell_visits = visits['https://singlecell.usegalaxy.org.au']
    plot_visits(genome_visits, 'genome')
    plot_visits(proteomics_visits, 'proteomics')
    plot_visits(singlecell_visits, 'singlecell')


if __name__ == '__main__':
    main()
