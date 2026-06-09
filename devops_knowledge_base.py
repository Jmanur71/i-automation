from dataclasses import dataclass, field
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


SOURCE_GITHUB_DEVOPS_EXERCISES = "https://github.com/bregman-arie/devops-exercises"
SOURCE_GITHUB_ROHIT = "https://github.com/rohitg00/devops-interview-questions"
SOURCE_GITHUB_INTERVIEWS = "https://github.com/devops-interviews/devops-interview-questions"
SOURCE_GITHUB_ROOPENDRA = "https://github.com/roopendra/devops-interview-questions-answers"
SOURCE_ROADMAP = "https://roadmap.sh/devops"
SOURCE_DEVOPS_ROADMAP = "https://devopsroadmap.io/"


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "between", "by", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "the", "to", "what", "when",
    "where", "which", "why", "with", "does", "do", "did", "explain", "tell",
    "me", "about", "difference", "role", "devops",
}

LEVEL_ORDER = ("junior", "mid", "senior", "principal")


def _bullets(lines: Sequence[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)


def _variants(
    junior: Sequence[str],
    mid: Optional[Sequence[str]] = None,
    senior: Optional[Sequence[str]] = None,
    principal: Optional[Sequence[str]] = None,
) -> Dict[str, Tuple[str, ...]]:
    mid = mid or junior
    senior = senior or mid
    principal = principal or senior
    return {
        "junior": tuple(junior),
        "mid": tuple(mid),
        "senior": tuple(senior),
        "principal": tuple(principal),
    }


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("state full set", "stateful set")
    text = text.replace("state full", "stateful")
    text = re.sub(r"[^a-z0-9/+\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _tokenize(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9/+\-]+", _normalize(text))
        if token not in STOPWORDS and len(token) > 1
    ]


def _band_for_years(years: Optional[int]) -> str:
    if years is None:
        return "mid"
    if years <= 2:
        return "junior"
    if years <= 7:
        return "mid"
    if years <= 15:
        return "senior"
    return "principal"


def _is_acronym_like(text: str) -> bool:
    compact = _normalize(text).replace(" ", "")
    return bool(re.fullmatch(r"[a-z]{2,6}(?:/[a-z]{2,6})?", compact))


@dataclass(frozen=True)
class KnowledgeEntry:
    id: str
    category: str
    tool: str
    type: str
    difficulty_target: str
    question: str
    keywords: Tuple[str, ...]
    aliases: Tuple[str, ...]
    answer_variants: Dict[str, Tuple[str, ...]]
    source_reference: Tuple[str, ...] = field(default_factory=tuple)

    def answer_for_level(self, level: str) -> str:
        variant = self.answer_variants.get(level)
        if variant is None:
            variant = self.answer_variants.get("mid") or next(iter(self.answer_variants.values()))
        return _bullets(variant)

    def score(self, question: str) -> int:
        q = _normalize(question)
        score = 0

        if self.id == "DEVOPS-001" and not re.search(r"^(what is|what's|whats|define|explain|tell me about)\s+devops\b", q):
            return 0

        for alias in self.aliases:
            alias_norm = _normalize(alias)
            if alias_norm and alias_norm in q:
                score += 100

        for keyword in self.keywords:
            keyword_norm = _normalize(keyword)
            if keyword_norm and keyword_norm in q:
                score += 8 if " " in keyword_norm else 4

        tool_norm = _normalize(self.tool)
        category_norm = _normalize(self.category)
        if tool_norm and tool_norm in q:
            score += 12
        if category_norm and category_norm in q:
            score += 3

        question_tokens = set(_tokenize(question))
        entry_tokens = set(_tokenize(self.question)) | set(_tokenize(self.tool)) | set(_tokenize(self.category))
        score += len(question_tokens & entry_tokens) * 2

        if any(token in q for token in ["difference", "vs", "versus"]):
            if "difference" in _normalize(self.question) or "vs" in _normalize(self.question):
                score += 8

        return score


