#!/bin/sh

if [ -z "$RUN_RETRO_PI_TV_BUILD_SCRIPT" ]; then
    cat <<EOF

WARNING: This script should ONLY run inside a clean systemd-nspawn Raspberry Pi
OS container, inside the dtcooper/rpi-image-modifier GitHub action.

If you don't know what this means, you probably don't want to run this script.

If you're *SURE* you know what you're doing, run this script via the following,

    \$ RUN_RETRO_PI_TV_BUILD_SCRIPT=1 ${0}

EOF
    exit 1
fi


FILES_DIR=/mounted-github-repo/image/files

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    git \
    libmpv2 \
    mpv \
    udiskie

cp -v "${FILES_DIR}/99-udisks2.rules" /etc/udev/rules.d/
cp -v "${FILES_DIR}/udiskie.service" /etc/systemd/system/

mkdir -p /usr/local/lib/retro-pi-tv-sys-mods
cp -v "${FILES_DIR}/resize_partitions.sh" /usr/local/lib/retro-pi-tv-sys-mods/
sed -i 's|init=/usr/lib/raspberrypi-sys-mods/firstboot|init=/usr/local/lib/retro-pi-tv-sys-mods/resize_partitions.sh|' /boot/firmware/cmdline.txt
systemctl enable udiskie.service
sed -i 's|/boot/firmware.*defaults|\0,uid=1000,gid=1000|' /etc/fstab

curl -L https://install.python-poetry.org | POETRY_HOME=/opt/poetry python3
cp -v "${FILES_DIR}/poetry.sh" /etc/profile.d/
su - pi -c "git clone --branch '${GITHUB_REF_NAME}' file:///mounted-github-repo/ retro-pi-tv"
su - pi -c "cd retro-pi-tv ; git remote set-url origin 'https://github.com/${GIHUBT_REPOSITORY}.git'"
su - pi -c "cd retro-pi-tv ; poetry config virtualenvs.in-project true"
su - pi -c "cd retro-pi-tv ; poetry install --without=dev"