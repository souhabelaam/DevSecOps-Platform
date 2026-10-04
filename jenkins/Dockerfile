FROM jenkins/jenkins:2.580.1-lts-jdk21

# docker CLI only; the daemon is the host's, reached through the mounted socket
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker

# running as root so the container can use the docker socket (local lab only)
USER root

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