class DevOpsKnowledgeBase:
    def __init__(self, entries: Optional[Iterable[KnowledgeEntry]] = None):
        self.entries: Tuple[KnowledgeEntry, ...] = tuple(entries or DEFAULT_ENTRIES)

    def search(self, question: str, experience_years: Optional[int] = None) -> Optional[KnowledgeEntry]:
        best = None
        best_score = 0
        for entry in self.entries:
            score = entry.score(question)
            if score > best_score:
                best = entry
                best_score = score

        return best if best and best_score >= 10 else None

    def answer(self, question: str, experience_years: Optional[int] = None) -> Optional[str]:
        normalized = _normalize(question)
        band = _band_for_years(experience_years)

        entry = self.search(question, experience_years=experience_years)
        if entry:
            return entry.answer_for_level(band)

        # Safe fallback for acronym-like DevOps questions that we do not know.
        if _is_acronym_like(normalized) or re.search(r"\b(?:[a-z]\s+){1,8}[a-z]\b", normalized):
            term = question.strip().rstrip("?.")
            return _bullets(
                [
                    f"I don't know a standard DevOps meaning for {term}.",
                    "If you mean a specific tool or acronym, tell me the exact expansion.",
                    "For interviews, answer only with the most common industry meaning.",
                ]
            )

        return None


