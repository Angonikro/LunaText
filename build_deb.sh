#!/bin/sh
set -eu
cd "$(dirname "$0")"

VERSION="$(dpkg-deb -f debian/DEBIAN/control Version)"
PACKAGE="$(dpkg-deb -f debian/DEBIAN/control Package)"
ARCH="$(dpkg-deb -f debian/DEBIAN/control Architecture)"
OUTPUT="${PACKAGE}_${VERSION}_${ARCH}.deb"

dpkg-deb --build --root-owner-group debian "$OUTPUT"
printf '\nErstellt: %s\n' "$OUTPUT"
