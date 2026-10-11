import os
import random
import socket
from flask import Flask, jsonify, request

app = Flask(__name__)

# (category, level, question, options, correct option index, interview answer)
RAW = [
    # ---------------- Docker ----------------
    ("Docker", "Basic", "What is the difference between a Docker image and a container?",
     ["An image is a running process and a container is a file",
      "An image is a read-only template and a container is a running instance of it",
      "They are the same thing",
      "An image runs only on Linux and a container runs only on Windows"], 1,
     "An image is a read-only template with your app and its dependencies. A container is a running instance of that image, with a thin writable layer on top."),
    ("Docker", "Intermediate", "What is the difference between CMD and ENTRYPOINT in a Dockerfile?",
     ["ENTRYPOINT sets the main command, and CMD gives default arguments that are easy to override",
      "They are exactly the same",
      "CMD runs at build time and ENTRYPOINT runs at pull time",
      "ENTRYPOINT can only be used in Docker Compose"], 0,
     "ENTRYPOINT defines the program that always runs. CMD supplies default arguments, and anything you add after the image name in docker run replaces CMD. They are often used together."),
    ("Docker", "Intermediate", "Why do we copy requirements.txt and install packages before copying the app code?",
     ["To make the image smaller in every case",
      "To use the layer cache, so packages are not reinstalled when only the code changes",
      "Because pip needs to run first",
      "To run the container as root"], 1,
     "Docker caches each layer. If requirements.txt did not change, the install layer is reused, and your builds become much faster."),
    ("Docker", "Basic", "How do you keep data after a container is removed?",
     ["Use a volume or a bind mount", "Use a bigger image", "Use docker restart", "Use the EXPOSE instruction"], 0,
     "The container filesystem is temporary. Volumes and bind mounts live outside the container, so the data survives."),
    ("Docker", "Intermediate", "What does a multi-stage build help with?",
     ["Running many containers at once",
      "Keeping the final image small by leaving the build tools behind",
      "Building on many servers",
      "Encrypting the image"], 1,
     "You build in one stage and copy only the result into a small final stage, so compilers and build tools never reach production."),
    ("Docker", "Advanced", "Two containers are on the same user-defined Docker network. How can one reach the other?",
     ["By its container or service name, using Docker's built-in DNS",
      "Only by IP address",
      "Through the host's /etc/hosts file",
      "They cannot talk to each other"], 0,
     "A user-defined network has built-in DNS, so a container can call another by name. This is how nginx reaches the backend in Docker Compose."),

    # ---------------- Git ----------------
    ("Git", "Basic", "What is the difference between git fetch and git pull?",
     ["fetch downloads changes without merging, and pull is fetch plus merge",
      "They are the same",
      "pull only works on the main branch",
      "fetch deletes your local changes"], 0,
     "git fetch only updates your remote-tracking branches. git pull is fetch followed by a merge (or a rebase), so it changes your current branch."),
    ("Git", "Intermediate", "What is the difference between git merge and git rebase?",
     ["Merge keeps the real history with a merge commit, and rebase replays your commits on top of another branch for a straight history",
      "Rebase deletes the branch",
      "Merge works only on tags",
      "There is no difference"], 0,
     "Merge keeps the true history. Rebase rewrites your commits on top of the target branch. Never rebase commits that other people have already pulled."),
    ("Git", "Intermediate", "You pushed a secret key to GitHub by mistake. What do you do first?",
     ["Delete the file and commit again",
      "Rotate the secret immediately, then remove it from the history",
      "Make the repo private and do nothing else",
      "Ignore it"], 1,
     "Once pushed, assume it is leaked. Rotate the key first. Then clean the history (for example with git filter-repo) and add the file to .gitignore."),
    ("Git", "Basic", "Which command undoes the last commit but keeps your changes staged?",
     ["git reset --hard HEAD~1", "git reset --soft HEAD~1", "git clean -fd", "git checkout --force"], 1,
     "--soft moves the branch back one commit and keeps your changes staged. --mixed keeps them unstaged. --hard throws them away."),
    ("Git", "Intermediate", "What does git revert do?",
     ["Deletes a commit from the history",
      "Creates a new commit that undoes an earlier commit",
      "Moves the branch pointer back",
      "Resets the working folder"], 1,
     "Revert is safe on shared branches because it adds a new commit instead of rewriting history."),

    # ---------------- CI/CD ----------------
    ("CI/CD", "Basic", "What is the difference between Continuous Delivery and Continuous Deployment?",
     ["Delivery needs a manual approval before production, and Deployment releases automatically",
      "They are the same",
      "Deployment means only testing",
      "Delivery means only building images"], 0,
     "Both keep your code always ready to release. In delivery a person approves the release. In deployment every change that passes the checks goes live automatically."),
    ("CI/CD", "Intermediate", "Where should cloud keys and passwords for a pipeline be stored?",
     ["In the repository code", "In the pipeline's secret store, like GitHub Actions secrets",
      "In the Dockerfile", "In the README"], 1,
     "Secret stores keep values encrypted and hide them in logs. Never commit them. Even better, use short-lived credentials such as OIDC."),
    ("CI/CD", "Intermediate", "Which is a sensible order for pipeline stages?",
     ["Deploy, build, test", "Build, test, scan, push the image, deploy",
      "Test, deploy, build", "Push the image, test, build"], 1,
     "Fail fast: build and test first, scan for problems, publish the artifact once, then deploy that same artifact."),
    ("CI/CD", "Advanced", "Why tag Docker images with a version or commit SHA instead of only using latest?",
     ["It makes the image smaller",
      "Every deployment becomes traceable, and you can roll back to an exact version",
      "Because the latest tag is not allowed",
      "It makes pulling faster"], 1,
     "latest moves every time you push, so you cannot tell what is running. A SHA or version tag gives repeatable deployments and clean rollbacks."),
    ("CI/CD", "Intermediate", "What is a blue-green deployment?",
     ["Two identical environments, and you switch traffic from the old one to the new one",
      "Deploying only at night",
      "Running tests in two colours",
      "A deployment done by two teams"], 0,
     "You deploy to the idle environment, test it, then switch the traffic. If something breaks, you switch back, so rollback is instant."),
    ("CI/CD", "Intermediate", "What is a canary release?",
     ["Releasing to all users at once",
      "Sending a small share of traffic to the new version first",
      "Releasing only to developers",
      "Deleting the old version first"], 1,
     "You show the new version to a small percentage of users, watch the metrics, and increase the traffic only if everything looks healthy."),

    # ---------------- Kubernetes ----------------
    ("Kubernetes", "Basic", "What is a Pod?",
     ["A node in the cluster",
      "The smallest deployable unit, with one or more containers that share network and storage",
      "A type of Service",
      "A Docker image"], 1,
     "Containers in one pod share an IP address and volumes. Usually a pod holds one app container, sometimes with a helper sidecar."),
    ("Kubernetes", "Basic", "Which object does a Deployment use to manage its pods?",
     ["ReplicaSet", "StatefulSet", "DaemonSet", "Ingress"], 0,
     "A Deployment creates a ReplicaSet for each version, and the ReplicaSet keeps the right number of pods. This is also how rollbacks work."),
    ("Kubernetes", "Intermediate", "What is the difference between a liveness probe and a readiness probe?",
     ["Liveness restarts a stuck container, and readiness decides whether the pod gets traffic",
      "They are the same",
      "Readiness restarts the pod and liveness stops the traffic",
      "Both run only at startup"], 0,
     "If liveness fails, the kubelet restarts the container. If readiness fails, the pod is removed from the Service endpoints but is not restarted."),
    ("Kubernetes", "Basic", "What are the three common Service types?",
     ["ClusterIP, NodePort, LoadBalancer", "Pod, Node, Cluster",
      "Ingress, Egress, Gateway", "Public, Private, Hybrid"], 0,
     "ClusterIP is internal only. NodePort opens a port on every node. LoadBalancer asks the cloud for an external load balancer."),
    ("Kubernetes", "Intermediate", "A pod is in CrashLoopBackOff. What do you check first?",
     ["kubectl logs --previous and kubectl describe pod", "Delete the cluster",
      "Add more replicas", "Restart the node"], 0,
     "The container keeps crashing and restarting. The previous container's logs and the Events in describe usually show the reason."),
    ("Kubernetes", "Intermediate", "The pods are Running, but the Service has no Endpoints. What is the most likely cause?",
     ["The Service selector does not match the pod labels", "The image is too big",
      "The node is full", "Helm is missing"], 0,
     "A Service finds pods by label selector. A typo or a mismatch means no pod matches, so Endpoints stays empty."),
    ("Kubernetes", "Intermediate", "When do you use a StatefulSet instead of a Deployment?",
     ["For stateless web servers",
      "For apps that need stable names and their own persistent disk, like databases",
      "To run one-time tasks",
      "To run one pod on every node"], 1,
     "A StatefulSet gives each pod a stable name (db-0, db-1), ordered startup, and its own PVC."),
    ("Kubernetes", "Basic", "What is a ConfigMap for?",
     ["Storing passwords securely", "Keeping non-secret settings outside the container image",
      "Running background jobs", "Balancing traffic"], 1,
     "A ConfigMap lets you change settings without rebuilding the image. Use a Secret for sensitive values."),
    ("Kubernetes", "Intermediate", "What is the difference between a PV and a PVC?",
     ["A PV is the actual storage, and a PVC is a request for that storage",
      "They are the same", "A PVC works only in the cloud", "A PV is used for ConfigMaps"], 0,
     "An admin or a StorageClass provides the PV. A pod's PVC asks for a size and an access mode, and Kubernetes binds the two."),
    ("Kubernetes", "Intermediate", "What is the difference between resource requests and limits?",
     ["The request is what the scheduler reserves, and the limit is the maximum the container may use",
      "They are the same",
      "Limits are used only by the scheduler",
      "Requests are for memory and limits are for CPU"], 0,
     "The scheduler places pods using requests. At runtime, a container that goes over its memory limit is killed (OOMKilled), and CPU use is throttled."),
    ("Kubernetes", "Advanced", "What does an Ingress do?",
     ["Stores secrets",
      "Routes external HTTP and HTTPS traffic to Services using host and path rules",
      "Creates persistent volumes",
      "Schedules pods on nodes"], 1,
     "An Ingress needs an Ingress controller, such as NGINX, to work. It is the front door to many Services behind one address."),
    ("Kubernetes", "Intermediate", "What does kubectl rollout undo do?",
     ["Deletes the Deployment", "Rolls the Deployment back to the previous revision",
      "Restarts all nodes", "Scales the Deployment to zero"], 1,
     "Kubernetes keeps old ReplicaSets, so it can switch back to the previous version quickly."),

    # ---------------- Helm ----------------
    ("Helm", "Basic", "What is Helm?",
     ["A container runtime", "A package manager for Kubernetes", "A CI server", "A monitoring tool"], 1,
     "Helm packages Kubernetes YAML into charts with templates and values, so you can install and upgrade a whole app with one command."),
    ("Helm", "Intermediate", "What is the difference between a chart and a release?",
     ["A chart is the package, and a release is an installed instance of it",
      "They are the same", "A release is a Git tag", "A chart runs only on EKS"], 0,
     "You can install one chart many times with different names and values. Each install is a release with its own history."),
    ("Helm", "Intermediate", "Which command shows the final YAML without installing anything?",
     ["helm template", "helm install --force", "helm pull", "helm list"], 0,
     "helm template renders the manifests locally. It is great for reviewing changes and for checks in CI."),

    # ---------------- Terraform ----------------
    ("Terraform", "Basic", "What is Infrastructure as Code?",
     ["Writing app code in a cloud editor",
      "Managing servers and networks with code files instead of manual clicks",
      "Backing up code to the cloud",
      "Running code on servers"], 1,
     "IaC makes infrastructure repeatable, reviewable in Git, and easy to rebuild."),
    ("Terraform", "Intermediate", "What does the Terraform state file do?",
     ["Stores the logs", "Tracks which real resources Terraform manages",
      "Holds your variables", "Saves your Git history"], 1,
     "Terraform compares your code with the state to plan changes. Keep it in a remote backend and never commit it to Git."),
    ("Terraform", "Basic", "What is the usual Terraform workflow?",
     ["init, plan, apply", "build, test, deploy", "pull, push, merge", "start, stop, restart"], 0,
     "init downloads the providers, plan shows what will change, and apply makes the change. destroy removes everything."),
    ("Terraform", "Intermediate", "Why use a remote backend for Terraform state in a team?",
     ["To make Terraform faster",
      "To share the state safely and stop two people changing it at the same time",
      "To hide variables",
      "To avoid using providers"], 1,
     "A remote backend with locking, for example S3 with state locking, stops two people from running apply together and corrupting the state."),

    # ---------------- Ansible ----------------
    ("Ansible", "Basic", "What does agentless mean in Ansible?",
     ["It has no playbooks",
      "It connects over SSH and needs no agent installed on the servers",
      "It runs without Python",
      "It only works on your own laptop"], 1,
     "Ansible pushes tasks over SSH from your control machine. The managed servers only need Python and SSH."),
    ("Ansible", "Intermediate", "What does idempotent mean for an Ansible task?",
     ["It runs only once a year",
      "Running it many times gives the same result, with no extra changes",
      "It deletes old files",
      "It runs in parallel"], 1,
     "If the package is already installed, the task reports ok and changes nothing. That makes playbooks safe to run again."),
    ("Ansible", "Intermediate", "What is a handler in Ansible?",
     ["A task that runs only when notified, like restarting a service after a config change",
      "A variable file", "An SSH key", "A role folder"], 0,
     "Handlers run at the end of a play, and only if a task changed something and notified them."),

    # ---------------- AWS ----------------
    ("AWS", "Basic", "What is the difference between a public and a private subnet?",
     ["A public subnet has a route to an Internet Gateway, and a private one does not",
      "Public subnets are faster", "Private subnets have no IP addresses", "Public subnets are free"], 0,
     "A private subnet can still reach the internet through a NAT gateway, but the internet cannot start connections to it."),
    ("AWS", "Intermediate", "Which statement about Security Groups and Network ACLs is true?",
     ["Security Groups are stateful and work per instance, and NACLs are stateless and work per subnet",
      "Both are stateful", "NACLs work per instance", "Security Groups are stateless"], 0,
     "A Security Group automatically allows the reply traffic. A NACL needs rules in both directions."),
    ("AWS", "Intermediate", "What is the best way to give an EC2 instance access to S3?",
     ["Save access keys on the instance", "Attach an IAM role to the instance",
      "Make the bucket public", "Email the keys to the team"], 1,
     "An IAM role gives temporary credentials that rotate automatically, so no long-term keys sit on the server."),
    ("AWS", "Basic", "What does an Auto Scaling Group do?",
     ["Adds or removes EC2 instances based on rules or demand", "Backs up volumes",
      "Encrypts traffic", "Creates IAM users"], 0,
     "It keeps the right number of healthy instances and replaces failed ones, often behind a load balancer."),
    ("AWS", "Intermediate", "Which service is a managed relational database with backups and failover?",
     ["Amazon RDS", "Amazon S3", "Amazon SQS", "AWS Lambda"], 0,
     "RDS manages patching, backups, and Multi-AZ failover, so you do not run the database server yourself."),

    # ---------------- Linux & Network ----------------
    ("Linux & Network", "Basic", "Which command shows the disk space used on each filesystem?",
     ["df -h", "ps aux", "chmod", "netstat"], 0,
     "df -h shows used and free space per filesystem. du shows the size of folders and files."),
    ("Linux & Network", "Intermediate", "A server is slow. Which command shows live CPU and memory use per process?",
     ["top or htop", "cat /etc/passwd", "ping", "tar"], 0,
     "top shows the load, CPU, memory, and the busiest processes. After that, check the disk and the network if needed."),
    ("Linux & Network", "Intermediate", "curl returns connection refused. What does it usually mean?",
     ["The host was reached, but nothing is listening on that port",
      "DNS failed", "A firewall silently dropped the packet", "The certificate expired"], 0,
     "Refused means the host answered with a reset, so no process listens on that port. A timeout usually points to a firewall or routing problem, and a DNS problem says it could not resolve the host."),
    ("Linux & Network", "Basic", "What does DNS do?",
     ["Encrypts traffic", "Turns names like example.com into IP addresses",
      "Assigns IP addresses to devices", "Balances load"], 1,
     "DNS lets you use names instead of IP addresses. In Kubernetes, CoreDNS lets pods call Services by name."),

    # ---------------- Monitoring ----------------
    ("Monitoring", "Intermediate", "What do metrics, logs, and traces show?",
     ["Metrics are numbers over time, logs are event records, and traces follow one request across services",
      "They are three names for the same data",
      "Metrics are errors only, logs are CPU only, and traces are disk only",
      "Traces are old logs"], 0,
     "Together they are the three pillars of observability. Prometheus is common for metrics, Loki or ELK for logs, and Jaeger or Tempo for traces."),
    ("Monitoring", "Intermediate", "What does Prometheus do?",
     ["Collects and stores metrics, and it can trigger alerts", "Builds Docker images",
      "Creates servers", "Stores Git repositories"], 0,
     "Prometheus scrapes metrics from your apps on a schedule. Grafana is usually used to draw dashboards from that data."),
]

