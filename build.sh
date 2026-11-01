#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build vendor
python3 - <<'PYDATA'
import tarfile
with tarfile.open('third_party/tzdata-source.tar.gz') as archive:
    archive.extractall('vendor', filter='data')
PYDATA
cd third_party/swisseph
cc -O2 -fPIC -shared -o ../../build/libswe.so swedate.c swehouse.c swejpl.c swemmoon.c swemplan.c sweph.c swephlib.c swecl.c swehel.c -lm -ldl
cc -O2 -o ../../build/swetest swetest.c -L../../build -Wl,-rpath,'$ORIGIN' -lswe -lm -ldl
