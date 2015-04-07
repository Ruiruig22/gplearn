"""Testing the Genetic Programming module's underlying datastructure
(gplearn.genetic._Program)."""

# Author: Trevor Stephens <trevorstephens.com>
#
# License: BSD 3 clause

import numpy as np
import os
import warnings
import sys

from gplearn.genetic import _Program

from sklearn.externals.six.moves import StringIO
from sklearn.datasets import load_boston

from gplearn.skutils.testing import assert_false, assert_true
from gplearn.skutils.testing import assert_greater
from gplearn.skutils.testing import assert_equal, assert_array_almost_equal
from gplearn.skutils.testing import assert_raises
from gplearn.skutils.validation import check_random_state

# load the boston dataset and randomly permute it
rng = check_random_state(0)
boston = load_boston()
perm = rng.permutation(boston.target.size)
boston.data = boston.data[perm]
boston.target = boston.target[perm]


def test_program_init_method():
    """'full' should create longer and deeper programs than other methods"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2',
                               'sqrt1', 'log1', 'abs1', 'max2', 'min2'],
              'arities': {1: ['sqrt1', 'log1', 'abs1'],
                          2: ['add2', 'sub2', 'mul2', 'div2', 'max2', 'min2']},
              'init_depth': (2, 6),
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)
    programs = []
    for i in range(20):
        programs.append(_Program(init_method='full',
                                 random_state=random_state, **params))
    full_length = np.mean([gp.length_ for gp in programs])
    full_depth = np.mean([gp.depth_ for gp in programs])
    programs = []
    for i in range(20):
        programs.append(_Program(init_method='half and half',
                                 random_state=random_state, **params))
    hnh_length = np.mean([gp.length_ for gp in programs])
    hnh_depth = np.mean([gp.depth_ for gp in programs])
    programs = []
    for i in range(20):
        programs.append(_Program(init_method='grow',
                                 random_state=random_state, **params))
    grow_length = np.mean([gp.length_ for gp in programs])
    grow_depth = np.mean([gp.depth_ for gp in programs])

    assert_greater(full_length, hnh_length)
    assert_greater(hnh_length, grow_length)
    assert_greater(full_depth, hnh_depth)
    assert_greater(hnh_depth, grow_depth)


def test_program_init_depth():
    """'full' should create constant depth programs for single depth limit"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2',
                               'sqrt1', 'log1', 'abs1', 'max2', 'min2'],
              'arities': {1: ['sqrt1', 'log1', 'abs1'],
                          2: ['add2', 'sub2', 'mul2', 'div2', 'max2', 'min2']},
              'init_depth': (6, 6),
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)
    programs = []
    for i in range(20):
        programs.append(_Program(init_method='full',
                                 random_state=random_state, **params))
    full_depth = np.bincount([gp.depth_ for gp in programs])
    programs = []
    for i in range(20):
        programs.append(_Program(init_method='half and half',
                                 random_state=random_state, **params))
    hnh_depth = np.bincount([gp.depth_ for gp in programs])
    programs = []
    for i in range(20):
        programs.append(_Program(init_method='grow',
                                 random_state=random_state, **params))
    grow_depth = np.bincount([gp.depth_ for gp in programs])

    assert_true(full_depth[-1] == 20)
    assert_false(hnh_depth[-1] == 20)
    assert_false(grow_depth[-1] == 20)


def test_validate_program():
    """Check that valid programs are accepted & invalid ones raise error"""

    function_set = ['add2', 'sub2', 'mul2', 'div2',
                    'sqrt1', 'log1', 'abs1', 'max2', 'min2']
    arities = {1: ['sqrt1', 'log1', 'abs1'],
               2: ['add2', 'sub2', 'mul2', 'div2', 'max2', 'min2']}
    init_depth = (2, 6)
    init_method = 'half and half'
    n_features = 10
    const_range = (-1.0, 1.0)
    metric = 'mean absolute error'
    p_point_replace = 0.05
    parsimony_coefficient = 0.1

    random_state = check_random_state(415)
    test_gp = ['sub2', 'abs1', 'sqrt1', 'log1', 'log1', 'sqrt1', 7, 'abs1',
               'abs1', 'abs1', 'log1', 'sqrt1', 2]

    # This one should be fine
    _ = _Program(function_set, arities, init_depth, init_method, n_features,
                 const_range, metric, p_point_replace, parsimony_coefficient,
                 random_state, test_gp)

    # Now try a couple that shouldn't be
    assert_raises(ValueError, _Program, function_set, arities, init_depth,
                  init_method, n_features, const_range, metric,
                  p_point_replace, parsimony_coefficient, random_state,
                  test_gp[:-1])
    assert_raises(ValueError, _Program, function_set, arities, init_depth,
                  init_method, n_features, const_range, metric,
                  p_point_replace, parsimony_coefficient, random_state,
                  test_gp + [1])


