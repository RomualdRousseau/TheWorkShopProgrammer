set dotenv-load

#
# VARIABLES
#

#
# EXPORTS
#

export ROOT_DIR := `pwd`

#
# HELPERS
#

default: help

# Print the available recipes
help:
    @just --justfile {{justfile()}} --list

# install poetry with no root
initialize:
    poetry install --no-root
    python -m ipykernel install --prefix .venv --name kernel-py311

# update poetry with
update:
    poetry update