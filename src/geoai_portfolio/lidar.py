"""Observed point evidence and explicitly generated exploratory catenaries."""

import numpy as np
from scipy.optimize import least_squares


def coordinates(las):
    return np.column_stack([np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)])


def fit_catenary(points):
    """Fit one already-selected conductor segment; preserve input rows unchanged.

    A PCA horizontal axis defines along-track distance. Bounded robust fitting
    estimates z = a * (cosh((s-s0)/a)-1) + z0. This is not a tension estimate.
    """
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < 20:
        raise ValueError("At least 20 XYZ observations are required")
    if not np.isfinite(points).all():
        raise ValueError("Nonfinite observations")
    origin = points[:, :2].mean(0)
    _, _, axes = np.linalg.svd(points[:, :2] - origin, full_matrices=False)
    axis = axes[0]
    if axis[1] < 0:
        axis *= -1
    s = (points[:, :2] - origin) @ axis
    length = np.ptp(s)
    if length < 20:
        raise ValueError("Segment is too short for this demonstration")

    def curve(parameters, distances):
        a, s0, z0 = parameters
        return a * (np.cosh((distances - s0) / a) - 1) + z0

    solved = least_squares(
        lambda p: curve(p, s) - points[:, 2],
        x0=[500, 0, np.percentile(points[:, 2], 10)],
        bounds=([max(10, length / 10), -length, -100], [100000, length, 300]),
        loss="soft_l1",
        f_scale=0.25,
    )
    if not solved.success:
        raise ValueError("Catenary optimizer did not converge")
    prediction = curve(solved.x, s)
    along = np.linspace(s.min(), s.max(), 200)
    generated = np.column_stack([origin + along[:, None] * axis, curve(solved.x, along)])
    return {
        "parameters": solved.x,
        "along": s,
        "prediction": prediction,
        "origin": origin,
        "axis": axis,
        "residual": points[:, 2] - prediction,
        "generated": generated,
        "rmse_m": float(np.sqrt(np.mean((points[:, 2] - prediction) ** 2))),
        "support_length_m": float(length),
        "success": bool(solved.success),
    }
