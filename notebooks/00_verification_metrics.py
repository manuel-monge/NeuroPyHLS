# %% [markdown]
# # Verification metrics
#
# How NeuroPyHLS decides whether a ported kernel matches its Python reference:
# the maximum absolute error and the signal-to-error ratio (SNR, in dB).

# %%
import numpy as np

from neuropyhls.verify import max_abs_error, snr_db

reference = np.sin(2 * np.pi * 10 * np.linspace(0, 1, 30_000))

# %% [markdown]
# Quantising to Q1.15 fixed point (16-bit signed) gives about 98 dB SNR on a full-scale sine.

# %%
q15 = np.round(reference * 2**15) / 2**15
print(f"max |err| = {max_abs_error(reference, q15):.2e}, SNR = {snr_db(reference, q15):.1f} dB")
