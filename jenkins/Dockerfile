FROM jenkins/jenkins:2.580.1-lts-jdk21

# docker CLI only; the daemon is the host's, reached through the mounted socket
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

# checkov:skip=CKV_DOCKER_8: local lab tool, never shipped; root is needed to use the docker socket
USER root

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD curl -fs http://localhost:8080/login || exit 1
