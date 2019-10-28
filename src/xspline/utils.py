# utility functions for the bsplinex class
import numpy as np


def indicator_f(x, b, l_close=True, r_close=False):
    r"""Indicator function for provided interval.

    Args:
        x (float | np.ndarray):
        Float scalar or numpy array store the variable(s).

        b (np.ndarray):
        1D array with 2 elements represent the left and right end of the
        interval.

        l_close (bool | True, optional):
        Bool variable indicate that if include the left end of the interval.

        r_close (bool | False, optional):
        Bool variable indicate that if include the right end of the interval.

    Returns:
        float | np.ndarray:
        Return function value(s) at ``x``. The result has the same shape with
        ``x``. 0 in the result indicate corresponding element in ``x`` is not in
        the interval and 1 means the it is in the interval.
    """
    if l_close:
        lb = (x >= b[0])
    else:
        lb = (x > b[0])

    if r_close:
        rb = (x <= b[1])
    else:
        rb = (x < b[1])

    if np.isscalar(x):
        return float(lb & rb)
    else:
        return (lb & rb).astype(np.double)


def linear_f(x, z, fz, dfz):
    r"""Linear function construct by a base point and its derivative.

    Args:
        x (float | np.ndarray):
        Float scalar or numpy array store the variable(s).

        z (float | np.ndarray):
        Float scalar or numpy array store the base point(s). When ``x`` is
        ``np.ndarray``, ``z`` has to have the same shape with ``x``.

        fz (float | np.ndarray):
        Float scalar or numpy array store the function value(s) at ``z``. Same
        requirements with ``z``.

        dfz (float | np.ndarray):
        Float scalar or numpy array store the function derivative(s) at ``z``.
        Same requirements with ``z``.

    Returns:
        float | np.ndarray:
        Return function value(s) at ``x`` with linear function constructed at
        base point(s) ``z``. The result has the same shape with ``x`` when
        ``z`` is scalar or same shape with ``z`` when ``x`` is scalar.
    """
    return fz + dfz*(x - z)


def linear_lf(x, b):
    r"""Linear function constructed by linearly interpolate 0 and 1 from left
    end point to right end point.

    Args:
        x (float | np.ndarray):
        Float scalar or numpy array that store the variable(s).

        b (np.ndarray):
        1D array with 2 elements represent the left and right end of the
        interval.

    Returns:
        float | np.ndarray:
        Return function value(s) at ``x``. The result has the same shape with
        ``x``.
    """
    return (x - b[0])/(b[1] - b[0])


def linear_rf(x, b):
    r"""Linear function constructed by linearly interpolate 0 and 1 from right
    end point to left end point.

    Args:
        x (float | np.ndarray):
        Float scalar or numpy array that store the variable(s).

        b (np.ndarray):
        1D array with 2 elements represent the left and right end of the
        interval.

    Returns:
        float | np.ndarray:
        Return function value(s) at ``x``. The result has the same shape with
        ``x``.
    """
    return (x - b[1])/(b[0] - b[1])


def constant_if(a, x, order, c):
    r"""Integration of constant function.

    Args:
        a (float | np.ndarray):
        Starting point(s) of the integration. If both ``a`` and ``x`` are
        ``np.ndarray``, they should have the same shape.

        x (float | np.ndarray):
        Ending point(s) of the integration. If both ``a`` and ``x`` are
        ``np.ndarray``, they should have the same shape.

        order (int):
        Non-negative integer number indicate the order of integration. In other
        words, how many time(s) we integrate.

        c (float):
        Constant function value.

    Returns:
        float | np.ndarray:
        Integration value(s) of the constant function.
    """
    # determine the result size
    a_is_ndarray = isinstance(a, np.ndarray)
    x_is_ndarray = isinstance(x, np.ndarray)

    if a_is_ndarray and x_is_ndarray:
        assert a.size == x.size

    result_is_ndarray = a_is_ndarray or x_is_ndarray
    if a_is_ndarray:
        result_size = a.size
    elif x_is_ndarray:
        result_size = x.size
    else:
        result_size = 1

    # special case when c is 0
    if c == 0.0:
        if result_is_ndarray:
            return np.zeros(result_size)
        else:
            return 0.0

    return c*(x - a)**order/np.math.factorial(order)


