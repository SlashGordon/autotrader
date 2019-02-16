@echo off

set scriptdir=%~dp0
SET PYTHONPATH=%PYTHONPATH%;%scriptdir%

alembic revision --autogenerate

pause