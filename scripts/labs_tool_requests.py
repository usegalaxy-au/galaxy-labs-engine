"""Analyse Nginx log files to extract user metrics.

Expects a filtered access log including only lines matching ALL of:
    - grep -v 'https://usegalaxy'
    - grep '/build'
    - grep '/api/tools/toolshed.g2.bx.psu.edu'

"""

import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict
from datetime import datetime
from pathlib import Path


DATA_DIR = Path('~/Downloads/labs_nginx_logs').expanduser()
tools_path = DATA_DIR / 'labs_tool_access_20250415-20250817.log'
csv_tools = DATA_DIR / 'lab_tools.csv'
LABS_TO_PLOT = [
    'https://genome.usegalaxy.org.au',
    'https://proteomics.usegalaxy.org.au',
    'https://singlecell.usegalaxy.org.au',
    'https://microbiology.usegalaxy.org.au',
]


def count_lab_tool_usage():
    visits = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    with tools_path.open() as f:
        for line in f:
            if 'GET' in line and '/build' in line:
                continue
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
            match = re.search(r'(toolshed.+)/build', line)
            if not match:
                continue
            tool_id = '/'.join(match.group(1).split('/')[3:5])
            visits[lab][tool_id][dt] += 1
            visits[lab]['Total'][dt] += 1
    return visits


def plot_tool_requests(lab_tool_requests, name):
    top_5_tools = sorted(
        lab_tool_requests.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True,
    )[:6]  # includes "total"
    fig, axes = plt.subplots(
        len(top_5_tools),
        1,
        figsize=(10, 10),
        sharex=True,
    )
    if len(top_5_tools) == 1:
        axes = [axes]  # Ensure axes is iterable when there's only one subplot
    for ax, (tool, data) in zip(axes, top_5_tools):
        total_count = sum(data.values())
        dates = sorted(data.keys())
        counts = [data[date] for date in dates]
        ax.bar(dates, counts)
        ax.set_title(f"{tool} (total {total_count} requests)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.set_ylabel('Count')
    fig.autofmt_xdate()  # Auto rotate date labels
    ax.set_xlabel('Date')
    fig.suptitle(f'{name.title()} Lab tool usage', fontsize=20)
    fig.tight_layout()
    fig.savefig(DATA_DIR / f'{name}_lab_tool_usage.png')


def main():
    tool_requests = count_lab_tool_usage()
    with csv_tools.open('w') as f:
        f.write('lab,tool_id,datetime,count\n')
        for lab, tools in tool_requests.items():
            for tool_id, dt in tools.items():
                for date, count in dt.items():
                    f.write(f'{lab},{tool_id},{date},{count}\n')

    for url in LABS_TO_PLOT:
        subdomain = url.split('//')[1].split('.')[0]
        plot_tool_requests(tool_requests[url], subdomain)


if __name__ == '__main__':
    main()
