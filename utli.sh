#!/usr/bin/bash -f

pip install -r ./requirements.txt

APT_GET_CMD=$(which apt-get)
PACMAN_CMD=$(which pacman)

DEB_PACKAGE="tesseract-ocr libtesseract-dev"
ARCH_PACKAGE="tesseract tesseract-data-eng"
PACKAGE="tesseract"

if [[ ! -z $APT_GET_CMD ]]; then
    apt install $DEB_PACKAGE
elif [[ ! -z $PACMAN_CMD ]]; then
    pacman -Syyu $ARCH_PACKAGE
else
    echo "Error can't install package $PACKAGE"
    exit 1;
fi
