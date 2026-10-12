#!/usr/bin/env bash
# Creates the AWS server, sets up k3s, and deploys the quiz. Safe to run again.
set -euo pipefail
cd "$(dirname "$0")/.."

KEY=~/.ssh/quiz-aws
SSH_OPTS="-i $KEY -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5 -o LogLevel=ERROR"
MY_IP="$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')/32"

echo "==> 1/5 Terraform: creating the server"
terraform -chdir=terraform init -input=false >/dev/null
terraform -chdir=terraform apply -auto-approve -input=false -var="my_ip=$MY_IP"
IP="$(terraform -chdir=terraform output -raw public_ip)"

echo "==> 2/5 Waiting for SSH on $IP"
ready=""
for i in $(seq 1 40); do
  if ssh $SSH_OPTS ubuntu@"$IP" true 2>/dev/null; then ready=yes; break; fi
  sleep 5
done
[ -n "$ready" ] || { echo "SSH did not come up. Check the Security Group and your IP."; exit 1; }

echo "==> 3/5 Ansible: installing k3s and Helm"
cat > ansible/inventory.ini <<EOF
[quiz]
server ansible_host=$IP ansible_user=ubuntu ansible_ssh_private_key_file=$KEY
EOF
(cd ansible && ansible-playbook playbook.yml)

echo "==> 4/5 Helm: deploying the quiz"
ssh $SSH_OPTS ubuntu@"$IP" "IP=$IP bash -s" <<'REMOTE'
set -euo pipefail
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
if [ -d "$HOME/devops-quiz/.git" ]; then
  git -C "$HOME/devops-quiz" pull --ff-only
else
  git clone https://github.com/abd-khalil-dev/devops-quiz.git "$HOME/devops-quiz"
fi
kubectl get namespace quiz >/dev/null 2>&1 || kubectl create namespace quiz
kubectl get secret db-secret -n quiz >/dev/null 2>&1 || \
  kubectl create secret generic db-secret -n quiz --from-literal=POSTGRES_PASSWORD="$(openssl rand -hex 16)"
helm upgrade --install quiz "$HOME/devops-quiz/helm/quiz" -n quiz \
  --set ingress.className=traefik --set ingress.host="quiz.$IP.nip.io" \
  --wait --timeout 8m
kubectl get pods -n quiz
REMOTE

echo
echo "==> 5/5 Done"
echo "Open:  http://quiz.$IP.nip.io"
echo "SSH:   ssh -i $KEY ubuntu@$IP"
echo "Stop the bill when you finish: scripts/down.sh"