def linear_if(a, x, order, z, fz, dfz):
    """integrate the linear function"""
    fa = fz + dfz*(a - z)
    dfa = dfz

    return dfa*(x - a)**(order + 1)/np.math.factorial(order + 1) + \
        fa*(x - a)**order/np.math.factorial(order)


def integrate_across_pieces(a, x, order, funcs, knots):
    """integrate Across piecewise functions"""
    if len(funcs) == 1:
        return funcs[0](a, x, order)
    else:
        assert np.all(a < knots[0]) and np.all(x > knots[-1])

    b = np.repeat(knots[0], a.size)
    val = integrate_across_pieces(b, x, order, funcs[1:], knots[1:])

    for j in range(order):
        val += funcs[0](a, b, order - j)*(x - b)**j / np.math.factorial(j)

    return val


def pieces_if(a, x, order, funcs, knots):
    """integrate different pieces of the functions"""
    # verify the input
    if np.isscalar(a) and not np.isscalar(x):
        a = np.repeat(a, x.size)
    if np.isscalar(x) and not np.isscalar(a):
        x = np.repeat(x, a.size)
    if np.isscalar(a) and np.isscalar(x):
        a = np.array([a])
        x = np.array([x])
        result_is_scalar = True
    else:
        result_is_scalar = False

    assert a.size == x.size
    assert np.all(a <= x)
    assert len(funcs) == len(knots) + 1

    num_knots = len(knots)

    # different cases
    a_ind = [a < knots[0]] +\
            [(a >= knots[i]) & (a < knots[i + 1])
             for i in range(num_knots - 1)] +\
            [a >= knots[-1]]

    x_ind = [x <= knots[0]] +\
            [(x > knots[i]) & (x <= knots[i + 1])
             for i in range(num_knots - 1)] +\
            [x > knots[-1]]

    int_f = np.zeros(a.size)
    for ia in range(len(funcs)):
        for ix in range(ia, len(funcs)):
            case_id = a_ind[ia] & x_ind[ix]
            if np.any(case_id):
                int_f[case_id] = integrate_across_pieces(a[case_id],
                                                         x[case_id],
                                                         order,
                                                         funcs[ia:ix + 1],
                                                         knots[ia:ix])

    if result_is_scalar:
        return int_f[0]
    else:
        return int_f


def indicator_if(a, x, order, b):
    """integrate indicator function to the order of n"""
    return pieces_if(a, x, order,
                     [lambda *params: constant_if(*params, 0.0),
                      lambda *params: constant_if(*params, 1.0),
                      lambda *params: constant_if(*params, 0.0)], b)


def seq_diff_mat(size):
    """sequencial difference matrix"""
    assert isinstance(size, int) and size >= 2

    mat = np.zeros((size - 1, size))
    id_d0 = np.diag_indices(size - 1)
    id_d1 = (id_d0[0], id_d0[1] + 1)

    mat[id_d0] = -1.0
    mat[id_d1] = 1.0

    return mat


def index_list(i, sizes):
    """flat index to index list"""
    assert sizes
    assert i < np.prod(sizes)

    ndim = len(sizes)
    n = np.cumprod(np.insert(sizes[::-1], 0, 1))[-2::-1]

    idxes = []
    for j in range(ndim):
        quotient = i // n[j]
        idxes.append(quotient)
        i -= quotient*n[j]

    return idxes


def option_to_list(opt, size):
    """convert default option to option list"""
    if not opt:
        return [False]*size
    else:
        return [True]*size


def outer_flatten(*arg):
    """outer product of multiple vectors and then flatten the result"""
    ndim = len(arg)
    if ndim == 1:
        return arg[0]

    mat = np.outer(arg[0], arg[1])
    vec = mat.reshape(mat.size,)

    if ndim == 2:
        return vec
    else:
        return outer_flatten(vec, *arg[2:])
