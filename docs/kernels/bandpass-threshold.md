# Bandpass filter + threshold-crossing detection

The first kernel for both flows. It is small, causal, well understood, and present in SpikeInterface, so a trusted reference and golden vectors are easy to get. Its first comparison is direct versus Bambu.

1. **Bandpass filter:** IIR, second-order sections (biquads), e.g. 300–6000 Hz.
2. **Noise estimate:** median absolute deviation (MAD) per channel.
3. **Threshold crossing:** detect samples beyond *k*·MAD, with a refractory period.

**Reference:** SpikeInterface `bandpass_filter` and `detect_peaks(method="by_channel")`, pinned in `examples/sources.toml`.

!!! note "Hardware-specific choices to document here"
    - Causal filtering (`sosfilt`) versus SpikeInterface's default zero-phase `sosfiltfilt`.
    - A streaming MAD estimate in place of a whole-recording median.
    - Fixed-point formats per stage.
