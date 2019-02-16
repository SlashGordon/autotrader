export PYTHONPATH=$PYTHONPATH:$(dirname "$0")

alembic downgrade head