def test_print_overloading():
    """Check that printing a program object results in 'pretty' output"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2'],
              'arities': {2: ['add2', 'sub2', 'mul2', 'div2']},
              'init_depth': (2, 6),
              'init_method': 'half and half',
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)

    test_gp = ['mul2', 'div2', 8, 1, 'sub2', 9, .5]

    gp = _Program(random_state=random_state, program=test_gp, **params)

    orig_stdout = sys.stdout
    try:
        out = StringIO()
        sys.stdout = out
        print(gp)
        output = out.getvalue().strip()
    finally:
        sys.stdout = orig_stdout

    print(gp)
    lisp = "mul(div(X8, X1), sub(X9, 0.500))"
    assert_true(output == lisp)


def test_export_graphviz():
    """Check output of a simple program to Graphviz"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2'],
              'arities': {2: ['add2', 'sub2', 'mul2', 'div2']},
              'init_depth': (2, 6),
              'init_method': 'half and half',
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)

    # Test for a small program
    test_gp = ['mul2', 'div2', 8, 1, 'sub2', 9, .5]
    gp = _Program(random_state=random_state, program=test_gp, **params)
    output = gp.export_graphviz()
    tree = 'digraph program {\n' \
           'node [style=filled]0 [label="mul", fillcolor="#3499cd"] ;\n' \
           '1 [label="div", fillcolor="#3499cd"] ;\n' \
           '2 [label="X8", fillcolor="#f89939"] ;\n' \
           '3 [label="X1", fillcolor="#f89939"] ;\n' \
           '1 -> 3 ;\n1 -> 2 ;\n' \
           '4 [label="sub", fillcolor="#3499cd"] ;\n' \
           '5 [label="X9", fillcolor="#f89939"] ;\n' \
           '6 [label="0.500", fillcolor="#f89939"] ;\n' \
           '4 -> 6 ;\n4 -> 5 ;\n0 -> 4 ;\n0 -> 1 ;\n}'
    assert_true(output == tree)

    # Test a degenerative single-node program
    test_gp = [1]
    gp = _Program(random_state=random_state, program=test_gp, **params)
    output = gp.export_graphviz()
    tree = 'digraph program {\n' \
           'node [style=filled]0 [label="X1", fillcolor="#f89939"] ;\n}'
    assert_true(output == tree)


def test_execute():
    """Check executing the program works"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2'],
              'arities': {2: ['add2', 'sub2', 'mul2', 'div2']},
              'init_depth': (2, 6),
              'init_method': 'half and half',
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)

    # Test for a small program
    test_gp = ['mul2', 'div2', 8, 1, 'sub2', 9, .5]
    X = np.reshape(random_state.uniform(size=50), (5, 10))
    gp = _Program(random_state=random_state, program=test_gp, **params)
    result = gp.execute(X)
    expected = [-0.19656208, 0.78197782, -1.70123845, -0.60175969, -0.01082618]
    assert_array_almost_equal(result, expected)


def test_all_metrics():
    """Check all supported metrics work"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2'],
              'arities': {2: ['add2', 'sub2', 'mul2', 'div2']},
              'init_depth': (2, 6),
              'init_method': 'half and half',
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)

    # Test for a small program
    test_gp = ['mul2', 'div2', 8, 1, 'sub2', 9, .5]
    gp = _Program(random_state=random_state, program=test_gp, **params)
    X = np.reshape(random_state.uniform(size=50), (5, 10))
    y = random_state.uniform(size=5)
    expected = [1.48719809776, 1.82389179833, 1.76013763179, 0.98663772258]
    result = []
    for m in ['mean absolute error', 'mse', 'rmse', 'rmsle']:
        gp.metric = m
        result.append(gp.fitness(X, y))
    assert_array_almost_equal(result, expected)


def test_get_subtree():
    """Check that get subtree does the same thing for self and new programs"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2'],
              'arities': {2: ['add2', 'sub2', 'mul2', 'div2']},
              'init_depth': (2, 6),
              'init_method': 'half and half',
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)

    # Test for a small program
    test_gp = ['mul2', 'div2', 8, 1, 'sub2', 9, .5]
    gp = _Program(random_state=random_state, program=test_gp, **params)

    self_test = gp.get_subtree(check_random_state(0))
    external_test = gp.get_subtree(check_random_state(0), test_gp)

    assert_equal(self_test, external_test)


def test_genetic_operations():
    """Check all genetic operations are stable and don't change programs"""

    params = {'function_set': ['add2', 'sub2', 'mul2', 'div2'],
              'arities': {2: ['add2', 'sub2', 'mul2', 'div2']},
              'init_depth': (2, 6),
              'init_method': 'half and half',
              'n_features': 10,
              'const_range': (-1.0, 1.0),
              'metric': 'mean absolute error',
              'p_point_replace': 0.05,
              'parsimony_coefficient': 0.1}
    random_state = check_random_state(415)

    # Test for a small program
    test_gp = ['mul2', 'div2', 8, 1, 'sub2', 9, .5]
    donor = ['add2', 0.1, 'sub2', 2, 7]

    gp = _Program(random_state=random_state, program=test_gp, **params)

    assert_equal(gp.reproduce(),
                 ['mul2', 'div2', 8, 1, 'sub2', 9, 0.5])
    assert_equal(gp.program, test_gp)
    assert_equal(gp.crossover(donor, random_state)[0],
                 ['sub2', 2, 7])
    assert_equal(gp.program, test_gp)
    assert_equal(gp.subtree_mutation(random_state)[0],
                 ['mul2', 'div2', 8, 1, 'sub2', 'sub2', 3, 5, 'add2', 6, 3])
    assert_equal(gp.program, test_gp)
    assert_equal(gp.hoist_mutation(random_state)[0],
                 ['div2', 8, 1])
    assert_equal(gp.program, test_gp)
    assert_equal(gp.point_mutation(random_state)[0],
                 ['mul2', 'div2', 8, 1, 'sub2', 9, 0.5])
    assert_equal(gp.program, test_gp)


if __name__ == "__main__":
    import nose
    nose.runmodule()
