#!/bin/bash
set -eo pipefail

if [ -e "./test_data/TPCH.db" ]; then
    echo "FOUND"
    exit 0
else
    wget https://github.com/lovasoa/TPCH-sqlite/releases/download/v1.0/TPC-H.db -O "./test_data/TPCH.db"
fi  # <-- SE CIERRA EL IF AQUÍ
