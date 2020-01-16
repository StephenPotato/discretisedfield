import numpy as np
import discretisedfield as df
import discretisedfield.util as dfu


def dot(f1, f2):
    """Dot product.

    This function computes the dot product between two fields. Both
    fields must be three-dimensional and defined on the same mesh. If
    any of the fields is not of dimension 3, `ValueError` is raised.

    Parameters
    ----------
    f1, f2 : discretisedfield.Field
        Three-dimensional fields

    Returns
    -------
    discretisedfield.Field

    Raises
    ------
    ValueError
        If the dimension of any of the fields is not 3.

    Example
    -------
    1. Compute the dot product of two vector fields.

    >>> import discretisedfield as df
    ...
    >>> p1 = (0, 0, 0)
    >>> p2 = (10, 10, 10)
    >>> cell = (2, 2, 2)
    >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
    ...
    >>> f1 = df.Field(mesh, dim=3, value=(1, 3, 6))
    >>> f2 = df.Field(mesh, dim=3, value=(-1, -2, 2))
    >>> df.dot(f1, f2).average
    (5.0,)

    """
    if f1.dim != 3 or f2.dim != 3:
        msg = ('Dot product can be calculated only '
               'on three-dimensional fields.')
        raise ValueError(msg)
    if dfu.compatible(f1, f2):
        res_array = np.einsum('ijkl,ijkl->ijk', f1.array, f2.array)
        return df.Field(f1.mesh, dim=1, value=res_array[..., np.newaxis])


def cross(f1, f2):
    """Cross product.

    This function computes the cross product between two fields. Both
    fields must be three-dimensional and defined on the same mesh. If
    any of the fields is not of dimension 3, `ValueError` is raised.

    Parameters
    ----------
    f1, f2 : discretisedfield.Field
        Three-dimensional fields

    Returns
    -------
    discretisedfield.Field

    Raises
    ------
    ValueError
        If the dimension of any of the fields is not 3.

    Example
    -------
    1. Compute the cross product of two vector fields.

    >>> import discretisedfield as df
    ...
    >>> p1 = (0, 0, 0)
    >>> p2 = (10, 10, 10)
    >>> cell = (2, 2, 2)
    >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
    ...
    >>> f1 = df.Field(mesh, dim=3, value=(1, 0, 0))
    >>> f2 = df.Field(mesh, dim=3, value=(0, 1, 0))
    >>> df.cross(f1, f2).average
    (0.0, 0.0, 1.0)

    """
    if f1.dim != 3 or f2.dim != 3:
        msg = ('Cross product can be calculated only '
               'on three-dimensional fields.')
        raise ValueError(msg)
    if dfu.compatible(f1, f2):
        res_array = np.cross(f1.array, f2.array)
        return df.Field(f1.mesh, dim=3, value=res_array)


def stack(fields):
    """Stacking multiple scalar fields into a single vector field.

    This method takes a list of scalar (dim=1) fields and returns a
    vector field, whose components are defined by the scalar fields
    passed. If any of the fields passed is not of dimension 1 or they
    are not defined on the same mesh, an exception will be raised. The
    dimension of the resulting field with be equal to the length of
    the passed list.

    Returns
    -------
    disrectisedfield.Field

    Raises
    ------
    ValueError
        If the dimension of any of the fields is not 1, or the fields
        passed are not defined on the same mesh.

    Example
    -------
    1. Stack 3 scalar fields.

    >>> import discretisedfield as df
    ...
    >>> p1 = (0, 0, 0)
    >>> p2 = (10, 10, 10)
    >>> cell = (2, 2, 2)
    >>> mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
    ...
    >>> f1 = df.Field(mesh, dim=1, value=1)
    >>> f2 = df.Field(mesh, dim=1, value=5)
    >>> f3 = df.Field(mesh, dim=1, value=-3)
    ...
    >>> f = df.stack([f1, f2, f3])
    >>> f.dim
    3
    >>> f.x == f1
    True
    >>> f.y == f2
    True
    >>> f.z == f3
    True

    """
    array_list = []
    for f in fields:
        if f.dim != 1:
            msg = 'Only scalar (dim=1) fields can be stacked.'
            raise ValueError(msg)
        # An exception will be raised if any of the fields is not
        # compatible with the first one in the list.
        if dfu.compatible(fields[0], f):
            array_list.append(f.array[..., 0])

    return df.Field(fields[0].mesh, dim=len(fields),
                    value=np.stack(array_list, axis=3))