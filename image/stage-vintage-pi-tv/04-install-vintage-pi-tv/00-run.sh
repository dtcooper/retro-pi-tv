#!/bin/bash -e

if [ -z "${GITHUB_REF_TYPE}" ] || [ -z "${GITHUB_REF_NAME}" ] || [ -z "${GITHUB_REPOSITORY}" ]; then
    echo 'WARNING: At least one optional GITHUB_* environment variable not found. Will use sane defaults.'
fi

GITHUB_REF_TYPE="${GITHUB_REF_TYPE:-branch}"
GITHUB_REF_NAME="${GITHUB_REF_NAME:-main}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-dtcooper/vintage-pi-tv}"

install -vm 644 files/099_vintage_pi_tv_ir_keytable "${ROOTFS_DIR}/etc/sudoers.d/099_vintage_pi_tv_ir_keytable"

if [ ! -d files/vintage-pi-tv ]; then
    echo 'WARNING: Vintage Pi TV repository not found at files/vintage-pi-tv so cloning fresh copy.'
    git clone "https://github.com/${GITHUB_REPOSITORY}.git" files/vintage-pi-tv
fi
REPO_PATH="file:///$(pwd)/files/vintage-pi-tv"
REPO_DIR="$(pwd)/files/vintage-pi-tv"

install -vdm 755 "${ROOTFS_DIR}/opt/vintage-pi-tv"

pushd "${ROOTFS_DIR}/opt/vintage-pi-tv"

if [ "${GITHUB_REF_TYPE}" != 'copy' ]; then
    git clone --branch "${GITHUB_REF_NAME}" "${REPO_PATH}" .
fi

if [ "${GITHUB_REF_TYPE}" = 'tag' ]; then
    rm -rf .git
    echo "${GITHUB_REF_NAME}" > version.txt
elif [ "${GITHUB_REF_TYPE}" = 'copy' ]; then
    echo "WARNING: github ref name is set to 'copy', so copying repository niavely"
    cp -r "${REPO_DIR}/." .
else
    git remote set-url origin "https://github.com/${GITHUB_REPOSITORY}.git"
fi

install -vm 644 sample-config.toml "${ROOTFS_DIR}/boot/firmware/vintage-pi-tv-config.toml"
popd

on_chroot <<EOF
addgroup --system ir-keytable
adduser "${FIRST_USER_NAME}" ir-keytable

chown -R "${FIRST_USER_NAME}:${FIRST_USER_NAME}" /opt/vintage-pi-tv

su - "${FIRST_USER_NAME}" -c "/opt/poetry/bin/poetry config virtualenvs.in-project true"
if [ "${GITHUB_REF_TYPE}" = 'tag' ]; then
    su - "${FIRST_USER_NAME}" -c "cd /opt/vintage-pi-tv ; /opt/poetry/bin/poetry install --without=dev"
else
    su - "${FIRST_USER_NAME}" -c "cd /opt/vintage-pi-tv ; /opt/poetry/bin/poetry install"
fi
su - "${FIRST_USER_NAME}" -c "ln -vs /opt/vintage-pi-tv vintage-pi-tv"
su - "${FIRST_USER_NAME}" -c "ln -vs /opt/vintage-pi-tv/LICENSE LICENSE"
su - "${FIRST_USER_NAME}" -c "ln -vs /opt/vintage-pi-tv/README.md README.md"
EOF