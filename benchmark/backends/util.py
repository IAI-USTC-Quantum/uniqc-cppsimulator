"""Small numeric helpers shared by backend adapters."""

from __future__ import annotations

import math

import numpy as np


def prob_q0_1_from_statevector(vec, q0_is_lsb: bool = True) -> float:
    """P(measure qubit 0 -> 1) from a flat statevector of length 2^n.

    ``q0_is_lsb`` says whether qubit 0 is the least-significant bit of the
    flat amplitude index (the usual little-endian convention).
    """
    vec = np.asarray(vec)
    n = round(math.log2(vec.shape[0]))
    probs = np.abs(vec.reshape((2,) * n)) ** 2
    axis = n - 1 if q0_is_lsb else 0
    others = tuple(i for i in range(n) if i != axis)
    return float(probs.sum(axis=others)[1])


def prob_q0_1_from_diag(mat, q0_is_lsb: bool = True) -> float:
    """P(q0 -> 1) from a density-matrix diag; ordering flag as above."""
    diag = np.abs(np.diag(np.asarray(mat)))
    return prob_q0_1_from_statevector(np.sqrt(diag), q0_is_lsb)
