from __future__ import annotations
import numpy as np

def make_scalar_field(shape=(40,40,20), hot_spots=None, cold_spots=None, wall_mask=None):
    """Return scalar 'cost' field. Lower is better."""
    Z = np.zeros(shape, dtype=float)
    if hot_spots:
        for (x,y,z),amp,sigma in hot_spots:
            gx,gy,gz = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), np.arange(shape[2]), indexing='ij')
            Z += amp*np.exp(-(((gx-x)**2+(gy-y)**2+(gz-z)**2)/(2*sigma**2)))
    if cold_spots:
        for (x,y,z),amp,sigma in cold_spots:
            gx,gy,gz = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), np.arange(shape[2]), indexing='ij')
            Z -= amp*np.exp(-(((gx-x)**2+(gy-y)**2+(gz-z)**2)/(2*sigma**2)))
    if wall_mask is not None:
        Z[wall_mask>0] = np.inf  # hard obstacles
    return Z

def grad(field: np.ndarray):
    """Central gradient (∇field) for descent-like penalties."""
    return np.stack(np.gradient(field))
