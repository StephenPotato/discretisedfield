import random
import numpy as np
import matplotlib.pyplot as plt
import joommfutil.typesystem as ts
import discretisedfield.util as dfu
from mpl_toolkits.mplot3d import Axes3D


@ts.typesystem(p1=ts.ConstantRealVector(size=3),
               p2=ts.ConstantRealVector(size=3),
               cell=ts.ConstantPositiveRealVector(size=3),
               name=ts.ConstantObjectName)
class Mesh:
    """Finite difference rectangular mesh.

    The rectangular mesh domain spans between two points `p1` and
    `p2`. They are defined as ``array_like`` objects of length 3
    (e.g. ``tuple``, ``list``, ``numpy.ndarray``), :math:`p = (p_{x},
    p_{y}, p_{z})`. The domain is then discretised into finite
    difference cells, where dimensions of a single cell is defined
    with a `cell` parameter. Similar to `p1` and `p2`, `cell`
    parameter is an ``array_like`` object :math:`(d_{x}, d_{y},
    d_{z})` of length 3. The parameter `name` is optional and defaults
    to "mesh".

    In order to properly define a mesh, the length of all mesh domain
    edges must not be zero, and the mesh domain must be an aggregate
    of discretisation cells.

    Parameters
    ----------
    p1, p2 : (3,) array_like
        Points between which the mesh domain spans :math:`p = (p_{x},
        p_{y}, p_{z})`.
    cell : (3,) array_like
        Discretisation cell size :math:`(d_{x}, d_{y}, d_{z})`.
    name : str, optional
        Mesh name (the default is "mesh"). The mesh name must be a valid
        Python variable name string. More specifically, it must not
        contain spaces, or start with underscore or numeric character.

    Raises
    ------
    ValueError
        If the length of one or more mesh domain edges is zero, or
        mesh domain is not an aggregate of discretisation cells.

    Examples
    --------
    1. Creating a nano-sized thin film mesh object

    >>> import discretisedfield as df
    >>> p1 = (-50e-9, -25e-9, 0)
    >>> p2 = (50e-9, 25e-9, 5e-9)
    >>> cell = (1e-9, 1e-9, 0.1e-9)
    >>> name = "mesh_name"
    >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell, name=name)

    2. An attempt to create a mesh with invalid parameters, so that
    the ``ValueError`` is raised. In this example, the mesh domain is
    not an aggregate of discretisation cells in the :math:`z`
    direction.

    >>> import discretisedfield as df
    >>> p1 = (-25, 3, 0)
    >>> p2 = (25, 6, 1)
    >>> cell = (5, 1, 0.3)
    >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell, name=name)
    Traceback (most recent call last):
        ...
    ValueError: ...

    """
    def __init__(self, p1, p2, cell, name="mesh"):
        self.p1 = tuple(p1)
        self.p2 = tuple(p2)
        self.cell = tuple(cell)
        self.name = name

        # Is the length of any mesh domain edge zero?
        for i in range(3):
            if self.l[i] == 0:
                msg = "Mesh domain edge length is zero (l[{}]==0).".format(i)
                raise ValueError(msg)

        # Is the discretisation cell greater than the mesh domain?
        for i in range(3):
            if self.cell[i] > self.l[i]:
                msg = ("Discretisation cell is greater than the mesh domain: "
                       "cell[{0}] > abs(p2[{0}]-p1[{0}]).").format(i)
                raise ValueError(msg)

        # Is the mesh domain not an aggregate of discretisation cells?
        tol = 1e-12  # picometer tolerance
        for i in range(3):
            if tol < self.l[i] % self.cell[i] < self.cell[i] - tol:
                msg = ("Mesh domain is not an aggregate of the discretisation "
                       "cell: abs(p2[{0}]-p1[{0}]) % cell[{0}].").format(i)
                raise ValueError(msg)

    @property
    def pmin(self):
        """Point contained in the mesh domain with minimum coordinates.
        
        The :math:`i`-th component of :math:`p_\\text{min}` is computed
        from the points :math:`p_{1}` and :math:`p_{2}` between which
        the mesh domain spans: :math:`p_\\text{min}^{i} =
        \\text{min}(p_{1}^{i}, p_{2}^{i})`.

        Returns
        -------
        tuple (3,)
            Point with minimum mesh coordinates :math:`(p_{x}^\\text{min},
            p_{y}^\\text{min}, p_{z}^\\text{min})`.

        Example
        -------
        Getting the minimum domain coordinate as the mesh object property.

        >>> import discretisedfield as df
        >>> p1 = (-1.1, 2.9, 0)
        >>> p2 = (5, 0, 0.01)
        >>> cell = (0.1, 0.1, 0.005)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.pmin
        (-1.1, 0, 0)

        .. note::

           Please note this method is a property and should be called
           as ``mesh.pmin``, not ``mesh.pmin()``.

        .. seealso:: :py:func:`~discretisedfield.Mesh.pmax`

        """
        return tuple(min(coords) for coords in zip(self.p1, self.p2))

    @property
    def pmax(self):
        """Point contained in the mesh domain with maximum coordinates.

        The :math:`i`-th component of :math:`p_\\text{max}` is computed
        from the points :math:`p_{1}` and :math:`p_{2}` between which
        the mesh domain spans: :math:`p_\\text{min}^{i} =
        \\text{max}(p_{1}^{i}, p_{2}^{i})`.

        Returns
        -------
        tuple (3,)
            Point with maximum mesh coordinates :math:`(p_{x}^\\text{max},
            p_{y}^\\text{max}, p_{z}^\\text{max})`.

        Example
        -------
        Getting the maximum domain coordinate as the mesh object property.

        >>> import discretisedfield as df
        >>> p1 = (-1.1, 2.9, 0)
        >>> p2 = (5, 0, 0.01)
        >>> cell = (0.1, 0.1, 0.005)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.pmax
        (5, 2.9, 0.01)

        .. note::

           Please note this method is a property and should be called
           as ``mesh.pmin``, not ``mesh.pmax()``.

        .. seealso:: :py:func:`~discretisedfield.Mesh.pmax`

        """
        return tuple(max(coords) for coords in zip(self.p1, self.p2))

    @property
    def l(self):
        """Mesh domain edge lengths.

        Edge length in any direction :math:`i` is computed from the
        points between which the mesh domain spans :math:`l^{i} =
        |p_{2}^{i} - p_{1}^{i}|`.

        Returns
        -------
        tuple (3,)
            Lengths of mesh domain edges :math:`(l_{x}, l_{y}, l_{z})`.

        Example
        -------
        Getting mesh domain edge lengths.

        >>> import discretisedfield as df
        >>> p1 = (0, 0, -5)
        >>> p2 = (5, 15, 15)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.l
        (5, 15, 20)

        .. note::

           Please note this method is a property and should be called
           as ``mesh.l``, not ``mesh.l()``.

        """
        return tuple(abs(c2-c1) for c1, c2 in zip(self.p1, self.p2))

    @property
    def n(self):
        """Number of discretisation cells in all directions.

        By dividing the lengths of mesh domain edges with
        discretisation in all directions, the number of cells is
        computed :math:`n^{i} = l^{i}/d^{i}`.

        Returns
        -------
        tuple (3,)
            The number of discretisation cells :math:`(n_{x},
            n_{y}, n_{z})`.

        Example
        -------
        Getting the number of discretisation cells in all three direction.

        >>> import discretisedfield as df
        >>> p1 = (0, 5, 0)
        >>> p2 = (5, 15, 1)
        >>> cell = (0.5, 0.1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.n
        (10, 100, 1)

        .. note::

           Please note this method is a property and should be called
           as ``mesh.n``, not ``mesh.n()``.
    
        """
        return tuple(int(round(l/d)) for l, d in zip(self.l, self.cell))

    @property
    def centre(self):
        """Mesh domain centre point.

        This point does not necessarily coincides with the
        discretisation cell centre. It is computed as the middle point
        between minimum and maximum coordinate :math:`p_{c}^{i} =
        p_\\text{min}^{i} + 0.5l^{i}`, where :math:`p_\\text{min}^{i}`
        is the :math:`i`-th coordinate of the minimum mesh domain
        point and :math:`l^{i}` is the mesh domain edge length in the
        :math:`i`-th direction.

        Returns
        -------
        tuple (3,)
            Mesh domain centre point :math:`(c_{x}, c_{y}, c_{z})`.

        Example
        -------
        Getting the mesh centre point.

        >>> import discretisedfield as df
        >>> p1 = (0, 0, 0)
        >>> p2 = (5, 15, 18)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.centre
        (2.5, 7.5, 9.0)

        """
        return tuple(pmini+0.5*li for pmini, li in zip(self.pmin, self.l))

    @property
    def indices(self):
        """Generator iterating through all mesh cells and yielding their
        indices.

        Yields
        ------
        tuple (3,)
            Mesh cell indices (`ix`, `iy`, `iz`).


        Example
        -------
        Getting all mesh cell indices.

        >>> import discretisedfield as df
        >>> p1 = (0, 0, 0)
        >>> p2 = (3, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> tuple(mesh.indices)
        ((0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (1, 1, 0), (2, 1, 0))

        """
        for k in range(self.n[2]):
            for j in range(self.n[1]):
                for i in range(self.n[0]):
                    yield (i, j, k)

    @property
    def coordinates(self):
        """Generator iterating through all mesh cells and yielding their
        coordinates.

        Yields
        ------
        tuple (3,)
            Mesh cell coordinates (`px`, `py`, `pz`).


        Example
        -------
        Getting all mesh cell coordinates.

        >>> import discretisedfield as df
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> tuple(mesh.coordinates)
        ((0.5, 0.5, 0.5), (1.5, 0.5, 0.5), (0.5, 1.5, 0.5), (1.5, 1.5, 0.5))

        """
        for i in self.indices:
            yield self.index2point(i)

    def __repr__(self):
        """Mesh representation.

        This method returns the string that can be copied in another
        Python script so that exactly the same mesh object would be
        reproduced.
        
        Returns
        -------
        str
           Mesh representation string


        Example
        -------
        Getting mesh representation string.

        >>> import discretisedfield as df
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> repr(mesh)
        'Mesh(p1=(0, 0, 0), p2=(2, 2, 1), cell=(1, 1, 1), name="mesh")'

        """
        return ("Mesh(p1={}, p2={}, cell={}, "
                "name=\"{}\")").format(self.p1, self.p2, self.cell, self.name)

    def _ipython_display_(self):
        """Figure of mesh domain and discretisation cell."""
        return self.plot()  # pragma: no cover

    def random_point(self):
        """Generate the random point coordinates inside the mesh.

        Returns
        -------
        tuple (3,)
            Coordinates of a random point inside the mesh `p` = (`x`, `y`, `z`).

        Example
        -------
        Getting mesh representation string.

        >>> import discretisedfield as df
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.random_point()  # doctest: +ELLIPSIS
        (...)

        .. note::

           In the example, ellipsis is used instead of a tuple because
           the result differs each time the random_point command
           command is run.

        """
        return tuple(self.pmin[i]+random.random()*self.l[i] for i in range(3))

    def index2point(self, index):
        """Convert the cell index to its centre point coordinate.

        The finite difference domain is disretised in x, y, and z directions
        in dx, dy, and dz steps, respectively. Consequently, there are
        nx, ny, and nz discretisation steps. This method converts the cell
        index (ix, iy, iz) to the cell's centre point coordinate.

        This method raises ValueError if the index is out of range.

        Args:
          i (tuple): A length 3 tuple of integers (ix, iy, iz)

        Returns:
          A length 3 tuple of x, y, and z coodinates

        """
        # Does index refer to a cell outside the mesh?
        for i in range(3):
            if index[i] < 0 or index[i] > self.n[i] - 1:
                msg = ("index[{}]={} out of range "
                       "[0, n[{}]].").format(i, index[i], self.n[i])
                raise ValueError(msg)

        return tuple(self.pmin[i]+(index[i]+0.5)*self.cell[i]
                     for i in range(3))

    def point2index(self, p):
        """Compute the index of a cell containing point `p`.

        Parameters
        ----------
        p : (3,) array_like
            Point `p` = (`px`, `py`, `pz`) in the mesh domain.

        Returns
        -------
        tuple (3,)
            Mesh cell indices (`ix`, `iy`, `iz`).
        
        Raises
        ------
        ValueError
            If the point `p` is outside the mesh.

        Example
        -------
        Getting mesh representation string.

        >>> import discretisedfield as df
        >>> p1 = (0, 0, 0)
        >>> p2 = (2, 2, 1)
        >>> cell = (1, 1, 1)
        >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        >>> mesh.point2index((0.5, 0.1, 0))  # doctest: +ELLIPSIS
        (...)

        """
        # Is the point outside the mesh?
        for i in range(3):
            if p[i] < self.pmin[i] or p[i] > self.pmax[i]:
                msg = "Point p[{}]={} outside the mesh.".format(i, p[i])
                raise ValueError(msg)

        index = tuple(int(round((p[i]-self.pmin[i])/self.cell[i] - 0.5))
                      for i in range(3))

        # If rounded to the out-of-range values
        return tuple(max(min(self.n[i]-1, index[i]), 0) for i in range(3))

    def plot(self):
        """Creates a figure of a mesh domain and discretisation cell."""
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.set_aspect("equal")

        # domain box
        dfu.plot_box(ax, self.pmin, self.pmax, "b-", linewidth=1.5)

        # cell box
        cell_point = tuple(self.pmin[i]+self.cell[i] for i in range(3))
        dfu.plot_box(ax, self.pmin, cell_point, "r-", linewidth=1)

        ax.set(xlabel=r"$x$", ylabel=r"$y$", zlabel=r"$z$")
        plt.close()

        return fig

    def line_intersection(self, l, l0, n=100):
        """Generator yielding mesh cell indices and their centre coordinates,
        along the line defined with l and l0 in n points."""
        try:
            p1, p2 = dfu.box_line_intersection(self.pmin, self.pmax, l, l0)
        except TypeError:
            raise ValueError("Line does not intersect mesh in two points.")

        p1, p2 = np.array(p1), np.array(p2)
        dl = (p2-p1) / (n-1)
        for i in range(n):
            point = p1 + i*dl
            yield np.linalg.norm(i*dl), tuple(point)

    @property
    def _script(self):
        """This abstract method should be implemented by a specific
        calculator.

        Raises
        ------
        NotImplementedError
            If not implemented by a specific calculator.

        """
        raise NotImplementedError
