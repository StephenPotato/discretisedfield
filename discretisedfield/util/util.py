import collections
import numpy as np
import itertools as it
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable


axesdict = collections.OrderedDict([("x", 0), ("y", 1), ("z", 2)])


def array2tuple(array):
    return tuple(array.tolist())


def plane_info(*args, **kwargs):
    info = dict()
    # The plane is defined with: planeaxis and point. They should be
    # extracted from *args and *kwargs.
    if args:
        # Only an axis is provided.
        planeaxis = args[0]
        info["point"] = None
    else:
        # Both an axis and the value are provided.
        planeaxis = [key for key in kwargs.keys()
                     if kwargs[key] is not None and key != "args"][0]
        info["point"] = kwargs[planeaxis]

    if planeaxis not in axesdict.keys():
        msg = f"Argument name must be one of {axesdict.keys()}."
        raise ValueError(msg)

    info["slice"] = axesdict[planeaxis]
    axes = tuple(filter(lambda val: val != info["slice"], axesdict.values()))
    info["haxis"], info["vaxis"] = axes

    return info


def as_array(mesh, dim, val):
    val_array = np.empty(mesh.n + (dim,))
    if isinstance(val, (int, float)) and (dim == 1 or val == 0):
        val_array.fill(val)
    elif isinstance(val, (tuple, list, np.ndarray)) and len(val) == dim:
        val_array[..., :] = val
    elif isinstance(val, np.ndarray) and val.shape == val_array.shape:
        val_array = val
    elif callable(val):
        for index, point in zip(mesh.indices, mesh.coordinates):
            val_array[index] = val(point)
    else:
        raise TypeError("Unsupported type(val)={}.".format(type(val)))
    return val_array


def plot_line(ax, p1, p2, *args, **kwargs):
    """Plot a line between points p1 and p2 on axis ax."""
    ax.plot(*zip(p1, p2), *args, **kwargs)


def plot_box(ax, p1, p2, *args, **kwargs):
    """Plots a cube that spans between p1 and p2 on the given axis.

    Args:
      ax (matplolib axis): matplolib axis object
      p1 (tuple, list, np.ndarray): First cube point
        p1 is of length 3 (xmin, ymin, zmax).
      p2 (tuple, list, np.ndarray): Second cube point
        p2 is of length 3 (xmin, ymin, zmax).
      color (str): matplotlib color string
      linewidth (Real): matplotlib linewidth parameter

    """
    x1, y1, z1 = p1
    x2, y2, z2 = p2

    plot_line(ax, (x1, y1, z1), (x2, y1, z1), *args, **kwargs)
    plot_line(ax, (x1, y2, z1), (x2, y2, z1), *args, **kwargs)
    plot_line(ax, (x1, y1, z2), (x2, y1, z2), *args, **kwargs)
    plot_line(ax, (x1, y2, z2), (x2, y2, z2), *args, **kwargs)

    plot_line(ax, (x1, y1, z1), (x1, y2, z1), *args, **kwargs)
    plot_line(ax, (x2, y1, z1), (x2, y2, z1), *args, **kwargs)
    plot_line(ax, (x1, y1, z2), (x1, y2, z2), *args, **kwargs)
    plot_line(ax, (x2, y1, z2), (x2, y2, z2), *args, **kwargs)

    plot_line(ax, (x1, y1, z1), (x1, y1, z2), *args, **kwargs)
    plot_line(ax, (x2, y1, z1), (x2, y1, z2), *args, **kwargs)
    plot_line(ax, (x1, y2, z1), (x1, y2, z2), *args, **kwargs)
    plot_line(ax, (x2, y2, z1), (x2, y2, z2), *args, **kwargs)


def addcolorbar(ax, imax):
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.05)
    cbar = plt.colorbar(imax, cax=cax)
    return ax, cbar
