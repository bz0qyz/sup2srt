FROM python:3.12-bookworm AS builder
ENV DEBIAN_FRONTEND noninteractive

ADD "./" "/tmp/sup2srt"

RUN set -e; \
  echo "Update debian linux packages"; \
  apt update > /dev/null && \
  apt upgrade -y > /dev/null; \
  apt install -y \
    build-essential \
    libgl1 \
    tesseract-ocr; \
  echo "Installing python modules"; \
  python3 -m pip install --no-cache-dir --upgrade pip \
  && python3 -m pip install -r "/tmp/sup2srt/src/requirements.txt" \
  && python3 -m pip install --upgrade setuptools

RUN set -e; \
  # Build sup2srt python application
  cd /tmp/sup2srt \
  && pyinstaller --clean -F -n sup2srt src/__main__.py;

FROM eclipse-temurin:17 AS app

ENV HOME_DIR /home/sup2srt
ENV APP_USER sup2srt
ENV APP_UID 1001

ENV OUT_VOLUME "${HOME_DIR}/output"
ENV BDSUP2SUB "${HOME_DIR}/bin/BDSup2Sub.jar"
ENV SUP2SRT "${HOME_DIR}/bin/sup2srt"
ENV DEBIAN_FRONTEND noninteractive

RUN set -e; \
  echo "Update debian linux packages"; \
  apt update > /dev/null && \
  apt upgrade -y > /dev/null; \
  apt install -y \
    tesseract-ocr \
    libgl1 \
    tzdata \
    findutils \
    mkvtoolnix \
    curl;

RUN set -e; \
  echo "Creating user: ${APP_USER} (${APP_UID})" \
  && useradd -m -d ${HOME_DIR} -u ${APP_UID} ${APP_USER} \
  && echo "Creating application folders" \
  && mkdir -p "${HOME_DIR}/bin" \
  && mkdir -p "{OUT_VOLUME}" \
  && echo "Installing BDSup2Sub" \
  && curl -Lo "${BDSUP2SUB}" "https://raw.githubusercontent.com/wiki/mjuhasz/BDSup2Sub/downloads/BDSup2Sub.jar" \
  && ls -l "${HOME_DIR}/bin"; \
  [ -e "${BDSUP2SUB}" ] && java -jar "${BDSUP2SUB}" --version; \
  chown -R ${APP_USER}:${APP_USER} "${HOME_DIR}";

COPY --from=builder --chown=${APP_USER}:${APP_USER} "/tmp/sup2srt/dist/sup2srt" "${SUP2SRT}"

WORKDIR ${HOME_DIR}
USER ${APP_USER}
VOLUME ${OUT_VOLUME}

CMD ["${SUP2SRT}", "-h"]
