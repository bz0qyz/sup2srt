# FROM python:3.12-bookworm AS builder
FROM eclipse-temurin:17 AS builder
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.12.5
ENV LD_LIBRARY_PATH='/usr/lib:/usr/local/lib:/lib/x86_64-linux-gnu/'

ADD "./" "/tmp/sup2srt"

RUN set -e; \
  echo "Update debian linux packages"; \
  apt update > /dev/null && \
  apt upgrade -y > /dev/null; \
  apt install -y \
    build-essential \
    zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libreadline-dev \
    libffi-dev libsqlite3-dev wget libbz2-dev \
    libgl1 curl \
    tesseract-ocr tesseract-ocr-eng;

RUN set -e; \
  echo "Installing Python ${PYTHON_VERSION}" \
  && cd /usr/local/src \
  && curl -L -o python.tar.gz "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz" \
  && tar -zxf python.tar.gz \
  && cd "Python-${PYTHON_VERSION}" \
  && ./configure --enable-optimizations --enable-shared \
  && make -j $(nproc| tr -d '\n') \
  && make altinstall \
  && python3 --version;

RUN set -e; \
  echo "Installing python modules" \
  && python3.12 -m pip install --no-cache-dir --upgrade pip \
  && python3.12 -m pip install -r "/tmp/sup2srt/src/requirements.txt" \
  && python3.12 -m pip install --upgrade setuptools

RUN set -e; \
  # Build sup2srt python application
  STDC=$(find /lib/x86_64-linux-gnu/ -name 'libstdc++.so.*' -type l | head -1); \
  TSLIB=$(find /lib/x86_64-linux-gnu/ -name 'libtesseract.so.*' -type l | head -1); \
  cd /tmp/sup2srt \
  && pyinstaller --clean --onefile --name sup2srt \
    --paths /usr/lib/x86_64-linux-gnu \
    --add-binary "${STDC}:." \
    --add-binary "${TSLIB}:." \
    src/__main__.py;

FROM eclipse-temurin:17 AS app

ENV HOME_DIR=/home/sup2srt
ENV APP_USER=sup2srt
ENV APP_UID=1001

ENV OUT_VOLUME="${HOME_DIR}/output"
ENV BDSUP2SUB="${HOME_DIR}/bin/BDSup2Sub.jar"
ENV SUP2SRT="${HOME_DIR}/bin/sup2srt"
ENV DEBIAN_FRONTEND=noninteractive
ENV LD_LIBRARY_PATH='/usr/lib:/usr/local/lib:/lib/x86_64-linux-gnu/'
ENV RUN_IN_DOCKER=1
SHELL ["/bin/bash", "-c"]

RUN set -e; \
  echo "Update debian linux packages"; \
  apt update > /dev/null && \
  apt upgrade -y > /dev/null; \
  echo "Installing required run packages"; \
  apt install -y \
    tesseract-ocr tesseract-ocr-eng \
    libgl1 \
    tzdata \
    findutils \
    lib32stdc++6 \
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

RUN set -e; \
  echo "Loading latest tesseract training files"; \
  FILES=('eng.traineddata' 'osd.traineddata' 'pdf.ttf'); \
  TPATH=$(dirname "$(find "/usr/share/tesseract-ocr" -name "${FILES[0]}" | head -n 1)"); \
  for file in ${FILES[@]}; do \
    echo "Installing: ${TPATH}/${file}"; \
    [ -e "${TPATH}/${file}" ] && mv "${TPATH}/${file}" "${TPATH}/${file}.dist"; \
    curl -sL "https://github.com/tesseract-ocr/tessdata/raw/main/${file}" -o "${TPATH}/${file}"; \
  done;

COPY --from=builder --chown=${APP_USER}:${APP_USER} "/tmp/sup2srt/dist/sup2srt" "${SUP2SRT}"

WORKDIR ${HOME_DIR}
USER root
VOLUME ${OUT_VOLUME}

CMD ["${SUP2SRT}", "-h"]
