import k3d
import itertools
import ipywidgets
import collections
import numpy as np
import discretisedfield as df
import ubermagutil.units as uu
import matplotlib.pyplot as plt
import ubermagutil.typesystem as ts
import discretisedfield.util as dfu
from mpl_toolkits.mplot3d import Axes3D


@ts.typesystem(region=ts.Typed(expected_type=df.Region),
               cell=ts.Vector(size=3, positive=True, const=True),
               n=ts.Vector(size=3, component_type=int, unsigned=True,
                           const=True),
               bc=ts.Typed(expected_type=str),
               subregions=ts.Dictionary(
                   key_descriptor=ts.Name(),
                   value_descriptor=ts.Typed(expected_type=df.Region),
                   allow_empty=True))
class Mesh:
    """Finite difference mesh.

    Mesh discretises cubic ``discretisedfield.Region``, passed as ``region``,
    using a regular finite difference mesh. Since cubic region spans between
    two points :math:`\\mathbf{p}_{1}` and :math:`\\mathbf{p}_{2}`, these
    points can be passed as ``p1`` and ``p2``, instead of passing
    ``discretisedfield.Region`` object. In this case
    ``discretisedfield.Region`` is created internally. Either ``region`` or
    ``p1`` and ``p2`` must be passed, not both. The region is discretised using
    a finite difference cell, whose dimensions are defined with ``cell``.
    Alternatively, the domain can be discretised by passing the number of
    discretisation cells ``n`` in all three dimensions. Either ``cell`` or
    ``n`` should be passed to discretise the region, not both. Periodic
    boundary conditions can be specified by passing ``bc`` argument as a string
    containing one or more characters from ``{'x', 'y', 'z'}`` set (e.g.
    ``'x'``, ``'yz'``, ``'xyz'``). Neumann or Dirichlet boundary conditions are
    defined by passing ``'neumann'`` or ``dirichlet`` string. Neumann and
    Dirichlett boundary conditions are still experimental. If it is necessary
    to define subregions in the mesh, a dictionary can be passed as
    ``subregions``. More precisely, dictionary keys are strings (as valid
    Python variable names), whereas values are ``discretisedfield.Region``
    objects. Subregions are not checked internally, so it is users
    responsibility to make sure subregions are well defined.

    In order to properly define a mesh, mesh region must be an aggregate of
    discretisation cells. Otherwise, ``ValueError`` is raised.

    Parameters
    ----------
    region : discretisedfield.Region, optional

        Cubic region to be discretised on a regular mesh. Either ``region`` or
        ``p1`` and ``p2`` should be defined, not both. Defaults to ``None``.

    p1 / p2 : (3,) array_like, optional

        Points between which the mesh region spans :math:`\\mathbf{p} = (p_{x},
        p_{y}, p_{z})`. Either ``region`` or ``p1`` and ``p2`` should be
        defined, not both. Defaults to ``None``.

    cell : (3,) array_like, optional

        Discretisation cell size :math:`(d_{x}, d_{y}, d_{z})`. Either ``cell``
        or ``n`` should be defined, not both. Defaults to ``None``.

    n : (3,) array_like, optional

        The number of discretisation cells :math:`(n_{x}, n_{y}, n_{z})`.
        Either ``cell`` or ``n`` should be defined, not both. Defaults to
        ``None``.

    bc : str, optional

        Periodic boundary conditions in x, y, or z directions is a string
        consisting of one or more characters ``'x'``, ``'y'``, or ``'z'``,
        denoting the direction(s) along which the mesh is periodic. In the case
        of Neumann or Dirichlet boundary condition, string ``'neumann'`` or
        ``'dirichlet'`` is passed. Defaults to an empty string.

    subregions : dict, optional

        A dictionary defining subregions in the mesh. The keys of the
        dictionary are the region names (``str``) as valid Python variable
        names, whereas the values are ``discretisedfield.Region`` objects.
        Defaults to an empty dictionary.

    Raises
    ------
    ValueError

        If mesh domain is not an aggregate of discretisation cells.
        Alternatively, if both ``region`` as well as ``p1`` and ``p2`` or both
        ``cell`` and ``n`` are passed.

    Examples
    --------
    1. Defining a nano-sized thin film mesh by passing ``region`` and ``cell``
    parameters.

    >>> import discretisedfield as df
    ...
    >>> p1 = (-50e-9, -25e-9, 0)
    >>> p2 = (50e-9, 25e-9, 5e-9)
    >>> cell = (1e-9, 1e-9, 0.1e-9)
    >>> region = df.Region(p1=p1, p2=p2)
    >>> mesh = df.Mesh(region=region, cell=cell)
    >>> mesh
    Mesh(...)

    2. Defining a nano-sized thin film mesh by passing ``p1``, ``p2`` and ``n``
    parameters.

    >>> n = (100, 50, 5)
    >>> mesh = df.Mesh(p1=p1, p2=p2, n=n)
    >>> mesh
    Mesh(...)

    3. Defining a mesh with periodic boundary conditions in :math:`x` and
    :math:`y` directions.

    >>> bc = 'xy'
    >>> region = df.Region(p1=p1, p2=p2)
    >>> mesh = df.Mesh(region=region, n=n, bc=bc)
    >>> mesh
    Mesh(...)

    4. Defining a mesh with two subregions.

    >>> p1 = (0, 0, 0)
    >>> p2 = (100, 100, 100)
    >>> n = (10, 10, 10)
    >>> subregions = {'r1': df.Region(p1=(0, 0, 0), p2=(50, 100, 100)),
    ...               'r2': df.Region(p1=(50, 0, 0), p2=(100, 100, 100))}
    >>> mesh = df.Mesh(p1=p1, p2=p2, n=n, subregions=subregions)
    >>> mesh
    Mesh(...)

    5. An attempt to define a mesh, whose region is not an aggregate of
    discretisation cells in the :math:`z` direction.

    >>> p1 = (-25, 3, 0)
    >>> p2 = (25, 6, 1)
    >>> cell = (5, 3, 0.4)
    >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
    Traceback (most recent call last):
        ...
    ValueError: ...

    """
    def __init__(self, region=None, p1=None, p2=None, n=None, cell=None,
                 bc='', subregions=dict()):
        if region is not None and p1 is None and p2 is None:
            self.region = region
        elif region is None and p1 is not None and p2 is not None:
            self.region = df.Region(p1=p1, p2=p2)
        else:
            msg = 'Either region or p1 and p2 can be passed, not both.'
            raise ValueError(msg)

        if cell is not None and n is None:
            self.cell = tuple(cell)
            n = np.divide(self.region.edges, self.cell).round().astype(int)
            self.n = dfu.array2tuple(n)
        elif n is not None and cell is None:
            self.n = tuple(n)
            cell = np.divide(self.region.edges, self.n).astype(float)
            self.cell = dfu.array2tuple(cell)
        else:
            msg = 'Either n or cell can be passed, not both.'
            raise ValueError(msg)

        # Check if the mesh region is an aggregate of the discretisation cell.
        tol = 1e-12  # picometre tolerance
        rem = np.remainder(self.region.edges, self.cell)
        if np.logical_and(np.greater(rem, tol),
                          np.less(rem, np.subtract(self.cell, tol))).any():
            msg = (f'Region cannot be divided into '
                   f'discretisation cells of size {self.cell}.')
            raise ValueError(msg)

        self.bc = bc.lower()
        self.subregions = subregions

    def __len__(self):
        """Number of discretisation cells in the mesh.

        It is computed by multiplying all elements of ``n``:

        .. math::

            n_\\text{total} = n_{x} n_{y} n_{z}.

        Returns
        -------
        int

            Total number of discretisation cells.

        Examples
        --------
        1. Getting the number of discretisation cells in a mesh.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 5, 0)
        >>> p2 = (5, 15, 2)
        >>> cell = (1, 0.1, 1)
        >>> mesh = df.Mesh(region=df.Region(p1=p1, p2=p2), cell=cell)
        >>> mesh.n
        (5, 100, 2)
        >>> len(mesh)
        1000

        """
        return int(np.prod(self.n))

    @property
    def indices(self):
        """Generator yielding indices of all mesh cells.

        Yields
        ------
        tuple (3,)

            Mesh cell indices :math:`(i_{x}, i_{y}, i_{z})`.

        Examples
        --------
        1. Getting indices of all mesh cells.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (3, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> list(mesh.indices)
        [(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0)]

        .. seealso:: :py:func:`~discretisedfield.Mesh.__iter__`

        """
        for index in itertools.product(*map(range, reversed(self.n))):
            yield tuple(reversed(index))

    def __iter__(self):
        """Generator yielding coordinates of discretisation cells.

        The discretisation cell's coordinate corresponds to its centre point.

        Yields
        ------
        tuple (3,)

            Mesh cell's centre point :math:`\\mathbf{p} = (p_{x}, p_{y},
            p_{z})`.

        Examples
        --------
        1. Getting coordinates of all mesh cells.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(region=df.Region(p1=p1, p2=p2), cell=cell)
        >>> list(mesh)
        [(0.5, 0.5, 0.5), (1.5, 0.5, 0.5), (0.5, 1.5, 0.5), (1.5, 1.5, 0.5)]

        .. seealso:: :py:func:`~discretisedfield.Mesh.indices`

        """
        for index in self.indices:
            yield self.index2point(index)

    def axis_points(self, axis):
        """Points (ticks) on ``axis``.

        This method is a generator yielding points on ``axis`` at which
        discretisation cell coordinates are defined.

        Parameters
        ----------
        axis : str

            Axis ``'x'``, ``'y'``, or ``'z'``.

        Yields
        ------
        numbers.Real

            Point on ``axis``.

        Examples
        --------
        1. Getting points (ticks) on the axis.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (10, 1, 1)
        >>> cell = (2, 1, 1)
        >>> mesh = df.Mesh(region=df.Region(p1=p1, p2=p2), cell=cell)
        ...
        >>> list(mesh.axis_points('x'))
        [1.0, 3.0, 5.0, 7.0, 9.0]

        """
        if isinstance(axis, str):
            axis = dfu.axesdict[axis]

        for i in range(self.n[axis]):
            yield self.index2point((0, 0, 0))[axis] + i*self.cell[axis]

    def __eq__(self, other):
        """Relational operator ``==``.

        Two meshes are considered to be equal if:

          1. Regions of both meshes are equal.

          2. They have the same number of discretisation cells in all three
          directions :math:`n^{1}_{i} = n^{2}_{i}`, for :math:`i = x, y, z`.

        Boundary conditions ``bc`` and ``subregions`` are not considered to be
        necessary conditions for determining equality.

        Parameters
        ----------
        other : discretisedfield.Mesh

            Second operand.

        Returns
        -------
        bool

            ``True`` if two meshes are equal and ``False`` otherwise.

        Examples
        --------
        1. Check if meshes are equal.

        >>> import discretisedfield as df
        ...
        >>> mesh1 = df.Mesh(p1=(0, 0, 0), p2=(5, 5, 5), cell=(1, 1, 1))
        >>> mesh2 = df.Mesh(p1=(0, 0, 0), p2=(5, 5, 5), cell=(1, 1, 1))
        >>> mesh3 = df.Mesh(p1=(1, 1, 1), p2=(5, 5, 5), cell=(2, 2, 2))
        >>> mesh1 == mesh2
        True
        >>> mesh1 != mesh2
        False
        >>> mesh1 == mesh3
        False
        >>> mesh1 != mesh3
        True

        """
        if not isinstance(other, self.__class__):
            return False
        if self.region == other.region and self.n == other.n:
            return True
        else:
            return False

    def __repr__(self):
        """Representation string.

        Returns
        -------
        str

           Representation string.

        Example
        -------
        1. Getting representation string.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> bc = 'x'
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell, bc=bc)
        >>> repr(mesh)
        "Mesh(region=Region(p1=(0, 0, 0), p2=(2, 2, 1)), n=(2, 2, 1), ...)"

        """
        return (f'Mesh(region={repr(self.region)}, n={self.n}, '
                f'bc=\'{self.bc}\', subregions={self.subregions})')

    def index2point(self, index):
        """Convert cell's index to its coordinate.

        Parameters
        ----------
        index : (3,) array_like

            The cell's index :math:`(i_{x}, i_{y}, i_{z})`.

        Returns
        -------
        (3,) tuple

            The cell's coordinate :math:`\\mathbf{p} = (p_{x}, p_{y}, p_{z})`.

        Raises
        ------
        ValueError

            If ``index`` is out of range.

        Examples
        --------
        1. Converting cell's index to its centre point coordinate.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.index2point((0, 0, 0))
        (0.5, 0.5, 0.5)
        >>> mesh.index2point((0, 1, 0))
        (0.5, 1.5, 0.5)

        .. seealso:: :py:func:`~discretisedfield.Mesh.point2index`

        """
        if np.logical_or(np.less(index, 0),
                         np.greater_equal(index, self.n)).any():
            msg = f'Index {index} out of range.'
            raise ValueError(msg)

        point = np.add(self.region.pmin,
                       np.multiply(np.add(index, 0.5), self.cell))
        return dfu.array2tuple(point)

    def point2index(self, point):
        """Convert point to the index of a cell which contains that point.

        Parameters
        ----------
        point : (3,) array_like

            Point :math:`\\mathbf{p} = (p_{x}, p_{y}, p_{z})`.

        Returns
        -------
        (3,) tuple

            The cell's index :math:`(i_{x}, i_{y}, i_{z})`.

        Raises
        ------
        ValueError

            If ``point`` is outside the mesh.

        Examples
        --------
        1. Converting point to the cell's index.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(region=df.Region(p1=p1, p2=p2), cell=cell)
        >>> mesh.point2index((0.2, 1.7, 0.3))
        (0, 1, 0)

        .. seealso:: :py:func:`~discretisedfield.Mesh.index2point`

        """
        if point not in self.region:
            msg = f'Point {point} is outside the mesh region.'
            raise ValueError(msg)

        index = np.subtract(np.divide(np.subtract(point, self.region.pmin),
                                      self.cell), 0.5).round().astype(int)
        # If index is rounded to the out-of-range values.
        index = np.clip(index, 0, np.subtract(self.n, 1))

        return dfu.array2tuple(index)

    def neighbours(self, index):
        """Indices of discretisation cell neighbours.

        Parameters
        ----------
        index : (3,) array_like

            The cell's index :math:`(i_{x}, i_{y}, i_{z})`.

        Returns
        -------
        list

            The list of cell's neighbour indices.

        Raises
        ------
        ValueError

            If ``index`` is outside the mesh.

        Examples
        --------
        1. Getting cell neighbours' indices.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(region=df.Region(p1=p1, p2=p2), cell=cell, bc='xz')
        >>> mesh.neighbours((1, 0, 0))
        [(0, 0, 0), (1, 1, 0)]
        >>> mesh.neighbours((0, 1, 0))
        [(1, 1, 0), (0, 0, 0)]

        """
        if np.logical_or(np.less(index, 0),
                         np.greater_equal(index, self.n)).any():
            msg = f'Index {index} out of range.'
            raise ValueError(msg)

        nghbrs = []
        for axis in range(3):
            for i in [index[axis]-1, index[axis]+1]:
                nghbr_index = list(index)  # make it mutable
                if 0 <= i <= self.n[axis]-1:
                    # not outside the mesh
                    nghbr_index[axis] = i
                elif dfu.raxesdict[axis] in self.bc:
                    if i == -1 and self.n[axis] != 1:
                        nghbr_index[axis] = self.n[0]-1
                    elif i == self.n[axis] and self.n[axis] != 1:
                        nghbr_index[axis] = 0
                if tuple(nghbr_index) != index:
                    nghbrs.append(tuple(nghbr_index))

        # Remove duplicates and preserve order.
        return list(collections.OrderedDict.fromkeys(nghbrs))

    def line(self, p1, p2, n):
        """Line generator.

        Given two points ``p1`` and ``p2`` line is defined and ``n`` points on
        that line are generated and yielded in ``n`` iterations:

        .. math::

           \\mathbf{r}_{i} = i\\frac{\\mathbf{p}_{2} - \\mathbf{p}_{1}}{n-1},
           \\text{for}\\, i = 0, ..., n-1

        Parameters
        ----------
        p1 / p2 : (3,) array_like

            Points between which the line is defined :math:`\\mathbf{p} =
            (p_{x}, p_{y}, p_{z})`.

        n : int

            Number of points on the line.

        Yields
        ------
        tuple (3,)

            :math:`\\mathbf{r}_{i}`

        Raises
        ------
        ValueError

            If ``p1`` or ``p2`` is outside the mesh region.

        Examples
        --------
        1. Creating line generator.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 2)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        ...
        >>> line = mesh.line(p1=(0, 0, 0), p2=(2, 0, 0), n=2)
        >>> list(line)
        [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0)]

        .. seealso:: :py:func:`~discretisedfield.Region.plane`

        """
        if p1 not in self.region or p2 not in self.region:
            msg = f'Point {p1=} or point {p2=} is outside the mesh region.'
            raise ValueError(msg)

        dl = np.subtract(p2, p1) / (n-1)
        for i in range(n):
            yield dfu.array2tuple(np.add(p1, i*dl))

    def plane(self, *args, n=None, **kwargs):
        """Extracts plane mesh.

        If one of the axes (``'x'``, ``'y'``, or ``'z'``) is passed as a
        string, a plane mesh perpendicular to that axis is extracted,
        intersecting the mesh region at its centre. Alternatively, if a keyword
        argument is passed (e.g. ``x=1e-9``), a plane perpendicular to the
        x-axis (parallel to yz-plane) and intersecting it at ``x=1e-9`` is
        extracted. The number of points in two dimensions on the plane can be
        defined using ``n`` tuple (e.g. ``n=(10, 15)``).

        The resulting mesh has an attribute ``info``, which is a dictionary
        containing basic information about the plane mesh.

        Parameters
        ----------
        n : (2,) tuple

            The number of points on the plane in two dimensions.

        Returns
        ------
        discretisedfield.Mesh

            An extracted mesh.

        Examples
        --------
        1. Extracting the plane mesh at a specific point (``y=1``).

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (5, 5, 5)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        ...
        >>> plane_mesh = mesh.plane(y=1)

        2. Extracting the xy-plane mesh at the mesh region centre.

        >>> plane_mesh = mesh.plane('z')

        3. Specifying the number of points on the plane.

        >>> plane_mesh = mesh.plane('z', n=(3, 3))

        .. seealso:: :py:func:`~discretisedfield.Region.line`

        """
        if args and not kwargs:
            if len(args) != 1:
                msg = f'Multiple args ({args}) passed.'
                raise ValueError(msg)

            # Only planeaxis is provided via args and the point is defined as
            # the centre of the sample.
            planeaxis = dfu.axesdict[args[0]]
            point = self.region.centre[planeaxis]
        elif kwargs and not args:
            if len(kwargs) != 1:
                msg = f'Multiple kwargs ({kwargs}) passed.'
                raise ValueError(msg)

            planeaxis, point = list(kwargs.items())[0]
            planeaxis = dfu.axesdict[planeaxis]

            # Check if point is outside the mesh region.
            test_point = list(self.region.centre)  # make it mutable
            test_point[planeaxis] = point
            if test_point not in self.region:
                msg = f'Point {test_point} is outside the mesh region.'
                raise ValueError(msg)
        else:
            msg = 'Either one arg or one kwarg can be passed, not both.'
            raise ValueError(msg)

        # Get indices of in-plane axes.
        axis1, axis2 = tuple(filter(lambda val: val != planeaxis,
                                    dfu.axesdict.values()))

        if n is None:
            n = (self.n[axis1], self.n[axis2])

        # Build plane-mesh.
        p1pm, p2pm, npm = np.zeros(3), np.zeros(3), np.zeros(3, dtype=int)
        ilist = [axis1, axis2, planeaxis]
        p1pm[ilist] = (self.region.pmin[axis1],
                       self.region.pmin[axis2],
                       point - self.cell[planeaxis]/2)
        p2pm[ilist] = (self.region.pmax[axis1],
                       self.region.pmax[axis2],
                       point + self.cell[planeaxis]/2)
        npm[ilist] = (*n, 1)

        plane_mesh = self.__class__(p1=p1pm, p2=p2pm, n=dfu.array2tuple(npm))

        # Add info dictionary, so that the mesh can be interpreted easier.
        info = dict()
        info['planeaxis'] = planeaxis
        info['point'] = point
        info['axis1'], info['axis2'] = axis1, axis2
        plane_mesh.info = info

        return plane_mesh

    def __or__(self, other):
        """Check if ``other`` mesh is aligned to ``self``.

        Two meshes are considered to be aligned if and only if:

            1. They have the same discretisation cell.
            2. Coordinates of cells in ``other`` are in coodinates of ``self``.

        Parameters
        ----------
        other : discretisedfield.Mesh

            Second operand.

        Returns
        -------
        bool

            ``True`` if meshes are aligned. ``False`` otherwise.

        Examples
        --------
        1. Check whether two meshes are aligned.

        >>> import discretisedfield as df
        ...
        >>> p1 = (-50e-9, -25e-9, 0)
        >>> p2 = (50e-9, 25e-9, 5e-9)
        >>> cell = (5e-9, 5e-9, 5e-9)
        >>> region1 = df.Region(p1=p1, p2=p2)
        >>> mesh1 = df.Mesh(region=region1, cell=cell)
        ...
        >>> p1 = (-45e-9, -20e-9, 0)
        >>> p2 = (10e-9, 20e-9, 5e-9)
        >>> cell = (5e-9, 5e-9, 5e-9)
        >>> region2 = df.Region(p1=p1, p2=p2)
        >>> mesh2 = df.Mesh(region=region2, cell=cell)
        ...
        >>> p1 = (-42e-9, -20e-9, 0)
        >>> p2 = (13e-9, 20e-9, 5e-9)
        >>> cell = (5e-9, 5e-9, 5e-9)
        >>> region3 = df.Region(p1=p1, p2=p2)
        >>> mesh3 = df.Mesh(region=region3, cell=cell)
        ...
        >>> mesh1 | mesh2
        True
        >>> mesh1 | mesh3
        False
        >>> mesh1 | mesh1
        True

        """
        if self.cell != other.cell:
            return False

        tol = 1e-12  # picometre tolerance
        for i in ['pmin', 'pmax']:
            diff = np.subtract(getattr(self.region, i),
                               getattr(other.region, i))
            rem = np.remainder(abs(diff), self.cell)
            if np.logical_and(np.greater(rem, tol),
                              np.less(rem, np.subtract(self.cell, tol))).any():
                return False

        return True

    def __getitem__(self, item):
        """Extracts the mesh of a subregion.

        If subregions were defined by passing ``subregions`` dictionary when
        the mesh was created, this method returns a mesh defined on a subregion
        with key ``item``. Alternatively, a ``discretisedfield.Region``
        object can be passed and a minimum-sized mesh containing it will be
        returned. The resulting mesh has the same discretisation cell as the
        original mesh.

        Parameters
        ----------
        item : str, discretisedfield.Region

            The key of a subregion in ``subregions`` dictionary or a region
            object.

        Returns
        -------
        disretisedfield.Mesh

            Mesh of a subregion.

        Example
        -------
        1. Extract subregion mesh by passing a subregion key.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (100, 100, 100)
        >>> cell = (10, 10, 10)
        >>> subregions = {'r1': df.Region(p1=(0, 0, 0), p2=(50, 100, 100)),
        ...               'r2': df.Region(p1=(50, 0, 0), p2=(100, 100, 100))}
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell, subregions=subregions)
        ...
        >>> len(mesh)  # number of discretisation cells
        1000
        >>> mesh.region.pmin
        (0, 0, 0)
        >>> mesh.region.pmax
        (100, 100, 100)
        >>> submesh = mesh['r1']
        >>> len(submesh)
        500
        >>> submesh.region.pmin
        (0, 0, 0)
        >>> submesh.region.pmax
        (50, 100, 100)

        2. Extracting a submesh on a "newly-defined" region.

        >>> import discretisedfield as df
        ...
        >>> p1 = (-50e-9, -25e-9, 0)
        >>> p2 = (50e-9, 25e-9, 5e-9)
        >>> cell = (5e-9, 5e-9, 5e-9)
        >>> region = df.Region(p1=p1, p2=p2)
        >>> mesh = df.Mesh(region=region, cell=cell)
        ...
        >>> subregion = df.Region(p1=(0, 1e-9, 0), p2=(10e-9, 14e-9, 5e-9))
        >>> submesh = mesh[subregion]
        >>> submesh.cell
        (5e-09, 5e-09, 5e-09)
        >>> submesh.n
        (2, 3, 1)

        """
        if isinstance(item, str):
            return self.__class__(region=self.subregions[item], cell=self.cell)

        if item not in self.region:
            msg = 'Subregion is outside the mesh region.'
            raise ValueError(msg)

        pmin = self.index2point(self.point2index(item.pmin))
        pmax = self.index2point(self.point2index(item.pmax))
        half_cell = np.divide(self.cell, 2)

        return self.__class__(region=df.Region(p1=np.subtract(pmin, half_cell),
                                               p2=np.add(pmax, half_cell)),
                              cell=self.cell)

    def pad(self, pad_width):
        """Mesh padding.

        This method extends the mesh by adding (padding) discretisation cells
        in chosen direction. The way in which the mesh is going to be padded is
        defined by passing ``pad_width`` dictionary. The keys of the dictionary
        are the directions (axes), e.g. ``'x'``, ``'y'``, or ``'z'``, whereas
        the values are the tuples of length 2. The first integer in the tuple
        is the number of cells added in the negative direction, and the second
        integer is the number of cells added in the positive direction.

        Parameters
        ----------
        pad_width : dict

            The keys of the dictionary are the directions (axes), e.g. ``'x'``,
            ``'y'``, or ``'z'``, whereas the values are the tuples of length 2.
            The first integer in the tuple is the number of cells added in the
            negative direction, and the second integer is the number of cells
            added in the positive direction.

        Returns
        -------
        discretisedfield.Mesh

            Extended mesh.

        Examples
        --------
        1. Padding a mesh in the x and y directions by 1 cell.

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (100, 100, 100)
        >>> cell = (10, 10, 10)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        ...
        >>> mesh.region.edges
        (100, 100, 100)
        >>> padded_mesh = mesh.pad({'x': (1, 1), 'y': (1, 1), 'z': (0, 1)})
        >>> padded_mesh.region.edges
        (120, 120, 110)
        >>> padded_mesh.n
        (12, 12, 11)

        """
        # Convert to np.ndarray to allow operations on them.
        pmin = np.array(self.region.pmin)
        pmax = np.array(self.region.pmax)
        for direction in pad_width.keys():
            axis = dfu.axesdict[direction]
            pmin[axis] -= pad_width[direction][0] * self.cell[axis]
            pmax[axis] += pad_width[direction][1] * self.cell[axis]

        return self.__class__(p1=pmin, p2=pmax, cell=self.cell, bc=self.bc)

    @property
    def dV(self):
        """Volume of a discretisation cell.

        This property is used for calculating volume integrals.

        Returns
        -------
        float

            Discretisation cell volume.

        Examples
        --------
        1. Discretisation cell volume

        >>> import discretisedfield as df
        ...
        >>> p1 = (0, 0, 0)
        >>> p2 = (100, 100, 100)
        >>> cell = (10, 10, 10)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        ...
        >>> mesh.dV
        1000

        """
        return np.product(self.cell)

    def mpl(self, ax=None, figsize=None, color=dfu.cp_hex[:2], multiplier=None,
            filename=None, **kwargs):
        """``matplotlib`` plot.

        If ``ax`` is not passed, ``matplotlib.axes.Axes`` object is created
        automatically and the size of a figure can be specified using
        ``figsize``. The color of lines depicting the region and the
        discretisation cell can be specified using ``color`` length-2 tuple,
        where the first element is the colour of the region and the second
        element is the colour of the discretisation cell. The plot is saved in
        PDF-format if ``filename`` is passed.

        It is often the case that the object size is either small (e.g. on a
        nanoscale) or very large (e.g. in units of kilometers). Accordingly,
        ``multiplier`` can be passed as :math:`10^{n}`, where :math:`n` is a
        multiple of 3 (..., -6, -3, 0, 3, 6,...). According to that value, the
        axes will be scaled and appropriate units shown. For instance, if
        ``multiplier=1e-9`` is passed, all axes will be divided by
        :math:`1\\,\\text{nm}` and :math:`\\text{nm}` units will be used as
        axis labels. If ``multiplier`` is not passed, the best one is
        calculated internally.

        This method is based on ``matplotlib.pyplot.plot``, so any keyword
        arguments accepted by it can be passed (for instance, ``linewidth``,
        ``linestyle``, etc.).

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional

            Axes to which the plot is added. Defaults to ``None`` - axes are
            created internally.

        figsize : (2,) tuple, optional

            The size of a created figure if ``ax`` is not passed. Defaults to
            ``None``.

        color : (2,) array_like

            A valid ``matplotlib`` color for lines depicting the region.
            Defaults to the default color palette.

        multiplier : numbers.Real, optional

            Axes multiplier. Defaults to ``None``.

        filename : str, optional

            If filename is passed, the plot is saved. Defaults to ``None``.

        Examples
        --------
        1. Visualising the mesh using ``matplotlib``.

        >>> import discretisedfield as df
        ...
        >>> p1 = (-50e-9, -50e-9, 0)
        >>> p2 = (50e-9, 50e-9, 10e-9)
        >>> region = df.Region(p1=p1, p2=p2)
        >>> mesh = df.Mesh(region=region, n=(50, 50, 5))
        ...
        >>> mesh.mpl()

        .. seealso:: :py:func:`~discretisedfield.Mesh.k3d`

        """
        if ax is None:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111, projection='3d')

        if multiplier is None:
            multiplier = uu.si_max_multiplier(self.region.edges)

        cell_region = df.Region(p1=self.region.pmin,
                                p2=np.add(self.region.pmin, self.cell))
        self.region.mpl(ax=ax, color=color[0], multiplier=multiplier, **kwargs)
        cell_region.mpl(ax=ax, color=color[1], multiplier=multiplier, **kwargs)

        if filename is not None:
            plt.savefig(filename, bbox_inches='tight', pad_inches=0)

    def mpl_subregions(self, ax=None, figsize=None, color=dfu.cp_hex,
                       multiplier=None, filename=None, **kwargs):
        """``matplotlib`` subregions plot.

        If ``ax`` is not passed, ``matplotlib.axes.Axes`` object is created
        automatically and the size of a figure can be specified using
        ``figsize``. The color of lines depicting subregions and can be
        specified using ``color`` list. The plot is saved in PDF-format if
        ``filename`` is passed.

        It is often the case that the object size is either small (e.g. on a
        nanoscale) or very large (e.g. in units of kilometers). Accordingly,
        ``multiplier`` can be passed as :math:`10^{n}`, where :math:`n` is a
        multiple of 3 (..., -6, -3, 0, 3, 6,...). According to that value, the
        axes will be scaled and appropriate units shown. For instance, if
        ``multiplier=1e-9`` is passed, all axes will be divided by
        :math:`1\\,\\text{nm}` and :math:`\\text{nm}` units will be used as
        axis labels. If ``multiplier`` is not passed, the best one is
        calculated internally.

        This method is based on ``matplotlib.pyplot.plot``, so any keyword
        arguments accepted by it can be passed (for instance, ``linewidth``,
        ``linestyle``, etc.).

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional

            Axes to which the plot is added. Defaults to ``None`` - axes are
            created internally.

        figsize : (2,) tuple, optional

            The size of a created figure if ``ax`` is not passed. Defaults to
            ``None``.

        color : array_like

            Subregion colours. Defaults to the default color palette.

        multiplier : numbers.Real, optional

            Axes multiplier. Defaults to ``None``.

        filename : str, optional

            If filename is passed, the plot is saved. Defaults to ``None``.

        Examples
        --------
        1. Visualising subregions using ``matplotlib``.

        >>> p1 = (0, 0, 0)
        >>> p2 = (100, 100, 100)
        >>> n = (10, 10, 10)
        >>> subregions = {'r1': df.Region(p1=(0, 0, 0), p2=(50, 100, 100)),
        ...               'r2': df.Region(p1=(50, 0, 0), p2=(100, 100, 100))}
        >>> mesh = df.Mesh(p1=p1, p2=p2, n=n, subregions=subregions)
        ...
        >>> mesh.mpl_subregions()

        .. seealso:: :py:func:`~discretisedfield.Mesh.k3d_subregions`

        """
        if ax is None:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111, projection='3d')

        if multiplier is None:
            multiplier = uu.si_max_multiplier(self.region.edges)

        for i, subregion in enumerate(self.subregions.values()):
            subregion.mpl(ax=ax, multiplier=multiplier,
                          color=color[i % len(color)], **kwargs)

        if filename is not None:
            plt.savefig(filename, bbox_inches='tight', pad_inches=0)

    def k3d(self, plot=None, color=dfu.cp_int[:2], multiplier=None,
            **kwargs):
        """``k3d`` plot.

        If ``plot`` is not passed, ``k3d.Plot`` object is created
        automatically. The color of the region and the discretisation cell can
        be specified using ``color`` length-2 tuple, where the first element is
        the colour of the region and the second element is the colour of the
        discretisation cell.

        It is often the case that the object size is either small (e.g. on a
        nanoscale) or very large (e.g. in units of kilometers). Accordingly,
        ``multiplier`` can be passed as :math:`10^{n}`, where :math:`n` is a
        multiple of 3 (..., -6, -3, 0, 3, 6,...). According to that value, the
        axes will be scaled and appropriate units shown. For instance, if
        ``multiplier=1e-9`` is passed, all axes will be divided by
        :math:`1\\,\\text{nm}` and :math:`\\text{nm}` units will be used as
        axis labels. If ``multiplier`` is not passed, the best one is
        calculated internally.

        This method is based on ``k3d.voxels``, so any keyword arguments
        accepted by it can be passed (e.g. ``wireframe``).

        Parameters
        ----------
        plot : k3d.Plot, optional

            Plot to which the plot is added. Defaults to ``None`` - plot is
            created internally.

        color : (2,) array_like

            Colour of the region and the discretisation cell. Defaults to the
            default color palette.

        multiplier : numbers.Real, optional

            Axes multiplier. Defaults to ``None``.

        Examples
        --------
        1. Visualising the mesh using ``k3d``.

        >>> p1 = (0, 0, 0)
        >>> p2 = (100, 100, 100)
        >>> n = (10, 10, 10)
        >>> mesh = df.Mesh(p1=p1, p2=p2, n=n)
        ...
        >>> mesh.k3d()
        Plot(...)

        .. seealso:: :py:func:`~discretisedfield.Mesh.mpl`

        """
        if plot is None:
            plot = k3d.plot()
            plot.display()

        if multiplier is None:
            multiplier = uu.si_max_multiplier(self.region.edges)

        unit = f'({uu.rsi_prefixes[multiplier]}m)'

        plot_array = np.ones(tuple(reversed(self.n))).astype(np.uint8)
        plot_array[0, 0, -1] = 2  # mark the discretisation cell

        bounds = [i for sublist in
                  zip(np.divide(self.region.pmin, multiplier),
                      np.divide(self.region.pmax, multiplier))
                  for i in sublist]

        plot += k3d.voxels(plot_array, color_map=color, bounds=bounds,
                           outlines=False, **kwargs)

        plot.axes = [i + r'\,\text{{{}}}'.format(unit)
                     for i in dfu.axesdict.keys()]

    def k3d_subregions(self, plot=None, color=dfu.cp_int, multiplier=None,
                       **kwargs):
        """``k3d`` subregions plot.

        If ``plot`` is not passed, ``k3d.Plot`` object is created
        automatically. The color of the subregions can be specified using
        ``color``.

        It is often the case that the object size is either small (e.g. on a
        nanoscale) or very large (e.g. in units of kilometers). Accordingly,
        ``multiplier`` can be passed as :math:`10^{n}`, where :math:`n` is a
        multiple of 3 (..., -6, -3, 0, 3, 6,...). According to that value, the
        axes will be scaled and appropriate units shown. For instance, if
        ``multiplier=1e-9`` is passed, all axes will be divided by
        :math:`1\\,\\text{nm}` and :math:`\\text{nm}` units will be used as
        axis labels. If ``multiplier`` is not passed, the best one is
        calculated internally.

        This method is based on ``k3d.voxels``, so any keyword arguments
        accepted by it can be passed (e.g. ``wireframe``).

        Parameters
        ----------
        plot : k3d.Plot, optional

            Plot to which the plot is added. Defaults to ``None`` - plot is
            created internally.

        color : array_like

            Colour of the subregions. Defaults to the default color palette.

        multiplier : numbers.Real, optional

            Axes multiplier. Defaults to ``None``.

        Examples
        --------
        1. Visualising subregions using ``k3d``.

        >>> p1 = (0, 0, 0)
        >>> p2 = (100, 100, 100)
        >>> n = (10, 10, 10)
        >>> subregions = {'r1': df.Region(p1=(0, 0, 0), p2=(50, 100, 100)),
        ...               'r2': df.Region(p1=(50, 0, 0), p2=(100, 100, 100))}
        >>> mesh = df.Mesh(p1=p1, p2=p2, n=n, subregions=subregions)
        ...
        >>> mesh.k3d_subregions()
        Plot(...)

        .. seealso:: :py:func:`~discretisedfield.Mesh.mpl_subregions`

        """
        if plot is None:
            plot = k3d.plot()
            plot.display()

        if multiplier is None:
            multiplier = uu.si_max_multiplier(self.region.edges)

        unit = f'({uu.rsi_prefixes[multiplier]}m)'

        plot_array = np.zeros(self.n)
        for index in self.indices:
            for i, subregion in enumerate(self.subregions.values()):
                if self.index2point(index) in subregion:
                    # +1 to avoid 0 value - invisible voxel
                    plot_array[index] = (i % len(color)) + 1
                    break
        # swap axes for k3d.voxels and astypr to avoid k3d warning
        plot_array = np.swapaxes(plot_array, 0, 2).astype(np.uint8)

        bounds = [i for sublist in
                  zip(np.divide(self.region.pmin, multiplier),
                      np.divide(self.region.pmax, multiplier))
                  for i in sublist]

        plot += k3d.voxels(plot_array, color_map=color, bounds=bounds,
                           outlines=False, **kwargs)

        plot.axes = [i + r'\,\text{{{}}}'.format(unit)
                     for i in dfu.axesdict.keys()]

    def slider(self, axis, multiplier=None, description=None, **kwargs):
        """Axis slider.

        For ``axis``, ``'x'``, ``'y'``, or ``'z'`` is passed. Based on that
        value, ``ipywidgets.SelectionSlider`` is returned. Axis multiplier can
        be changed via ``multiplier``.

        This method is based on ``ipywidgets.SelectionSlider``, so any keyword
        argument accepted by it can be passed.

        Parameters
        ----------
        axis : str

            Axis for which the slider is returned (``'x'``, ``'y'``, or
            ``'z'``).

        multiplier : numbers.Real, optional

            Axis multiplier. Defaults to ``None``.

        Returns
        -------
        ipywidgets.SelectionSlider

            Axis slider.

        Example
        -------
        1. Get the slider for the x-coordinate.

        >>> p1 = (0, 0, 0)
        >>> p2 = (10e-9, 10e-9, 10e-9)
        >>> n = (10, 10, 10)
        >>> mesh = df.Mesh(p1=p1, p2=p2, n=n)
        ...
        >>> mesh.slider('x')
        SelectionSlider(...)

        """
        if isinstance(axis, str):
            axis = dfu.axesdict[axis]

        if multiplier is None:
            multiplier = uu.si_multiplier(self.region.edges[axis])

        slider_min = self.index2point((0, 0, 0))[axis]
        slider_max = self.index2point(np.subtract(self.n, 1))[axis]
        slider_step = self.cell[axis]
        if description is None:
            description = (f'{dfu.raxesdict[axis]} '
                           f'({uu.rsi_prefixes[multiplier]}m)')

        values = np.arange(slider_min, slider_max+1e-20, slider_step)
        labels = np.around(values/multiplier, decimals=3)
        options = list(zip(labels, values))

        # Select middle element for slider value
        slider_value = values[int(self.n[axis]/2)]

        return ipywidgets.SelectionSlider(options=options,
                                          value=slider_value,
                                          description=description,
                                          **kwargs)

    def axis_selector(self, widget='dropdown', description='axis'):
        """Axis selector.

        For ``widget='dropdown'``, ``ipywidgets.Dropdown`` is returned, whereas
        for ``widget='radiobuttons'``, ``ipywidgets.RadioButtons`` is returned.
        Default widget description can be changed using ``description``.

        Parameters
        ----------
        widget : str

            Type of widget to be returned. Defaults to ``'dropdown'``.

        description : str

            Widget description to be showed. Defaults to ``'axis'``.

        Returns
        -------
        ipywidgets.Dropdown, ipywidgets.RadioButtons

            Axis selection widget.

        Example
        -------
        1. Get the ``RadioButtons`` slider.

        >>> p1 = (0, 0, 0)
        >>> p2 = (10e-9, 10e-9, 10e-9)
        >>> n = (10, 10, 10)
        >>> mesh = df.Mesh(p1=p1, p2=p2, n=n)
        ...
        >>> mesh.axis_selector(widget='radiobuttons')
        RadioButtons(...)

        """
        if widget.lower() == 'dropdown':
            widget_cls = ipywidgets.Dropdown
        elif widget == 'radiobuttons':
            widget_cls = ipywidgets.RadioButtons
        else:
            msg = f'Widget {widget} is not supported.'
            raise ValueError(msg)

        return widget_cls(options=list(dfu.axesdict.keys()),
                          value='z',
                          description=description,
                          disabled=False)
