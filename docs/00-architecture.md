# Architecture

One small app (Task Tracker) goes through a pipeline that tests it, scans it, packages it
and deploys it. The same code can also be built by a second CI tool (Jenkins) and run on a
temporary AWS server. The diagrams render directly on GitLab.

## 1. The pipeline: from commit to running app

```mermaid
flowchart LR
    dev([Developer]) -->|git push| repo[(GitLab repo)]
    repo --> test

    subgraph ci [GitLab CI pipeline]
        direction LR
        test["test<br/>pytest, 90% coverage"] --> scan
        subgraph scan [scan: code and config]
            direction TB
            gl[Gitleaks<br/>secrets]
            sg[Semgrep<br/>code flaws]
            td[Trivy<br/>dependencies]
            hl[Hadolint<br/>Dockerfile]
            ck[Checkov<br/>Dockerfile, k8s, Terraform]
        end
        scan --> build["build<br/>Docker image"]
        build --> imgscan
        subgraph imgscan [image-scan]
            direction TB
            ti[Trivy image<br/>block CRITICAL]
            sbom[SBOM<br/>CycloneDX]
        end
        imgscan --> release["release<br/>tag latest, main only"]
        release --> deploy["deploy<br/>main only"]
    end

    build -->|push by SHA| reg[(GitLab Container Registry)]
    reg -.->|pull by digest| deploy
    deploy -->|kubectl apply<br/>limited ServiceAccount| kind[[kind cluster<br/>task-tracker namespace]]
```

Any red job stops the stages after it, so a vulnerable or leaky change never reaches the
registry's `latest` tag or the cluster. Each scanner was proven to fail on a throwaway
branch (docs 04, 05 and 07).

## 2. Where everything runs

```mermaid
flowchart TB
    subgraph cloud [GitLab.com]
        repo[(Repository)]
        shared[Shared runners<br/>test, scan, build jobs]
        reg[(Container Registry)]
    end

    subgraph pc [Developer PC, Windows + Docker Desktop]
        runner["Self-hosted runner<br/>tag local-kind"]
        subgraph kindbox [kind cluster]
            pod["Pod task-tracker<br/>non-root, read-only FS<br/>NetworkPolicy: no egress"]
            pvc[(PVC: SQLite file)]
        end
        jenkins["Jenkins container<br/>same checks, no deploy"]
    end

    subgraph aws [AWS Learner Lab, temporary]
        ec2["EC2 t3.micro<br/>Docker, same hardening"]
        sgrp{{"Security group<br/>8000 from one IP"}}
    end

    repo --> shared
    shared -->|push image| reg
    repo --> runner
    runner -->|deploy| pod
    pod --- pvc
    repo -->|fetch on build, read-only token| jenkins
    tf["Terraform<br/>run from the PC"] -->|create and destroy| ec2
    sgrp --- ec2
    reg -.->|pull by digest, read-only token| pod
    reg -.->|pull by digest, read-only token| ec2
    me([Browser]) -->|localhost:8080| pod
    me -->|my IP only, port 8000| sgrp
```

Why it is split this way:

| Part | Where | Why there |
|---|---|---|
| Test, scan, build | GitLab shared runners | Free, clean machine for every job |
| Deploy to kind | Self-hosted runner on the PC | GitLab's cloud cannot reach a cluster inside the PC |
| Jenkins | Container on the PC | Shows the same checks in a second CI tool. Never started together with kind, to save RAM |
| AWS server | Terraform from the PC | Lab credentials are temporary, so no pipeline holds them. Destroyed the same day |

## 3. Security controls by layer

| Layer | Control | Tool or setting | Doc |
|---|---|---|---|
| Code | Secret detection | Gitleaks | 04 |
| Code | Static analysis | Semgrep | 04 |
| Dependencies | Known CVEs, SBOM | Trivy, CycloneDX | 04 |
| Container | Lint, scan, non-root, healthcheck | Hadolint, Trivy image, Dockerfile | 04 |
| Kubernetes | PSA restricted, read-only FS, dropped capabilities, NetworkPolicy, image pinned by digest | Manifests, Checkov | 05, 06 |
| Deploy access | Least privilege | `ci-deployer` ServiceAccount limited to one namespace, no delete | 06 |
| Infrastructure | Scanned before creation | Checkov on Terraform, `/32` validation, IMDSv2, encrypted disk | 07 |
| Cloud | One-IP firewall, no SSH, read-only registry token | Security group, boot script | 09 |
