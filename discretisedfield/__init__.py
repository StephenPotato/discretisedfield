import pytest
import pkg_resources
import seaborn as sns  # TODO: Is this necessary?
from .region import Region
from .mesh import Mesh
from .field import Field
from .line import Line
from .interact import interact

__version__ = pkg_resources.get_distribution(__name__).version
__dependencies__ = pkg_resources.require(__name__)


def test():
    return pytest.main(['-v', '--pyargs',
                        'discretisedfield', '-l'])  # pragma: no cover
