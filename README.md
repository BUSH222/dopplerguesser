# Dopplerguesser
A project that extracts doppler signatures from satellite passes and guesses what satellite it is automatically.

# Research

The current implementation uses the IQ Exporter block from Sdr++ to stream into a gnuradio pipeline, which uses a phase locked loop to extract the carrier frequency (works with PSK signals for now).

I acquired data from a DMSP satellite which is in raw samples. 

My current thoughts on processing this: ignore the full doppler formula, ignore the relativistic effects, use an estimate with the relative velocity since v_sat << c (calculated frequency drift will be under 2hz from all these effects, even for a highly elliptical orbit)