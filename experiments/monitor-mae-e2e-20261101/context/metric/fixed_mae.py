"""Exact AST source excerpt of reviewed host evaluation._mae. No formula changes."""
import math

def _mae(pairs: list[tuple[float, float]]) -> float:
    errors = [abs(truth - prediction) for truth, prediction in pairs]
    if all(math.isfinite(error) for error in errors):
        scale = max(errors)
        return 0.0 if scale == 0.0 else scale * (math.fsum(error / scale for error in errors) / len(errors))
    # Finite operands can overflow on subtraction. Scale first in that case;
    # an unrepresentable final result is rejected by the caller.
    scale = max(abs(value) for pair in pairs for value in pair)
    return scale * (math.fsum(abs(truth / scale - prediction / scale)
                             for truth, prediction in pairs) / len(pairs))
