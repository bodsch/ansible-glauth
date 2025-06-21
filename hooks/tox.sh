#!/usr/bin/env bash

. hooks/molecule.rc

set -e

tox ${TOX_OPTS} -- molecule ${TOX_TEST} ${TOX_ARGS}
