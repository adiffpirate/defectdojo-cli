from .util import Util
from .findings import Findings
from .engagements import Engagements
from .tests import Tests
import pkg_resources  # part of setuptools

__version__ = pkg_resources.get_distribution("defectdojo_cli").version
