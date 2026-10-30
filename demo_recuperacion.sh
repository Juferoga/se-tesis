#!/usr/bin/env bash
# Demostración de punta a punta: el emisor y el receptor corren como procesos separados.
# Uso: ./demo_recuperacion.sh            (con pausas, para presentar)
#      ./demo_recuperacion.sh --seguido  (sin pausas)
cd "$(dirname "$0")"
export PYTHONWARNINGS=ignore TRANSFORMERS_VERBOSITY=error
[ "$1" = "--seguido" ] && export PAUSA=0
.venv/bin/python -I scripts/demo_recuperacion.py emisor || exit 1
echo
.venv/bin/python -I scripts/demo_recuperacion.py receptor
