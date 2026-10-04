// Same checks as .gitlab-ci.yml, run by Jenkins.
// Not ported on purpose: registry push/release and the kind deploy (GitLab handles those).
pipeline {
    agent none

    options {
        // keep the log of the last 10 builds only
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        // local image name, never pushed
        IMAGE = "task-tracker:${env.GIT_COMMIT?.take(8) ?: 'local'}"
        TRIVY_NO_PROGRESS = 'true'
        TRIVY_TIMEOUT = '15m'
    }

    stages {
        stage('test') {
            agent { docker { image 'python:3.12-slim' } }
            steps {
                sh 'pip install --no-cache-dir -r requirements-dev.txt'
                sh 'pytest --cov=app --cov-report=term --cov-fail-under=90'
            }
        }

        stage('scan') {
            stages {
                stage('gitleaks') {
                    agent { docker { image 'zricethezav/gitleaks:v8.21.2'; args '--entrypoint=' } }
                    steps {
                        sh 'gitleaks detect --source . --redact --verbose'
                    }
                }
                stage('semgrep') {
                    agent { docker { image 'semgrep/semgrep:1.179.0'; args '--entrypoint=' } }
                    steps {
                        sh 'semgrep scan --config p/python --config p/flask --error --metrics=off .'
                    }
                }
                stage('trivy-deps') {
                    // named volume keeps the vulnerability DB between builds
                    agent { docker { image 'aquasec/trivy:0.75.0'; args '--entrypoint= -v trivy-cache:/root/.cache/trivy' } }
                    steps {
                        sh 'trivy fs --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 requirements.txt'
                    }
                }
                stage('hadolint') {
                    agent { docker { image 'hadolint/hadolint:v2.15.1-alpine'; args '--entrypoint=' } }
                    steps {
                        sh 'hadolint --failure-threshold warning Dockerfile'
                    }
                }
                stage('checkov') {
                    agent { docker { image 'bridgecrew/checkov:3.3.22'; args '--entrypoint=' } }
                    steps {
                        sh 'checkov -d . --framework dockerfile --framework kubernetes --framework terraform --compact'
                    }
                }
            }
        }

        stage('build') {
            agent any
            steps {
                // uses the host Docker through the mounted socket
                sh 'docker build -t "$IMAGE" .'
            }
        }

        stage('image-scan') {
            agent { docker { image 'aquasec/trivy:0.75.0'; args '--entrypoint= -v trivy-cache:/root/.cache/trivy -v /var/run/docker.sock:/var/run/docker.sock' } }
            steps {
                // report first, gate second (same as GitLab)
                sh 'trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 0 "$IMAGE"'
                sh 'trivy image --severity CRITICAL --ignore-unfixed --exit-code 1 "$IMAGE"'
                sh 'trivy image --format cyclonedx --output sbom.cdx.json "$IMAGE"'
                archiveArtifacts artifacts: 'sbom.cdx.json', fingerprint: true
            }
        }
    }
}
