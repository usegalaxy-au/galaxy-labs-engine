-- $ sudo apt install lsyncd
-- $ ./sync.sh  # One-way sync to remote


-- Add sync config here

HOST     = 'dev.gvl.org.au'                  -- Remote host
USER     = 'cameron'                 -- Remote user
SRC_DIR  = '/home/cameron/dev/galaxy/galaxy-labs-engine/scripts/workflow_monitor/'  -- Trailing slash syncs dir contents only
DEST_DIR = '/home/cameron/labs_workflow_monitor'        -- Remote directory to sync to
RSA_KEY  = '~/.ssh/qcif'
EXCLUDE  = {
    '.git' ,
    'sync.sh',
    '.lsyncd.lua',
    'nohup.out',
    '*.log',
    'venv/'
}


-- Shouldn't need to touch this:

settings {
    logfile = "/var/log/lsyncd/lsyncd.log",
    statusFile = "/var/log/lsyncd/lsyncd-status.log",
    statusInterval = 20
}

sync {
  default.rsyncssh,
  delay = 3,                    -- Sync delay after file change
  host = HOST,
  source = SRC_DIR,
  targetdir = DEST_DIR,
  exclude = EXCLUDE,
  rsync = {
    rsh = "/usr/bin/ssh -l " .. USER .. " -i " .. RSA_KEY
  }
}
