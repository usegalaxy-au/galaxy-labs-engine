#!/usr/bin/bash

# POST Nginx logs with filename format:
# labs-tools.access.log-20250415
# labs-welcome.access.log-20260214

# Like:
# curl -X POST \
#     -F "file=@/mnt/var/log/nginx/labs-welcome.access.log-20260124" \
#     -F "log_type=nginx_welcome" \
#     -H 'X-API-KEY: ***' \
#     https://dev-labs.gvl.org.au/reporting/api/logs/upload

LOG_ROOT=/mnt/var/log/nginx
PATTERN_WELCOME='labs-welcome.access.log-*'
PATTERN_TOOL='labs-tools.access.log-*'
SKIP_PATTERN='*.gz'
FROM_DATE='20260126'
SLEEP_INTERVAL=10
URL=https://dev-labs.gvl.org.au/reporting/api/logs/upload
API_KEY='***'


post_log() {
    local path=$1
    local log_type=$2
    local filename
    filename=$(basename "$path")

    # Skip files matching SKIP_PATTERN
    if [[ $filename == $SKIP_PATTERN ]]; then
        return
    fi

    # Check read permission
    if [[ ! -r $path ]]; then
        echo "Error: cannot read $path (permission denied)" >&2
        exit 1
    fi

    # Extract date suffix (last 8 characters) and filter by FROM_DATE
    local file_date=${filename: -8}
    if [[ $file_date < $FROM_DATE ]]; then
        echo "Skipping $filename (before $FROM_DATE)"
        return
    fi

    echo "POSTing file $path..."
    curl -X POST \
        -F "file=@$(realpath "$path")" \
        -F "log_type=$log_type" \
        -H "X-API-KEY: $API_KEY" \
        "$URL"

    sleep $SLEEP_INTERVAL
}

for path in $LOG_ROOT/$PATTERN_WELCOME; do
    post_log "$path" nginx_welcome
done

for path in $LOG_ROOT/$PATTERN_TOOL; do
    post_log "$path" nginx_tool
done
