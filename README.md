# Coupling-Seam Diagnostics

**Where a multi-domain machine is weakest is not inside a part. It is the seam between parts.**

Most condition monitoring reads one domain at a time: pressure, heat, power, each alone. But many failures form in the handoff between domains, where load in one quietly raises load in the next until a chain forms. From raw multi-domain sensor data, with no prior knowledge of the machine, this tool locates the weak seam, the dominant failure chain, and the single coupling worth changing. The same method, unchanged, is run on **two different real machines**.

It is the second instrument in a family built on one governance law, **Theta = I/R** (driving load over absorption capacity):

- **Instrument 01 - cross-domain early warning** asks *when* a machine will fail: https://oren-speiser.github.io/cross-domain-earlywarning/
- **Instrument 02 - this one** asks *where* the weak seam is.

**Live demo:** _(enable GitHub Pages, then paste the link here)_

## What it does

Given a cross-domain coupling matrix, the method computes five readings: overall stability from the dominant eigenvalue; the weakest seam from where the least-stable mode concentrates; dangerous couplings ranked by how much the unstable mode runs through them (not by size); the dominant failure chain; and a targeted repair, the single coupling that most improves the margin if weakened.

## Result on two real machines

The identical method, nothing re-tuned, was run on two public benchmarks:

**Hydraulic rig** (UCI Condition Monitoring of Hydraulic Systems, 2,205 cycles, 17 sensors). With no prior knowledge, the estimated coupling places almost all of its strength in an **energy-flow-thermal triangle** (0.89 to 0.96), with mechanical and vibration nearly apart. Physically sensible for a hydraulic system, recovered from raw sensors.

**Turbofan engine** (NASA C-MAPSS FD001, 100 engines run to failure). The reading finds a **thermal-speed-flow cluster** that tightens as the engine degrades, with pressure nearly decoupled. Again sensible, again recovered from raw sensors.

**The honest cross-machine finding.** The diagnostic *reading* transfers cleanly to both machines: it locates the weak seam and the failure chain either way. The targeted-repair *advantage* does not transfer. It is real where coupling is uneven (the hydraulic rig: about 2.3x better than a naive even-split and about 1.1 to 1.2x better than the strictest proportional baseline) and it vanishes where the danger is a near-uniform cluster (the engine: about 2x better than naive but only about 1.0x against the strict baseline, because there is no single edge to target). The tool reports this honestly rather than hiding it.

A non-obvious reading it surfaces on the hydraulic rig: the most dangerous coupling is not the biggest one. The `Mechanical-Vibration` link is fairly heavy (0.33) but carries almost no instability (sensitivity 0.02), so cutting it would waste effort. On the engine there is no such trap; the biggest couplings are also the most dangerous.

## Reproduce from scratch

```bash
pip install -r requirements.txt
python seam_diagnostic.py
```

The script downloads both datasets, reduces each to physical domains (one value per cycle, standardized), estimates coupling as the partial correlation across the cycles, and prints every reading and the intervention comparison for both machines.

## What this is, exactly

- **Data:** real, public benchmarks (Helwig, Pignanelli and Schutze, 2015; Saxena and Goebel, 2008).
- **Math:** established, not new. Dominant-eigenvalue stability, eigenvector-guided edge selection (Restrepo, Ott and Hunt 2006; Van Mieghem et al. 2011), Perron-Frobenius.
- **Contribution:** the cross-domain framing of failure as a seam between physical domains, and the application of the established targeting rule to coupling matrices estimated empirically from real multi-domain data.
- **Limits:** partial correlation is observed dependence, not proven causation. The targeting advantage is a finite-budget empirical result that depends on the machine, as shown above. The internal measurement layer of the broader framework is not disclosed here.

## References

- N. Helwig, E. Pignanelli, A. Schutze. Condition monitoring of a complex hydraulic system using multivariate statistics. IEEE I2MTC, 2015.
- A. Saxena, K. Goebel. Turbofan Engine Degradation Simulation Data Set (C-MAPSS). NASA Ames Prognostics Data Repository, 2008.
- J. G. Restrepo, E. Ott, B. R. Hunt. Characterizing the dynamical importance of network nodes and links. Phys. Rev. Lett. 97, 094102 (2006).
- P. Van Mieghem et al. Decreasing the spectral radius of a graph by link removals. Phys. Rev. E 84, 016101 (2011).

---

**Oren A. L. Speiser** - Systems Architect - Tel Aviv - ORCID 0009-0001-1205-4079 - MIT License
