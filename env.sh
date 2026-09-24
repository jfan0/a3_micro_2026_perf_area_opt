export HEAD_IP=$(hostname -I | awk '{print $1}')

export TS_AUTHKEY=$(cat auth/tailscale_key)

export GCP_PROJECT=gcp_project_name
export GCP_SSH_KEY=/path/to/ssh_key