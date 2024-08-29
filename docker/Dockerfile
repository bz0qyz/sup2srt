FROM eclipse-temurin:17


ENV WORK_DIR=/home/sup2srt
ENV APP_USER=sup2srt
ENV APP_UID=1000
ENV DEBIAN_FRONTEND noninteractive

COPY ../requirements.txt /tmp/requirements.txt

RUN set -e; 
  echo Update debian linux packages; \
  apt update > /dev/null && \
  apt upgrade -y > /dev/null; \
  apt install -y \
    tesseract \
    tzdata \
    findutils \
    python3 \
    curl; \
  python -m pip install -f /tmp/requirements.txt


RUN set -e \
  echo "Creating user: ${APP_USER} (${APP_UID})"; \
  useradd -m -d ${WORK_DIR} -u ${APP_UID} ${APP_USER} \
  && mkdir -p "${WORK_DIR}/bin" \
  && chown -R ${APP_USER}:${APP_USER} "${WORK_DIR}"
  && echo "Installing BDSup2Sub" \
  && curl -o "${WORK_DIR}/bin/BDSup2Sub.jar" "https://raw.githubusercontent.com/wiki/mjuhasz/BDSup2Sub/downloads/BDSup2Sub.jar"

COPY --chown=${APP_USER}:${APP_USER} ../src "${WORK_DIR}/bin/sub2srt


WORKDIR ${WORK_DIR}
USER: ${APP_USER}

CMD ["${WORK_DIR}/bin/sup2srt", "-h"]
