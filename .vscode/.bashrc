source ~/.bashrc
source "/home/cameron/dev/galaxy/galaxy-labs-engine/venv/bin/activate"

echo ""
echo "External URL for your dev lab:"
echo http://127.0.0.1:8000/lab/export?content_root=${GITPOD_WORKSPACE_URL}/static/dev-lab/base.yml
echo ""
