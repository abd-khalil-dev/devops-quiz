#!/usr/bin/env bash
# Destroys everything Terraform created. Billing stops.
set -euo pipefail
cd "$(dirname "$0")/.."

MY_IP="$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')/32"
read -r -p "This deletes the server, its data and the leaderboard. Type 'yes' to continue: " ok
[ "$ok" = "yes" ] || { echo "Cancelled."; exit 1; }

terraform -chdir=terraform destroy -auto-approve -input=false -var="my_ip=$MY_IP"
rm -f ansible/inventory.ini
echo "Server destroyed. Billing stopped."
