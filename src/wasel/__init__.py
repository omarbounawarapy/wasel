import os

# The app scores one order at a time: the tiny numpy/scipy/xgboost calls don't benefit from a thread per core,
# and the default pools burn ~6x the CPU for the same result (enough to pin a laptop). Set before numpy loads;
# an explicit env value still wins.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")
