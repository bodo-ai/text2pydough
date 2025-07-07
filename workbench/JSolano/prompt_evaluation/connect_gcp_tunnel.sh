#!/bin/bash

# This script opens a secure tunnel to a GCP instance using IAP TCP forwarding.
# It's based on the principles of secure connections outlined in Google Cloud documentation.
# Ref: https://cloud.google.com/iap/docs/using-tcp-forwarding

# --- Configuration ---
# !!! IMPORTANT !!!
# Please set the following environment variables or replace the placeholders below.
PROJECT_ID="solid-drive-448717-p8"
ZONE="us-central1-a" # e.g., us-central1-a
INSTANCE_NAME="labeling-c"
LOCAL_PORT="2024"
REMOTE_PORT="2024"

# --- Pre-flight Checks ---
if [ "$PROJECT_ID" == "your-gcp-project-id" ]; then
    echo "❌ Error: GCP_PROJECT_ID is not set."
    echo "Please set the GCP_PROJECT_ID environment variable or edit this script."
    exit 1
fi

if [ "$ZONE" == "your-gcp-zone" ]; then
    echo "❌ Error: GCP_ZONE is not set."
    echo "Please set the GCP_ZONE environment variable or edit this script."
    exit 1
fi

echo "--- Tunnel Configuration ---"
echo "Project:      $PROJECT_ID"
echo "Zone:         $ZONE"
echo "Instance:     $INSTANCE_NAME"
echo "Local Port:   $LOCAL_PORT"
echo "Remote Port:  $REMOTE_PORT"
echo "--------------------------"
echo ""
echo "⚠️  IMPORTANT: Make sure your service on the VM is bound to 0.0.0.0:$REMOTE_PORT"
echo "   Services bound only to 127.0.0.1 won't be accessible via IAP tunneling."
echo ""
echo "   For example, if running a Python server:"
echo "   ✅ Good: uvicorn.run(app, host='0.0.0.0', port=$REMOTE_PORT)"
echo "   ❌ Bad:  uvicorn.run(app, host='127.0.0.1', port=$REMOTE_PORT)"
echo ""
echo "�� Attempting to open SSH tunnel via IAP..."
echo "If this is your first time, you may be prompted to log in or install components."
echo ""
echo "🔗 Once the tunnel is active, you can access the remote service at:"
echo "http://localhost:$LOCAL_PORT"
echo ""
echo "Press Ctrl+C to close the tunnel."
echo ""

# --- Establish Tunnel ---
# Use the correct gcloud compute ssh port forwarding syntax from Google Cloud documentation.
# This command creates an SSH tunnel that forwards local traffic to the remote VM.
# The -- separator passes the SSH flags directly to the underlying ssh command.
gcloud compute ssh "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    -- -NL "$LOCAL_PORT:localhost:$REMOTE_PORT"

exit_code=$?
echo ""
if [ $exit_code -ne 0 ]; then
    echo "❌ Tunnel failed with exit code $exit_code"
    echo ""
    echo "🔍 Common troubleshooting steps:"
    echo "1. Ensure the service is running on the VM and bound to 0.0.0.0:$REMOTE_PORT"
    echo "2. Check if you have the required IAM permissions (IAP-secured Tunnel User)"
    echo "3. Verify the firewall allows IAP traffic (35.235.240.0/20 -> port 22 for SSH)"
    echo "4. Try connecting to the VM via SSH to check the service:"
    echo "   gcloud compute ssh $INSTANCE_NAME --project=$PROJECT_ID --zone=$ZONE"
    echo "   Then run: sudo netstat -tlnp | grep :$REMOTE_PORT"
else
    echo "✅ Tunnel closed successfully."
fi 