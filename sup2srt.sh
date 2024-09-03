#!/usr/bin/env bash

# Process passed arguments
CMD=()
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -i|--in)
      INPUT_FILE="${2}"
      shift # past argument
      shift # past value
      ;;
    *)    # unknown option
      CMD+=("$1") # save it in an array for later
      shift # past argument
      ;;
  esac
done

CNT_OTPUT_DIR="/home/sup2srt/output"

if [[ -d "${INPUT_FILE}" ]]; then
  MOUNT_DIR="${INPUT_FILE}"
  INPUT_FILE="${CNT_OTPUT_DIR}"
else
  MOUNT_DIR=$(dirname "${INPUT_FILE}")
  INPUT_FILE="${CNT_OTPUT_DIR}/$(basename "${INPUT_FILE}")"
fi

UID=$(id -u)
GID=$(id -u)
echo "Converting subtitles from: \"${INPUT_FILE}\""
echo "Mounting \"${MOUNT_DIR}\" to the docker image output directory."

docker run --name sup2srt --rm -it \
  -v "${MOUNT_DIR}":"/home/sup2srt/output":rw  \
  sup2srt:latest /home/sup2srt/bin/sup2srt --uid ${UID} --gid ${GID} --in "${INPUT_FILE}" --out "${CNT_OTPUT_DIR}" ${CMD[@]}
