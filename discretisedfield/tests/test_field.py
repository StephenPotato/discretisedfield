import os
import types
import random
import pytest
import itertools
import numpy as np
import discretisedfield as df
import matplotlib.pyplot as plt
import discretisedfield.tests as dft


def check_field(field):
    assert isinstance(field.mesh, df.Mesh)
    assert isinstance(field.dim, int)
    assert isinstance(field.name, str)
    assert isinstance(field.array, np.ndarray)
    assert field.array.shape[-1] == field.dim
    assert isinstance(field.norm.array, np.ndarray)
    assert field.norm.array.shape[-1] == 1


class TestField:
    def setup(self):
        # Create meshes using valid arguments from TestMesh.
        tm = dft.TestMesh()
        tm.setup()
        self.meshes = []
        for p1, p2, n, cell in tm.valid_args:
            mesh = df.Mesh(p1=p1, p2=p2, n=n, cell=cell)
            self.meshes.append(mesh)

        # Create lists of field values.
        self.consts = [0, -5., np.pi, 1e-15, 1.2e12, random.random()]
        self.iters = [(0, 0, 1),
                      (0, -5.1, np.pi),
                      [70, 1e15, 2*np.pi],
                      [5, random.random(), np.pi],
                      np.array([4, -1, 3.7]),
                      np.array([2.1, 0.0, -5*random.random()])]
        self.sfuncs = [lambda c: 1,
                       lambda c: -2.4,
                       lambda c: -6.4e-15,
                       lambda c: c[0] + c[1] + c[2] + 1,
                       lambda c: (c[0]-1)**2 - c[1]+7 + c[2]*0.1,
                       lambda c: np.sin(c[0]) + np.cos(c[1]) - np.sin(2*c[2])]

        self.vfuncs = [lambda c: (1, 2, 0),
                       lambda c: (-2.4, 1e-3, 9),
                       lambda c: (c[0], c[1], c[2] + 100),
                       lambda c: (c[0]+c[2]+10, c[1], c[2]+1),
                       lambda c: (c[0]-1, c[1]+70, c[2]*0.1),
                       lambda c: (np.sin(c[0]), np.cos(c[1]), -np.sin(2*c[2]))]

        # Create a field for plotting
        mesh = df.Mesh(p1=(-5, -5, -5), p2=(5, 5, 5), cell=(1, 1, 1))
        self.pf = df.Field(mesh, dim=3, value=(0, 0, 2))

        def normfun(pos):
            x, y, z = pos
            if x**2 + y**2 <= 5**2:
                return 1
            else:
                return 0

        self.pf.norm = normfun

    def test_init(self):
        p1 = (0, 0, 0)
        p2 = (5, 10, 15)
        cell = (1, 1, 1)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        dim = 2
        name = 'test_field'
        value = [1, 2]
        f = df.Field(mesh, dim=dim, value=value, name=name)

        check_field(f)
        assert f.name == name
        assert f.array.shape == (5, 10, 15, 2)
        assert np.all(f.array[..., 0] == value[0])
        assert np.all(f.array[..., 1] == value[1])
        assert f.norm.array.shape == (5, 10, 15, 1)

    def test_valid_init(self):
        for mesh in self.meshes:
            for value in self.consts:
                f = df.Field(mesh, dim=1, value=value)
                check_field(f)
                assert f.value == value
                assert np.all(f.array == value)
                assert f(f.mesh.random_point()) == value
                assert f(f.mesh.centre) == value
            for value in self.sfuncs:
                f = df.Field(mesh, dim=1, value=value)
                check_field(f)
            for value in self.iters:
                f = df.Field(mesh, dim=3, value=value)
                check_field(f)
                assert np.equal(f.value, value).all()
                assert np.equal(f(f.mesh.random_point()), value).all()
                assert np.equal(f(f.mesh.centre), value).all()
            for value in self.vfuncs:
                f = df.Field(mesh, dim=3, value=value)
                check_field(f)

    def test_invalid_init(self):
        with pytest.raises(TypeError):
            mesh = 'wrong_mesh_string'
            f = df.Field(mesh, dim=1)

        for mesh in self.meshes:
            with pytest.raises(TypeError):
                f = df.Field(mesh, dim='wrong_dim')

    def test_set_with_ndarray(self):
        for mesh in self.meshes:
            f = df.Field(mesh, dim=3)
            value = np.zeros(f.mesh.n + (f.dim,))
            f.value = value

            check_field(f)
            assert isinstance(f.value, np.ndarray)
            assert np.equal(f.array, 0).all()

            with pytest.raises(ValueError) as excinfo:
                f.array = (1, 2, 3)
            assert 'Unsupported' in str(excinfo.value)

    def test_set_with_function(self):
        for mesh in self.meshes:
            for func in self.sfuncs:
                f = df.Field(mesh, dim=1, value=func)
                for j in range(10):
                    c = f.mesh.random_point()
                    c = f.mesh.index2point(f.mesh.point2index(c))
                    assert f(c) == func(c)

        for mesh in self.meshes:
            for func in self.vfuncs:
                f = df.Field(mesh, dim=3, value=func)
                for j in range(10):
                    c = f.mesh.random_point()
                    c = f.mesh.index2point(f.mesh.point2index(c))
                    assert np.all(f(c) == func(c))

    def test_set_with_dict(self):
        p1 = (0, 0, 0)
        p2 = (10e-9, 10e-9, 10e-9)
        n = (5, 5, 5)
        regions = {'r1': df.Region(p1=(0, 0, 0), p2=(5e-9, 10e-9, 10e-9)),
                   'r2': df.Region(p1=(5e-9, 0, 0), p2=(10e-9, 10e-9, 10e-9))}
        mesh = df.Mesh(p1=p1, p2=p2, n=n, regions=regions)

        field = df.Field(mesh, dim=3, value={'r1': (0, 0, 1), 'r2': (0, 0, 2)})
        assert np.all(field((3e-9, 7e-9, 9e-9)) == (0, 0, 1))
        assert np.all(field((8e-9, 2e-9, 9e-9)) == (0, 0, 2))

    def test_set_exception(self):
        for mesh in self.meshes:
            f = df.Field(mesh)
            with pytest.raises(ValueError):
                f.value = 'string'
            with pytest.raises(ValueError):
                f.value = 1+2j

    def test_repr(self):
        for mesh in self.meshes:
            f = df.Field(mesh, dim=1)
            check_field(f)
            rstr = repr(f)
            assert isinstance(rstr, str)
            assert 'mesh=' in rstr
            assert 'dim=1' in rstr
            assert 'name=' in rstr

            f = df.Field(mesh, dim=3)
            check_field(f)
            rstr = repr(f)
            assert isinstance(rstr, str)
            assert 'mesh=' in rstr
            assert 'dim=3' in rstr
            assert 'name=' in rstr

    def test_value_is_not_preserved(self):
        for mesh in self.meshes:
            f = df.Field(mesh, dim=3)
            f.value = (1, 1, 1)

            assert f.value == (1, 1, 1)

            f.array[0, 0, 0, 0] = 3
            assert isinstance(f.value, np.ndarray)

    def test_norm(self):
        mesh = df.Mesh(p1=(0, 0, 0), p2=(10, 10, 10), cell=(1, 1, 1))
        f = df.Field(mesh, dim=3, value=(2, 2, 2))

        assert np.all(f.norm.value == 2*np.sqrt(3))
        assert np.all(f.norm.array == 2*np.sqrt(3))
        assert np.all(f.array == 2)

        f.norm = 1
        assert np.all(f.norm.value == 1)
        assert np.all(f.norm.array == 1)
        assert np.all(f.array == 1/np.sqrt(3))

        f.array[0, 0, 0, 0] = 3
        assert isinstance(f.norm.value, np.ndarray)
        assert not np.all(f.norm.value == 1)

        for mesh in self.meshes:
            for value in self.iters + self.vfuncs:
                for norm_value in [1, 2.1, 50, 1e-3, np.pi]:
                    f = df.Field(mesh, dim=3, value=value, norm=norm_value)

                    # Compute norm.
                    norm = f.array[..., 0]**2
                    norm += f.array[..., 1]**2
                    norm += f.array[..., 2]**2
                    norm = np.sqrt(norm)

                    assert norm.shape == f.mesh.n
                    assert f.norm.array.shape == f.mesh.n + (1,)
                    assert np.all(abs(norm - norm_value) < 1e-12)

    def test_norm_is_not_preserved(self):
        for mesh in self.meshes:
            f = df.Field(mesh, dim=3)
            f.value = (0, 3, 0)
            f.norm = 1
            assert np.all(f.norm.array == 1)

            f.value = (0, 2, 0)
            assert np.all(f.norm.value != 1)
            assert np.all(f.norm.array == 2)

    def test_norm_scalar_field_exception(self):
        for mesh in self.meshes:
            for value in self.consts + self.sfuncs:
                for norm in [1, 2.1, 50, 1e-3, np.pi]:
                    f = df.Field(mesh, dim=1, value=value)
                    with pytest.raises(ValueError):
                        f.norm = norm

    def test_norm_zero_field_exception(self):
        for mesh in self.meshes:
            f = df.Field(mesh, dim=3, value=(0, 0, 0))
            with pytest.raises(ValueError):
                f.norm = 1

    def test_average(self):
        value = -1e-3 + np.pi
        tol = 1e-12
        for mesh in self.meshes:
            f = df.Field(mesh, dim=1, value=value)

            assert isinstance(f.average, tuple)
            assert len(f.average) == 1
            assert abs(f.average[0] - value) < tol

        value = np.array([1.1, -2e-3, np.pi])
        tol = 1e-12
        for mesh in self.meshes:
            f = df.Field(mesh, dim=3, value=value)

            assert isinstance(f.average, tuple)
            assert len(f.average) == 3
            assert np.allclose(f.average, value)

    def test_field_component(self):
        for mesh in self.meshes:
            f = df.Field(mesh, dim=3, value=(1, 2, 3))
            assert isinstance(f.x, df.Field)
            assert f.x.dim == 1
            assert np.all(f.x.array == 1)
            assert isinstance(f.y, df.Field)
            assert f.y.dim == 1
            assert np.all(f.y.array == 2)
            assert isinstance(f.z, df.Field)
            assert f.z.dim == 1
            assert np.all(f.z.array == 3)

            f = df.Field(mesh, dim=2, value=(1, 2))
            assert isinstance(f.x, df.Field)
            assert f.x.dim == 1
            assert np.all(f.x.array == 1)
            assert isinstance(f.y, df.Field)
            assert f.y.dim == 1
            assert np.all(f.y.array == 2)

            f = df.Field(mesh, dim=1, value=1)
            with pytest.raises(AttributeError):
                assert f.x.dim == 1

    def test_get_attribute_exception(self):
        for mesh in self.meshes:
            f = df.Field(mesh)
            with pytest.raises(AttributeError) as excinfo:
                f.__getattr__('nonexisting_attribute')
            assert 'has no attribute' in str(excinfo.value)

    def test_dir(self):
        for mesh in self.meshes:
            f = df.Field(mesh, value=(5, 6, -9))
            assert 'x' in f.__dir__()
            assert 'y' in f.__dir__()
            assert 'z' in f.__dir__()

            f = df.Field(mesh, dim=1, value=1)
            assert 'x' not in f.__dir__()
            assert 'y' not in f.__dir__()
            assert 'z' not in f.__dir__()

    def test_eq_ne(self):
        p1 = (-5e-9, -5e-9, -5e-9)
        p2 = (15e-9, 5e-9, 5e-9)
        cell = (5e-9, 1e-9, 2.5e-9)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        f1 = df.Field(mesh, dim=1, value=0.2)
        f2 = df.Field(mesh, dim=1, value=0.2)
        f3 = df.Field(mesh, dim=1, value=3.1)
        f4 = df.Field(mesh, dim=3, value=(1, -6, 0))
        f5 = df.Field(mesh, dim=3, value=(1, -6, 0))
        assert f1 == f2
        assert not f1 != f2
        assert not f1 == f3
        assert f1 != f3
        assert not f2 == f4
        assert f2 != f4
        assert f4 == f5
        assert not f4 != f5

    def test_neg(self):
        p1 = (-5e-9, -5e-9, -5e-9)
        p2 = (5e-9, 5e-9, 5e-9)
        cell = (1e-9, 1e-9, 1e-9)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # Scalar field
        f = df.Field(mesh, dim=1, value=3)
        res = -f
        check_field(res)
        assert res.average == (-3,)

        # Vector field
        f = df.Field(mesh, dim=3, value=(1, 2, -3))
        res = -f
        check_field(res)
        assert res.average == (-1, -2, 3)

    def test_pow(self):
        p1 = (0, 0, 0)
        p2 = (15e-9, 15e-9, 15e-9)
        cell = (3e-9, 3e-9, 3e-9)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # Scalar field
        f = df.Field(mesh, dim=1, value=2)
        res = f**2
        assert res.average == (4,)
        res = f**(-1)
        assert res.average == (0.5,)

        # Vector field
        f = df.Field(mesh, dim=3, value=(1, 2, -2))
        res = f**2
        assert res.average == (1, 4, 4)
        res = f**(-1)
        assert res.average == (1, 0.5, -0.5)

    def test_add_subtract(self):
        p1 = (0, 0, 0)
        p2 = (5e-9, 10e-9, -5e-9)
        n = (2, 2, 1)
        mesh = df.Mesh(p1=p1, p2=p2, n=n)

        # Scalar fields
        f1 = df.Field(mesh, dim=1, value=1.2)
        f2 = df.Field(mesh, dim=1, value=-0.2)
        res = f1 + f2
        assert res.average == (1,)
        res = f1 - f2
        assert res.average == (1.4,)

        # Vector fields
        f1 = df.Field(mesh, dim=3, value=(1, 2, 3))
        f2 = df.Field(mesh, dim=3, value=(-1, -3, -5))
        res = f1 + f2
        assert res.average == (0, -1, -2)
        res = f1 - f2
        assert res.average == (2, 5, 8)

        # Check if commutative
        assert f1 + f2 == f2 + f1
        assert f1 - f2 == -(f2 - f1)

    def test_mul_rmul(self):
        p1 = (0, 0, 0)
        p2 = (5e-9, 5e-9, 5e-9)
        cell = (1e-9, 5e-9, 1e-9)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # Scalar fields
        f1 = df.Field(mesh, dim=1, value=1.2)
        f2 = df.Field(mesh, dim=1, value=-2)
        res = f1 * f2
        assert res.average == (-2.4,)

        # Scalar field with a scalar
        f1 = df.Field(mesh, dim=1, value=5)
        res = f1 * 2  # __mul__
        assert res.average == (10,)
        res = 3 * f1  # __rmul__
        assert res.average == (15,)

        # Vector fields
        f1 = df.Field(mesh, dim=3, value=(1, 2, -3))
        f2 = df.Field(mesh, dim=3, value=(-1, -3, -5))
        res = f1 * f2
        assert res.average == (-1, -6, 15)

        # Vector field with a scalar
        f1 = df.Field(mesh, dim=3, value=(1, 2e6, 0))
        res = f1 * 2
        assert res.average == (2, 4e6, 0)
        res = 5 * f1
        assert res.average == (5, 10e6, 0)

        # Check if commutative
        assert f1 * f2 == f2 * f1
        assert -5 * f2 == f2 * (-5)

    def test_truediv_rtruediv(self):
        p1 = (0, 0, 0)
        p2 = (5e-9, 5e-9, 10e-9)
        cell = (1e-9, 5e-9, 2e-9)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # Scalar fields
        f1 = df.Field(mesh, dim=1, value=2)
        f2 = df.Field(mesh, dim=1, value=-2)
        res = f1 / f2
        assert res.average == (-1,)

        # Scalar field with a scalar
        f = df.Field(mesh, dim=1, value=5)
        res = f / 2  # __truediv__
        assert res.average == (2.5,)
        res = 10 / f  # __rtruediv__
        assert res.average == (2,)

        # Vector fields
        f1 = df.Field(mesh, dim=3, value=(1, 4, 10))
        f2 = df.Field(mesh, dim=3, value=(-1, 2, -5))
        res = f1 / f2
        assert res.average == (-1, 2, -2)

        # Vector field with a scalar
        f = df.Field(mesh, dim=3, value=(2, 2e6, -4))
        res = f / 2  # __truediv__
        assert res.average == (1, 1e6, -2)
        res = 4e6 / f  # __rturediv__
        assert res.average == (2e6, 2, -1e6)

        # Check if commutative
        assert f1 / f2 != f2 / f1
        assert (f1 / f2) == (f2 / f1)**(-1)

    def test_operators(self):
        p1 = (0, 0, 0)
        p2 = (5e-9, 5e-9, 10e-9)
        n = (2, 2, 1)
        mesh = df.Mesh(p1=p1, p2=p2, n=n)

        f1 = df.Field(mesh, dim=1, value=2)
        f2 = df.Field(mesh, dim=3, value=(-4, 0, 1))
        res = ((f1/2 + f2.x)**2 - 2*f1*3)/(-f2.z) - 2*f2.y + 1/f2.z**2
        assert np.all(res.array == 4)

    def test_derivative(self):
        p1 = (0, 0, 0)
        p2 = (10, 10, 10)
        cell = (2, 2, 2)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # f(x, y, z) = 0 -> grad(f) = (0, 0, 0)
        f = df.Field(mesh, dim=1, value=0)

        check_field(f.derivative('x'))
        assert f.derivative('x').average == (0,)
        assert f.derivative('y').average == (0,)
        assert f.derivative('z').average == (0,)

        # f(x, y, z) = x + y + z -> grad(f) = (1, 1, 1)
        def value_fun(pos):
            x, y, z = pos
            return x + y + z

        f = df.Field(mesh, dim=1, value=value_fun)

        assert f.derivative('x').average == (1,)
        assert f.derivative('y').average == (1,)
        assert f.derivative('z').average == (1,)

        # f(x, y, z) = x*y + y + z -> grad(f) = (y, x+1, 1)
        def value_fun(pos):
            x, y, z = pos
            return x*y + y + z

        f = df.Field(mesh, dim=1, value=value_fun)

        assert f.derivative(0)((3, 1, 3)) == (1,)
        assert f.derivative(1)((3, 1, 3)) == (4,)
        assert f.derivative(2)((3, 1, 3)) == (1,)
        assert f.derivative(0)((5, 3, 5)) == (3,)
        assert f.derivative(1)((5, 3, 5)) == (6,)
        assert f.derivative(2)((5, 3, 5)) == (1,)

        # f(x, y, z) = x*y + 2*y + x*y*z ->
        # grad(f) = (y+y*z, x+2+x*z, x*y)
        def value_fun(pos):
            x, y, z = pos
            return x*y + 2*y + x*y*z

        f = df.Field(mesh, dim=1, value=value_fun)

        assert f.derivative('x')((7, 5, 1)) == (10,)
        assert f.derivative('y')((7, 5, 1)) == (16,)
        assert f.derivative('z')((7, 5, 1)) == (35,)

        # f(x, y, z) = (0, 0, 0)
        # -> dfdx = (0, 0, 0)
        # -> dfdy = (0, 0, 0)
        # -> dfdz = (0, 0, 0)
        f = df.Field(mesh, dim=3, value=(0, 0, 0))

        check_field(f.derivative('y'))
        assert f.derivative('x').average == (0, 0, 0)
        assert f.derivative('y').average == (0, 0, 0)
        assert f.derivative('z').average == (0, 0, 0)

        # f(x, y, z) = (x,  y,  z)
        # -> dfdx = (1, 0, 0)
        # -> dfdy = (0, 1, 0)
        # -> dfdz = (0, 0, 1)
        def value_fun(pos):
            x, y, z = pos
            return (x, y, z)

        f = df.Field(mesh, dim=3, value=value_fun)

        assert f.derivative('x').average == (1, 0, 0)
        assert f.derivative('y').average == (0, 1, 0)
        assert f.derivative('z').average == (0, 0, 1)

        # f(x, y, z) = (x*y, y*z, x*y*z)
        # -> dfdx = (y, 0, y*z)
        # -> dfdy = (x, z, x*z)
        # -> dfdz = (0, y, x*y)
        def value_fun(pos):
            x, y, z = pos
            return (x*y, y*z, x*y*z)

        f = df.Field(mesh, dim=3, value=value_fun)

        assert f.derivative(0)((3, 1, 3)) == (1, 0, 3)
        assert f.derivative(1)((3, 1, 3)) == (3, 3, 9)
        assert f.derivative(2)((3, 1, 3)) == (0, 1, 3)
        assert f.derivative(0)((5, 3, 5)) == (3, 0, 15)
        assert f.derivative(1)((5, 3, 5)) == (5, 5, 25)
        assert f.derivative(2)((5, 3, 5)) == (0, 3, 15)

        # f(x, y, z) = (3+x*y, x-2*y, x*y*z)
        # -> dfdx = (y, 1, y*z)
        # -> dfdy = (x, -2, x*z)
        # -> dfdz = (0, 0, x*y)
        def value_fun(pos):
            x, y, z = pos
            return (3+x*y, x-2*y, x*y*z)

        f = df.Field(mesh, dim=3, value=value_fun)

        assert f.derivative('x')((7, 5, 1)) == (5, 1, 5)
        assert f.derivative('y')((7, 5, 1)) == (7, -2, 7)
        assert f.derivative('z')((7, 5, 1)) == (0, 0, 35)

    def test_derivative_single_cell(self):
        p1 = (0, 0, 0)
        p2 = (10, 10, 2)
        cell = (2, 2, 2)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # Scalar field: f(x, y, z) = x + y + z
        # -> grad(f) = (1, 1, 1)
        def value_fun(pos):
            x, y, z = pos
            return x + y + z

        f = df.Field(mesh, dim=1, value=value_fun)

        # only one cell in the z-direction
        assert f.plane('x').derivative('x').average == (0,)
        assert f.plane('y').derivative('y').average == (0,)
        assert f.derivative('z').average == (0,)

        # Vector field: f(x, y, z) = (x, y, z)
        # -> grad(f) = (1, 1, 1)
        def value_fun(pos):
            x, y, z = pos
            return (x, y, z)

        f = df.Field(mesh, dim=3, value=value_fun)

        # only one cell in the z-direction
        assert f.plane('x').derivative('x').average == (0, 0, 0)
        assert f.plane('y').derivative('y').average == (0, 0, 0)
        assert f.derivative('z').average == (0, 0, 0)

    def test_grad(self):
        p1 = (0, 0, 0)
        p2 = (10, 10, 10)
        cell = (2, 2, 2)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # f(x, y, z) = 0 -> grad(f) = (0, 0, 0)
        f = df.Field(mesh, dim=1, value=0)

        check_field(f.grad)
        assert f.grad.average == (0, 0, 0)

        # f(x, y, z) = x + y + z -> grad(f) = (1, 1, 1)
        def value_fun(pos):
            x, y, z = pos
            return x + y + z

        f = df.Field(mesh, dim=1, value=value_fun)

        assert f.grad.average == (1, 1, 1)

        # f(x, y, z) = x*y + y + z -> grad(f) = (y, x+1, 1)
        def value_fun(pos):
            x, y, z = pos
            return x*y + y + z

        f = df.Field(mesh, dim=1, value=value_fun)

        assert f.grad((3, 1, 3)) == (1, 4, 1)
        assert f.grad((5, 3, 5)) == (3, 6, 1)

        # f(x, y, z) = x*y + 2*y + x*y*z ->
        # grad(f) = (y+y*z, x+2+x*z, x*y)
        def value_fun(pos):
            x, y, z = pos
            return x*y + 2*y + x*y*z

        f = df.Field(mesh, dim=1, value=value_fun)

        assert f.grad((7, 5, 1)) == (10, 16, 35)
        assert f.grad.x == f.derivative('x')
        assert f.grad.y == f.derivative('y')
        assert f.grad.z == f.derivative('z')

    def test_div_curl(self):
        p1 = (0, 0, 0)
        p2 = (10, 10, 10)
        cell = (2, 2, 2)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # f(x, y, z) = (0, 0, 0)
        # -> div(f) = 0
        # -> curl(f) = (0, 0, 0)
        f = df.Field(mesh, dim=3, value=(0, 0, 0))

        check_field(f.div)
        assert f.div.dim == 1
        assert f.div.average == (0,)

        check_field(f.curl)
        assert f.curl.dim == 3
        assert f.curl.average == (0, 0, 0)

        # f(x, y, z) = (x, y, z)
        # -> div(f) = 3
        # -> curl(f) = (0, 0, 0)
        def value_fun(pos):
            x, y, z = pos
            return (x, y, z)

        f = df.Field(mesh, dim=3, value=value_fun)

        assert f.div.average == (3,)
        assert f.curl.average == (0, 0, 0)

        # f(x, y, z) = (x*y, y*z, x*y*z)
        # -> div(f) = y + z + x*y
        # -> curl(f) = (x*z-y, -y*z, -x)
        def value_fun(pos):
            x, y, z = pos
            return (x*y, y*z, x*y*z)

        f = df.Field(mesh, dim=3, value=value_fun)

        assert f.div((3, 1, 3)) == 7
        assert f.div((5, 3, 5)) == 23

        assert f.curl((3, 1, 3)) == (8, -3, -3)
        assert f.curl((5, 3, 5)) == (22, -15, -5)

        # f(x, y, z) = (3+x*y, x-2*y, x*y*z)
        # -> div(f) = y - 2 + x*y
        # -> curl(f) = (x*z, -y*z, 1-x)
        def value_fun(pos):
            x, y, z = pos
            return (3+x*y, x-2*y, x*y*z)

        f = df.Field(mesh, dim=3, value=value_fun)

        assert f.div((7, 5, 1)) == 38
        assert f.curl((7, 5, 1)) == (7, -5, -6)

    def test_integral(self):
        p1 = (0, 0, 0)
        p2 = (10, 10, 10)
        cell = (1, 1, 1)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        f = df.Field(mesh, dim=1, value=0)
        assert f.integral == (0,)

        f = df.Field(mesh, dim=1, value=2)
        assert f.integral == (2000,)

        f = df.Field(mesh, dim=3, value=(-1, 0, 3))
        assert f.integral == (-1000, 0, 3000)

        def value_fun(pos):
            x, y, z = pos
            if x <= 5:
                return (-1, -2, -3)
            else:
                return (1, 2, 3)

        f = df.Field(mesh, dim=3, value=value_fun)
        assert f.integral == (0, 0, 0)

    def test_topological_charge(self):
        p1 = (0, 0, 0)
        p2 = (10, 10, 10)
        cell = (2, 2, 2)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # f(x, y, z) = (0, 0, 0)
        # -> Q(f) = 0
        f = df.Field(mesh, dim=3, value=(0, 0, 0))

        q = f.plane('z').topological_charge_density
        check_field(q)
        assert q.dim == 1
        assert q.average == (0,)
        assert f.plane('z').topological_charge == 0

        # f(x, y, z) = (x, y, z)
        # -> Q(f) != 0
        def value_fun(pos):
            x, y, z = pos
            return (x, y, z)

        f = df.Field(mesh, dim=3, value=value_fun)

        q = f.plane('z').topological_charge_density
        assert q.dim == 1
        assert q.average != (0,)
        assert f.plane('z').topological_charge != 0

    def test_bergluescher(self):
        p1 = (0, 0, 0)
        p2 = (10, 10, 10)
        cell = (2, 2, 2)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)

        # f(x, y, z) = (0, 0, 0)
        # -> Q(f) = 0
        f = df.Field(mesh, dim=3, value=(0, 0, 0))

        assert f.plane('z').bergluescher == 0

        # f(x, y, z) = (x, y, z)
        # -> Q(f) != 0
        def value_fun(pos):
            x, y, z = pos
            return (x, y, z)

        f = df.Field(mesh, dim=3, value=value_fun, norm=1)
        
        assert f.plane('z').bergluescher != 0
        #assert f.plane('z').bergluescher == f.plane('z').topological_charge

    def test_line(self):
        mesh = df.Mesh(p1=(0, 0, 0), p2=(10, 10, 10), n=(10, 10, 10))
        f = df.Field(mesh, value=(1, 2, 3))

        line = f.line(p1=(0, 0, 0), p2=(5, 5, 5), n=20)
        assert isinstance(line, types.GeneratorType)
        p, v = zip(*list(line))

        assert len(p) == 20
        assert len(v) == 20
        assert p[0] == (0, 0, 0)
        assert p[-1] == (5, 5, 5)
        assert v[0] == (1, 2, 3)
        assert v[-1] == (1, 2, 3)

    def test_plane(self):
        for mesh in self.meshes:
            f = df.Field(mesh, dim=1, value=3)
            plane = f.plane('x', n=(3, 3))
            assert isinstance(plane, df.Field)

            p, v = zip(*list(plane))
            assert len(p) == 9
            assert len(v) == 9

    def test_writevtk(self):
        vtkfilename = 'test_file.ovf'
        mesh = df.Mesh(p1=(0, 0, 0), p2=(10, 12, 13), cell=(1, 1, 1))
        f = df.Field(mesh, dim=3, value=(1, 2, -5))
        f.write(vtkfilename)
        os.remove(vtkfilename)

    def test_write_wrong_file(self):
        wrongfilename = 'test_file.jpg'
        mesh = df.Mesh(p1=(0, 0, 0), p2=(10, 12, 13), cell=(1, 1, 1))
        f = df.Field(mesh, dim=3, value=(1, 2, -5))
        with pytest.raises(ValueError) as excinfo:
            f.write(wrongfilename)
        assert 'Allowed extensions' in str(excinfo.value)

    def test_wrong_dim_field(self):
        ovffilename = 'test_file.ovf'
        mesh = df.Mesh(p1=(0, 0, 0), p2=(10, 12, 13), cell=(1, 1, 1))
        f = df.Field(mesh, dim=2, value=(1, 2))
        with pytest.raises(TypeError) as excinfo:
            f.write(ovffilename)
        assert 'Cannot write' in str(excinfo.value)

    def test_write_extend_scalar(self):
        ovffilename = 'test_file.omf'
        mesh = df.Mesh(p1=(0, 0, 0), p2=(10, 12, 13), cell=(1, 1, 1))
        f = df.Field(mesh, dim=1, value=1)
        f.write(ovffilename, extend_scalar=True)

    def test_writeovf(self):
        representations = ['txt', 'bin4', 'bin8']
        tolerance = {'txt': 0, 'bin4': 1e-6, 'bin8': 1e-12}
        filename = 'test_file.ovf'
        mesh = df.Mesh(p1=(0, 0, 0), p2=(10, 12, 13), cell=(1, 1, 1))

        for dim, value in [(1, -1.23), (3, (1e-3 + np.pi, -5, 6))]:
            f_out = df.Field(mesh, dim=dim, value=value)
            for rep in representations:
                f_out.write(filename, representation=rep)
                f_in = df.Field.fromfile(filename)
                assert mesh.p1 == f_in.mesh.p1
                assert mesh.p2 == f_in.mesh.p2
                assert mesh.cell == f_in.mesh.cell
                np.testing.assert_allclose(f_out.array, f_in.array,
                                           rtol=tolerance[rep])

        os.remove(filename)

    def test_read_mumax3_ovffile(self):
        """Test reading a file created by mumax, with 4-byte binary data."""
        # Output file has been produced with Mumax ~3.1.0
        # (fd3a50233f0a6625086d390) using this script:
        #
        # SetGridsize(128, 32, 1)
        # SetCellsize(500e-9/128, 125e-9/32, 3e-9)
        #
        # Msat  = 800e3
        # Aex   = 13e-12
        # alpha = 0.02
        #
        # m = uniform(1, .1, 0)
        # save(m)

        # debug: which folder are we in? (use "py.test -l" to display
        # local variables on fail)
        cwd = os.getcwd()
        # -> tests are run in module base directory, when tests are
        #    run from discretisedfield.test()

        # here is our test-data from mumax3:
        filenames = ["mumax-output-linux.ovf", "mumax-output-win.ovf"]
        test_sample_dirname = os.path.join(os.path.dirname(__file__),
                                           'test_sample/')
        for f in filenames:
            path = os.path.join(test_sample_dirname, f)

            f = df.Field.fromfile(path)

            # comparison with human readable part of file
            assert f.dim == 3
            assert f.mesh.ntotal == 4096
            assert f.mesh.pmin == (0., 0., 0.)
            assert f.mesh.pmax == (5e-07, 1.25e-07, 3e-09)
            assert f.array.shape == (128, 32, 1, 3)

            # comparison with vector field (we know from the script
            # shown above)
            #
            # m vector in mumax (uses 4 bytes)
            m = np.array([1, 0.1, 0], dtype=np.float32)

            # needs to be normalised
            norm = sum(m**2)**0.5
            v = m / norm

            # expect the x-component to be v[0]
            np.alltrue(f.array[:, :, :, 0] == v[0])

            # same for y and z
            np.alltrue(f.array[:, :, :, 1] == v[1])
            np.alltrue(f.array[:, :, :, 2] == v[2])

            # expect each vector to be v
            assert np.max(np.abs(f.array[:, :, :] - m / norm)) == 0.

    def test_mpl(self):
        with pytest.raises(ValueError) as excinfo:
            self.pf.mpl()
        assert 'Only sliced field' in str(excinfo.value)

        self.pf.plane('x', n=(3, 4)).mpl()
        self.pf.z.plane('x', n=(3, 4)).mpl()

    def test_imshow(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        with pytest.raises(ValueError) as excinfo:
            self.pf.imshow(ax=ax)
        assert 'Only sliced field' in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            self.pf.plane('z').imshow(ax=ax)
        assert 'Only scalar' in str(excinfo.value)

        self.pf.x.plane('z', n=(3, 4)).imshow(ax=ax)
        self.pf.x.plane('x', n=(3, 4)).imshow(ax=ax, norm_field=self.pf.norm)

    def test_quiver(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        with pytest.raises(ValueError) as excinfo:
            self.pf.quiver(ax=ax)
        assert 'Only sliced field' in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            self.pf.x.plane('y').quiver(ax=ax)
        assert 'Only three-dimensional' in str(excinfo.value)

        self.pf.plane('x', n=(3, 4)).quiver(ax=ax)
        self.pf.plane('x', n=(3, 4)).quiver(ax=ax, color_field=self.pf.y)

    def test_colorbar(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        coloredplot = self.pf.x.plane('x', n=(3, 4)).imshow(ax=ax)
        self.pf.colorbar(ax=ax, coloredplot=coloredplot)

    def test_k3d_nonzero(self):
        with pytest.raises(ValueError) as excinfo:
            self.pf.k3d_nonzero()
        assert 'Only scalar' in str(excinfo.value)

        self.pf.norm.k3d_nonzero()

    def test_k3d_voxels(self):
        with pytest.raises(ValueError) as excinfo:
            self.pf.k3d_voxels()
        assert 'Only scalar' in str(excinfo.value)

        self.pf.x.k3d_voxels()
        self.pf.x.k3d_voxels(norm_field=self.pf.norm)

    def test_k3d_vectors(self):
        with pytest.raises(ValueError) as excinfo:
            self.pf.x.k3d_vectors()
        assert 'Only three-dimensional' in str(excinfo.value)

        self.pf.k3d_vectors()
        self.pf.k3d_vectors(color_field=self.pf.z)
        self.pf.k3d_vectors(points=False)

    def test_k3d_nanosized_sample(self):
        p1 = (0, 0, 0)
        p2 = (50e-9, 50e-9, 50e-9)
        cell = (2e-9, 2e-9, 2e-9)
        mesh = df.Mesh(p1=p1, p2=p2, cell=cell)
        Ms = 1e6
        value = (Ms, Ms, Ms)
        field = df.Field(mesh, dim=3, value=value)

        field.norm.k3d_nonzero()
        field.x.k3d_voxels()
        field.k3d_vectors()
