import pkg_resources
from subprocess import call

for dist in pkg_resources.working_set:
    package = dist.project_name
    call(f"pip install --upgrade {package}", shell=True)