DEFAULT_ENTRIES: Tuple[KnowledgeEntry, ...] = (
    KnowledgeEntry(
        id="GIT-001",
        category="Version Control",
        tool="Git",
        type="Concept",
        difficulty_target="Junior to Mid",
        question="What is Git and why is it important?",
        keywords=("version control", "branch", "merge", "rebase", "commit"),
        aliases=("git", "what is git", "explain git"),
        answer_variants=_variants(
            junior=[
                "Git is a distributed version control system.",
                "It tracks code changes, supports branching, and makes collaboration safe.",
                "Example: use feature branches and merge them after review.",
            ],
            mid=[
                "Git is a distributed version control system for tracking source changes.",
                "It enables branching, rebasing, merging, and parallel team work.",
                "Example: use trunk-based or GitFlow depending on team maturity.",
            ],
            senior=[
                "Git is the source-of-truth layer for change management in software delivery.",
                "It supports traceability, code review, release governance, and rollback strategy.",
                "Example: enforce protected branches, signed commits, and CI checks.",
            ],
            principal=[
                "Git underpins change control, compliance, and collaboration across the engineering org.",
                "At scale, standardize branching, release governance, and auditability.",
                "Example: use trunk-based development with policy-as-code enforcement.",
            ],
        ),
        source_reference=(SOURCE_ROADMAP, SOURCE_GITHUB_DEVOPS_EXERCISES),
    ),
    KnowledgeEntry(
        id="DEVOPS-001",
        category="Core Principles",
        tool="DevOps",
        type="Concept",
        difficulty_target="Junior to Principal",
        question="What is DevOps?",
        keywords=("culture", "collaboration", "automation", "ci/cd", "sre", "shared responsibility"),
        aliases=("devops", "what is devops", "define devops", "explain devops"),
        answer_variants=_variants(
            junior=[
                "DevOps is a culture and practice that brings development and operations together.",
                "It improves collaboration, automation, and delivery speed.",
                "Example: developers and ops share ownership of build, deploy, and monitoring.",
            ],
            mid=[
                "DevOps combines culture, automation, and shared ownership to deliver software faster and safer.",
                "It typically includes CI/CD, infrastructure as code, and observability.",
                "Example: one team owns build, release, and incident feedback loops.",
            ],
            senior=[
                "DevOps is an operating model for shortening feedback loops and improving reliability.",
                "It aligns engineering, operations, and security around measurable delivery outcomes.",
                "Example: standardize pipelines, platform guardrails, and production telemetry.",
            ],
            principal=[
                "DevOps is an organizational capability that connects product delivery to business outcomes.",
                "At scale, it drives platform engineering, governance, and engineering effectiveness.",
                "Example: self-service platforms with policy, automation, and SLO-based operations.",
            ],
        ),
        source_reference=(SOURCE_ROADMAP, SOURCE_DEVOPS_ROADMAP),
    ),
    KnowledgeEntry(
        id="CICD-001",
        category="CI/CD Automation",
        tool="CI/CD",
        type="Definition",
        difficulty_target="Junior to Senior",
        question="What is CI/CD?",
        keywords=("continuous integration", "continuous delivery", "continuous deployment", "pipeline"),
        aliases=("ci/cd", "ci cd", "cicd", "continuous integration and continuous deployment"),
        answer_variants=_variants(
            junior=[
                "CI/CD means Continuous Integration and Continuous Delivery or Deployment.",
                "CI automates build and test; CD automates release readiness or production release.",
                "Example: every pull request triggers tests, then a pipeline deploys the release.",
            ],
            mid=[
                "CI/CD is the automation backbone of modern software delivery.",
                "CI validates code frequently; CD keeps releases ready or ships them automatically.",
                "Example: build, test, scan, package, then deploy through stages.",
            ],
            senior=[
                "CI/CD reduces lead time, human error, and release risk.",
                "CI focuses on merge confidence; CD enforces reliable promotion across environments.",
                "Example: gated production deploys with rollback, approval, and observability checks.",
            ],
            principal=[
                "CI/CD is a product and platform capability that standardizes software flow across teams.",
                "The goal is fast, safe, repeatable change with policy, security, and traceability built in.",
                "Example: one pipeline template used across many service teams.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="DEP-001",
        category="Release Management",
        tool="Deployment",
        type="Concept",
        difficulty_target="Junior to Senior",
        question="What is deployment?",
        keywords=("release", "production", "rollout", "application version", "environment"),
        aliases=("deployment", "what is deployment", "deploying software"),
        answer_variants=_variants(
            junior=[
                "Deployment is the process of releasing a new application version to an environment.",
                "It moves code from build/test into production or a target stage safely.",
                "Example: roll out version 2 of a web app with a zero-downtime strategy.",
            ],
            mid=[
                "Deployment is the controlled release of software into an environment.",
                "Good deployment practice includes validation, rollback planning, and observability.",
                "Example: blue-green or rolling deployment for a web service.",
            ],
            senior=[
                "Deployment is an operational release workflow, not just a code copy step.",
                "At scale, it must account for safety, rollback, progressive delivery, and governance.",
                "Example: canary deployment with metrics-based promotion.",
            ],
            principal=[
                "Deployment is a delivery capability that balances speed, safety, and business continuity.",
                "Standardize strategies, guardrails, telemetry, and change management across teams.",
                "Example: platform-managed deployment templates for all services.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="CICD-002",
        category="CI/CD Automation",
        tool="Continuous Delivery vs Continuous Deployment",
        type="Comparison",
        difficulty_target="Junior to Senior",
        question="What is the difference between continuous delivery and continuous deployment?",
        keywords=("delivery", "deployment", "manual approval", "production"),
        aliases=("difference between continuous deployment and continuous delivery", "continuous delivery vs continuous deployment", "cd vs cd"),
        answer_variants=_variants(
            junior=[
                "Continuous Delivery keeps software release-ready with a manual approval step.",
                "Continuous Deployment automatically releases every validated change to production.",
                "Example: delivery waits for approval; deployment ships automatically.",
            ],
            mid=[
                "Continuous Delivery stops at a release-ready state and waits for approval.",
                "Continuous Deployment removes the approval step and ships after validation.",
                "Example: the pipeline promotes to production only after all checks pass.",
            ],
            senior=[
                "Delivery optimizes control and governance; deployment optimizes speed and automation.",
                "Choose delivery when compliance or business risk requires a gate.",
                "Choose deployment when telemetry, tests, and rollback are strong enough to automate fully.",
            ],
            principal=[
                "The business trade-off is control versus velocity.",
                "Delivery fits regulated environments; deployment fits high-confidence product streams.",
                "The right model depends on risk tolerance, observability, and org maturity.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_INTERVIEWS, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="K8S-001",
        category="Orchestration",
        tool="Kubernetes",
        type="Concept",
        difficulty_target="Junior to Senior",
        question="What is Kubernetes?",
        keywords=("orchestration", "pods", "cluster", "service", "deployment"),
        aliases=("kubernetes", "k8s", "what is kubernetes"),
        answer_variants=_variants(
            junior=[
                "Kubernetes is a container orchestration platform.",
                "It automates deployment, scaling, and self-healing of containers.",
                "Example: run multiple replicas of an app across worker nodes.",
            ],
            mid=[
                "Kubernetes schedules containers across a cluster and keeps desired state.",
                "It handles service discovery, rolling updates, scaling, and self-healing.",
                "Example: deploy a web app with replicas, probes, and service routing.",
            ],
            senior=[
                "Kubernetes is the control plane for operating containerized workloads at scale.",
                "It standardizes rollout, resilience, traffic management, and policy enforcement.",
                "Example: use Deployments, Services, Ingress, HPA, and RBAC together.",
            ],
            principal=[
                "Kubernetes is a platform for consistent application operations across teams and environments.",
                "At enterprise scale, it becomes a foundation for platform engineering and developer self-service.",
                "Example: multi-tenant clusters with guardrails, policies, observability, and cost controls.",
            ],
        ),
        source_reference=(SOURCE_ROADMAP, SOURCE_GITHUB_DEVOPS_EXERCISES),
    ),
    KnowledgeEntry(
        id="K8S-002",
        category="Orchestration",
        tool="Kubernetes Deployment and ReplicaSet",
        type="Comparison",
        difficulty_target="Mid to Senior",
        question="What is the difference between deployment and replica set?",
        keywords=("deployment", "replicaset", "rollout", "rollback", "scaling"),
        aliases=("difference between deployment and replica set", "deployment vs replicaset", "deployment replica set"),
        answer_variants=_variants(
            junior=[
                "A Deployment manages rollout, rollback, and scaling of application versions.",
                "A ReplicaSet only ensures a desired number of pod replicas are running.",
                "Example: Deployment creates and manages ReplicaSets for you.",
            ],
            mid=[
                "ReplicaSet ensures pod count; Deployment manages application lifecycle changes.",
                "Deployment adds rollout strategy, revision history, and rollback support.",
                "Example: use Deployment for production updates and ReplicaSet underneath.",
            ],
            senior=[
                "ReplicaSet is the low-level controller; Deployment is the rollout abstraction.",
                "Use Deployment for declarative app delivery and operational safety.",
                "ReplicaSet should rarely be managed directly unless you need fine control.",
            ],
            principal=[
                "Deployment is the lifecycle contract exposed to teams; ReplicaSet is an implementation detail.",
                "Standardize on Deployment to reduce operational complexity and improve governance.",
                "Avoid direct ReplicaSet management unless you are building platform internals.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_INTERVIEWS, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="K8S-006",
        category="Orchestration",
        tool="Kubernetes Deployment vs StatefulSet",
        type="Comparison",
        difficulty_target="Mid to Senior",
        question="What is the difference between Kubernetes Deployment and StatefulSet?",
        keywords=("deployment", "statefulset", "stateful set", "ordered", "stable identity", "persistent storage"),
        aliases=(
            "difference between kubernetes deployment and statefulset",
            "deployment vs statefulset",
            "deployment and statefulset",
            "deployment stateful set",
            "state full set",
        ),
        answer_variants=_variants(
            junior=[
                "Deployment is for stateless apps; StatefulSet is for stateful apps.",
                "Deployment gives flexible pod replacement; StatefulSet keeps stable identities.",
                "Example: use Deployment for web apps and StatefulSet for databases.",
            ],
            mid=[
                "Deployment manages interchangeable pods; StatefulSet manages ordered, sticky pods.",
                "StatefulSet keeps stable network identity and persistent volume claims.",
                "Example: use StatefulSet for PostgreSQL or Kafka, Deployment for APIs.",
            ],
            senior=[
                "Deployment is optimized for horizontally scalable stateless workloads.",
                "StatefulSet is optimized for ordered rollout, stable identity, and storage retention.",
                "Example: choose StatefulSet when pod identity and volume association must persist.",
            ],
            principal=[
                "The architectural difference is whether workload identity is disposable or durable.",
                "Deployment fits stateless service tiers; StatefulSet fits systems with identity and storage coupling.",
                "Example: platform standards should route each workload class to the correct controller.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_INTERVIEWS, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="K8S-003",
        category="Orchestration",
        tool="Kubernetes",
        type="Comparison",
        difficulty_target="Mid to Senior",
        question="What is the difference between ReplicaSet and ReplicationController?",
        keywords=("replicaset", "replication controller", "selector", "pods"),
        aliases=("difference between replicaset and replicationcontroller", "replica set vs replication controller", "replicaset replicationcontroller"),
        answer_variants=_variants(
            junior=[
                "ReplicaSet is the newer Kubernetes API for keeping a set of pods running.",
                "ReplicationController is the older resource and is mostly replaced by ReplicaSet.",
                "Use ReplicaSet in modern Kubernetes workloads.",
            ],
            mid=[
                "ReplicaSet supports richer label selectors and is the modern controller.",
                "ReplicationController is legacy and remains mainly for backward compatibility.",
                "Example: a Deployment creates ReplicaSets, not ReplicationControllers.",
            ],
            senior=[
                "ReplicaSet is the current primitive for replica management in Kubernetes.",
                "ReplicationController is deprecated in practice and should be avoided in new designs.",
                "Use Deployments for rollout management and ReplicaSets as the backing controller.",
            ],
            principal=[
                "Treat ReplicationController as legacy API surface for historical compatibility only.",
                "Modern platform standards should mandate Deployment + ReplicaSet patterns.",
                "This simplifies governance, upgrades, and operational consistency.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_INTERVIEWS, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="K8S-005",
        category="Orchestration",
        tool="Kubernetes",
        type="Comparison",
        difficulty_target="Mid to Senior",
        question="What is the difference between replication and replication controller?",
        keywords=("replication", "replication controller", "pods", "kubernetes"),
        aliases=("difference between replication and replication controller", "replication vs replication controller"),
        answer_variants=_variants(
            junior=[
                "Replication is a generic term for copying data or keeping copies in sync.",
                "ReplicationController is a Kubernetes resource that keeps a desired number of pod replicas running.",
                "Example: use a ReplicationController to replace failed pods automatically.",
            ],
            mid=[
                "Replication is the general concept of duplicating data or workloads for availability.",
                "ReplicationController is the older Kubernetes object that maintains pod replica count.",
                "Example: focus on ReplicaSet today, since it replaces ReplicationController in modern clusters.",
            ],
            senior=[
                "Replication is a system design pattern; ReplicationController is a Kubernetes workload controller.",
                "The first is generic; the second is about maintaining pod availability in a cluster.",
                "Use Deployment/ReplicaSet for modern Kubernetes operations.",
            ],
            principal=[
                "Do not mix generic storage replication with Kubernetes replica management.",
                "ReplicationController is historical Kubernetes API surface; modern clusters standardize on Deployment and ReplicaSet.",
                "For interviews, distinguish data replication from workload reconciliation.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_INTERVIEWS, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="K8S-004",
        category="Orchestration",
        tool="Kubernetes",
        type="Concept",
        difficulty_target="Mid to Senior",
        question="What is node affinity in Kubernetes?",
        keywords=("node affinity", "scheduler", "node labels", "pod placement"),
        aliases=("node affinity", "what is node affinity"),
        answer_variants=_variants(
            junior=[
                "Node affinity is a Kubernetes scheduling rule for placing pods on matching nodes.",
                "It uses node labels and constraints to influence scheduling.",
                "Example: send GPU workloads only to GPU-labeled nodes.",
            ],
            mid=[
                "Node affinity helps the scheduler place pods on nodes that match label-based rules.",
                "It is useful for hardware, locality, compliance, or environment constraints.",
                "Example: run latency-sensitive pods on nodes in a specific zone.",
            ],
            senior=[
                "Node affinity expresses workload placement intent using label selectors.",
                "Use required rules for hard constraints and preferred rules for soft optimization.",
                "Example: isolate stateful workloads to dedicated nodes for reliability.",
            ],
            principal=[
                "Node affinity is a placement control mechanism for multi-tenant scheduling strategy.",
                "At scale, combine it with taints, tolerations, and topology spread constraints.",
                "This improves resilience, cost control, and policy enforcement.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="AWS-001",
        category="Cloud Providers",
        tool="AWS VPC",
        type="Concept",
        difficulty_target="Junior to Senior",
        question="What is a VPC in AWS?",
        keywords=("vpc", "subnet", "route table", "security group", "nacl"),
        aliases=("vpc", "aws vpc", "what is vpc"),
        answer_variants=_variants(
            junior=[
                "A VPC is a logically isolated virtual network in AWS.",
                "It lets you control IP ranges, subnets, routing, and security boundaries.",
                "Example: public subnets for web servers and private subnets for databases.",
            ],
            mid=[
                "A VPC gives you private network control inside AWS.",
                "Use it to design subnets, route tables, internet access, and segmentation.",
                "Example: place ALB in public subnets and databases in private subnets.",
            ],
            senior=[
                "A VPC is the network boundary for secure and scalable AWS architectures.",
                "It is where you model traffic flow, isolation, egress, and connectivity patterns.",
                "Example: connect a VPC to on-prem through VPN or Direct Connect.",
            ],
            principal=[
                "A VPC is a foundational network abstraction for enterprise cloud governance.",
                "Design it around blast radius, routing policy, shared services, and observability.",
                "Example: hub-and-spoke VPC design across multiple accounts.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="AWS-002",
        category="Cloud Providers",
        tool="AWS IAM",
        type="Concept",
        difficulty_target="Mid to Senior",
        question="What is least privilege in AWS IAM?",
        keywords=("least privilege", "iam", "policy", "permissions"),
        aliases=("least privilege", "aws iam least privilege", "iam least privilege"),
        answer_variants=_variants(
            junior=[
                "Least privilege means giving only the permissions a user or service needs.",
                "It reduces the impact of mistakes or compromised credentials.",
                "Example: allow read-only access to an S3 bucket instead of full admin access.",
            ],
            mid=[
                "Least privilege is the practice of minimizing access to the exact actions required.",
                "In AWS IAM, use scoped policies, roles, and permission boundaries.",
                "Example: separate deployment roles from read-only observability roles.",
            ],
            senior=[
                "Least privilege is a core security control for limiting blast radius.",
                "Enforce it with policy review, role design, and continuous access analysis.",
                "Example: deny wildcard permissions and require temporary role assumption.",
            ],
            principal=[
                "Least privilege is an enterprise governance principle, not just an IAM tactic.",
                "It should be encoded into identity architecture, automation, and audit workflows.",
                "Example: policy-as-code and delegated access with periodic access attestation.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_DEVOPS_ROADMAP),
    ),
    KnowledgeEntry(
        id="DOCKER-001",
        category="Containerization",
        tool="Docker",
        type="Concept",
        difficulty_target="Junior to Senior",
        question="What is Docker?",
        keywords=("container", "image", "dockerfile", "runtime", "volume"),
        aliases=("docker", "what is docker"),
        answer_variants=_variants(
            junior=[
                "Docker is a container platform for packaging and running applications.",
                "It makes environments consistent from development to production.",
                "Example: build one image and run it on any Docker host.",
            ],
            mid=[
                "Docker packages an app and its dependencies into portable images.",
                "It simplifies delivery, isolation, and local development.",
                "Example: use multi-stage builds to reduce image size.",
            ],
            senior=[
                "Docker standardizes application runtime packaging and distribution.",
                "In production, optimize for image immutability, security, and fast startup.",
                "Example: run rootless containers and scan images in CI.",
            ],
            principal=[
                "Docker is part of the software supply chain and operational platform model.",
                "At scale, combine image governance, SBOMs, and policy enforcement.",
                "Example: signed images promoted through controlled registries.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="TF-001",
        category="Infrastructure as Code",
        tool="Terraform",
        type="Concept",
        difficulty_target="Mid to Principal",
        question="What is Terraform?",
        keywords=("iac", "state", "plan", "apply", "module", "drift"),
        aliases=("terraform", "what is terraform", "openTofu"),
        answer_variants=_variants(
            junior=[
                "Terraform is Infrastructure as Code for defining cloud resources declaratively.",
                "It creates, updates, and deletes infrastructure with repeatable plans.",
                "Example: define a VPC, subnets, and security groups in code.",
            ],
            mid=[
                "Terraform manages infrastructure with declarative configuration and state.",
                "It helps teams detect drift, reuse modules, and automate provisioning.",
                "Example: use remote state and locking for collaboration.",
            ],
            senior=[
                "Terraform is a stateful infrastructure workflow for repeatable, auditable change.",
                "Use modules, environments, locking, and review gates to scale safely.",
                "Example: separate platform modules from application stacks.",
            ],
            principal=[
                "Terraform becomes part of platform governance, not just provisioning.",
                "At enterprise scale, standardize module design, state strategy, and policy controls.",
                "Example: enforce guardrails with policy-as-code and drift monitoring.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_ROADMAP),
    ),
    KnowledgeEntry(
        id="ANS-001",
        category="Configuration Management",
        tool="Ansible",
        type="Concept",
        difficulty_target="Junior to Senior",
        question="What is Ansible?",
        keywords=("playbook", "role", "idempotent", "vault", "ssh"),
        aliases=("ansible", "what is ansible"),
        answer_variants=_variants(
            junior=[
                "Ansible is a configuration management and automation tool.",
                "It uses playbooks to configure systems without installing an agent on targets.",
                "Example: install packages, copy config files, and restart services.",
            ],
            mid=[
                "Ansible automates server configuration using declarative playbooks and roles.",
                "It is idempotent, so re-running a playbook should not break the system.",
                "Example: use Ansible Vault for secrets and dynamic inventories for scale.",
            ],
            senior=[
                "Ansible is a push-based automation layer for repeatable operational change.",
                "Use it for provisioning, patching, compliance, and orchestration tasks.",
                "Example: standardize hardening across fleets with reusable roles.",
            ],
            principal=[
                "Ansible is an operations automation platform that can encode operational policy.",
                "At scale, integrate it with CI, inventory sources, and security workflows.",
                "Example: automate cluster upgrades and compliance checks in one workflow.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_GITHUB_ROHIT),
    ),
    KnowledgeEntry(
        id="MON-001",
        category="Monitoring & Logging",
        tool="Prometheus and Grafana",
        type="Concept",
        difficulty_target="Mid to Principal",
        question="What is Prometheus and Grafana?",
        keywords=("metrics", "dashboard", "alert", "monitoring", "observability"),
        aliases=("prometheus grafana", "prometheus and grafana", "what is prometheus", "what is grafana"),
        answer_variants=_variants(
            junior=[
                "Prometheus collects and stores metrics; Grafana visualizes them.",
                "Together they help you monitor system health and performance.",
                "Example: alert when CPU, latency, or error rate exceeds a threshold.",
            ],
            mid=[
                "Prometheus is a metrics scraper and time-series database.",
                "Grafana builds dashboards and visualizes operational data.",
                "Example: alert on SLA breaches using Prometheus Alertmanager.",
            ],
            senior=[
                "Prometheus and Grafana form the metrics layer of observability.",
                "Use them to detect symptoms, trend behavior, and guide incident response.",
                "Example: SLO-based alerts with dashboards for service ownership.",
            ],
            principal=[
                "Metrics are the leading indicator for platform and product reliability.",
                "At scale, standardize metric naming, alert hygiene, and dashboard ownership.",
                "Example: SLO/error-budget dashboards across business-critical services.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_DEVOPS_ROADMAP),
    ),
    KnowledgeEntry(
        id="SEC-001",
        category="Security (DevSecOps)",
        tool="Trivy and Vault",
        type="Concept",
        difficulty_target="Mid to Principal",
        question="What is DevSecOps?",
        keywords=("sast", "dast", "scan", "secrets", "vulnerability"),
        aliases=("devsecops", "what is devsecops"),
        answer_variants=_variants(
            junior=[
                "DevSecOps means adding security into the DevOps pipeline.",
                "It shifts security checks left into build, test, and deployment stages.",
                "Example: scan containers with Trivy and store secrets in Vault.",
            ],
            mid=[
                "DevSecOps integrates security scanning, policy checks, and secret handling into delivery.",
                "The goal is to catch vulnerabilities before production.",
                "Example: run SAST, dependency scanning, container scanning, and IaC checks in CI.",
            ],
            senior=[
                "DevSecOps is security-as-code across the delivery lifecycle.",
                "It blends automation, policy, identity, and auditability into pipelines.",
                "Example: central secret management, signed artifacts, and enforcement gates.",
            ],
            principal=[
                "DevSecOps is a cultural and platform operating model for secure software supply chains.",
                "It requires governance, developer enablement, and measurable security outcomes.",
                "Example: standard controls embedded into reusable pipeline templates.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_GITHUB_INTERVIEWS),
    ),
    KnowledgeEntry(
        id="LINUX-001",
        category="OS & Scripting",
        tool="Linux",
        type="Concept",
        difficulty_target="Junior to Mid",
        question="What Linux commands do you use for troubleshooting?",
        keywords=("top", "htop", "df", "grep", "awk", "sed", "netstat", "ss", "journalctl"),
        aliases=("linux troubleshooting", "linux commands", "troubleshooting linux"),
        answer_variants=_variants(
            junior=[
                "Use top or htop for CPU and memory, df for disk, and journalctl for logs.",
                "Use grep, awk, and sed to inspect and filter text quickly.",
                "Example: check disk space, running processes, and service logs first.",
            ],
            mid=[
                "For Linux troubleshooting, check CPU, memory, disk, logs, and network state.",
                "Use top, free, df, journalctl, ss, grep, awk, and sed.",
                "Example: identify high load, full disk, and failing services in minutes.",
            ],
            senior=[
                "Troubleshooting is about correlating symptoms across process, disk, network, and logs.",
                "Use Linux tools to narrow down bottlenecks before changing code or infra.",
                "Example: pair journalctl with ss, iostat, and df to isolate the root cause.",
            ],
            principal=[
                "Linux diagnostics are part of operational discipline and incident response.",
                "At scale, standard runbooks and telemetry reduce mean time to recovery.",
                "Example: automate first-pass checks with scripts and dashboards.",
            ],
        ),
        source_reference=(SOURCE_GITHUB_DEVOPS_EXERCISES, SOURCE_GITHUB_ROHIT),
    ),
)


def _fallback_ambiguous_answer(term: str) -> str:
    return _bullets(
        [
            f"I don't know a standard DevOps meaning for {term}.",
            "If you mean a specific tool or acronym, tell me the exact expansion.",
            "For interviews, answer only with the most common industry meaning.",
        ]
    )


class KnowledgeBaseFacade:
    def __init__(self, entries: Iterable[KnowledgeEntry] = DEFAULT_ENTRIES):
        self.kb = DevOpsKnowledgeBase(entries)

    def answer(self, question: str, experience_years: Optional[int] = None) -> Optional[str]:
        answer = self.kb.answer(question, experience_years=experience_years)
        if answer:
            return answer

        # Let obvious short acronym-like questions fail safely instead of hallucinating.
        q = _normalize(question)
        term = _extract_term(question)
        if _is_acronym_like(term) or re.search(r"\b(?:[a-z]\s+){1,8}[a-z]\b", q):
            return _fallback_ambiguous_answer(term)

        return None

    def search(self, question: str, experience_years: Optional[int] = None) -> Optional[KnowledgeEntry]:
        return self.kb.search(question, experience_years=experience_years)


def _extract_term(question: str) -> str:
    q = _normalize(question)
    q = re.sub(r"^(what is|what's|whats|define|explain|tell me about|describe)\s+", "", q)
    q = re.sub(r"^(the difference between|difference between|difference of|difference in)\s+", "", q)
    q = re.sub(r"\b(in|for|on|of|at|to)\s+devops$", "", q).strip()
    return q.strip(" ?.!")


_DEFAULT_FACADE = KnowledgeBaseFacade()


def answer(question: str, experience_years: Optional[int] = None) -> Optional[str]:
    return _DEFAULT_FACADE.answer(question, experience_years=experience_years)
