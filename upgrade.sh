export PYTHONPATH=$PYTHONPATH:$(dirname "$0")

alembic upgrade head