QUESTIONS = [
    {"id": i + 1, "category": c, "level": lv, "question": q,
     "options": o, "answer": a, "explanation": e}
    for i, (c, lv, q, o, a, e) in enumerate(RAW)
]
CATEGORIES = list(dict.fromkeys(q["category"] for q in QUESTIONS))


@app.get("/api/health")
def health():
    return jsonify(status="ok")


@app.get("/api/info")
def info():
    return jsonify(
        pod=os.getenv("HOSTNAME", socket.gethostname()),
        version=os.getenv("APP_VERSION", "dev"),
    )


@app.get("/api/categories")
def categories():
    return jsonify([
        {"name": c, "count": sum(1 for q in QUESTIONS if q["category"] == c)}
        for c in CATEGORIES
    ])


@app.get("/api/questions")
def questions():
    category = request.args.get("category", default="", type=str)
    count = request.args.get("count", default=10, type=int)
    pool = [q for q in QUESTIONS if not category or q["category"] == category]
    count = max(1, min(count, len(pool))) if pool else 0
    picked = random.sample(pool, count) if pool else []
    hidden = ("answer", "explanation")
    return jsonify([{k: v for k, v in q.items() if k not in hidden} for q in picked])


@app.post("/api/answer")
def answer():
    data = request.get_json(silent=True) or {}
    q = next((q for q in QUESTIONS if q["id"] == data.get("id")), None)
    if q is None:
        return jsonify(error="unknown question"), 404
    right = q["options"][q["answer"]]
    return jsonify(
        correct=(data.get("choice") == right),
        answer=right,
        explanation=q["explanation"],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
