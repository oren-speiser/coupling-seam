"""
Coupling-Seam Diagnostics  -  reproducible pipeline on real data, two machines.

One governance law (Theta = I/R) yields a diagnostic that reads the SEAM between
coupled domains of a machine, not the domains alone.  Given a coupling matrix it
returns: overall stability, the weakest seam, the dominant failure chain, and the
single coupling worth changing.

This script runs the IDENTICAL method, nothing re-tuned, on two different real
machines:
  - a hydraulic test rig  (UCI Condition Monitoring of Hydraulic Systems)
  - a turbofan engine     (NASA C-MAPSS FD001, run to failure)

Honest finding it reproduces: the diagnostic READING transfers across both
machines, but the targeted-repair ADVANTAGE does not. It is real where coupling
is uneven (the hydraulic rig, ~2.3x vs naive, ~1.1-1.2x vs the strict baseline)
and vanishes where the danger is a near-uniform cluster (the engine, ~2x vs
naive but ~1.0x vs the strict baseline).

Math used is established (dominant-eigenvalue stability; eigenvector-guided edge
selection, Restrepo-Ott-Hunt / Van Mieghem et al.; Perron-Frobenius). The
contribution is the cross-domain framing and its application to real data.

Author: Oren A. L. Speiser  -  ORCID 0009-0001-1205-4079  -  MIT License
"""
import io, zipfile, urllib.request
import numpy as np

HYDRAULIC_URL = "https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip"
ENGINE_URL = "https://raw.githubusercontent.com/hankroark/Turbofan-Engine-Degradation/master/CMAPSSData/train_FD001.txt"

HYDRAULIC_DOMAINS = {
    "Mechanical": ["PS1", "PS2", "PS3", "PS4", "PS5", "PS6"],  # pressure
    "Energy":     ["EPS1"],                                    # motor power
    "Flow":       ["FS1", "FS2"],                              # volume flow
    "Thermal":    ["TS1", "TS2", "TS3", "TS4"],                # temperature
    "Vibration":  ["VS1"],                                     # vibration
}
# C-MAPSS sensor columns (1-indexed within the 21-sensor block) grouped by domain.
ENGINE_DOMAINS = {
    "Thermal":  [2, 3, 4, 17],    # T24, T30, T50, bleed enthalpy
    "Pressure": [7, 11],          # P30, Ps30
    "Speed":    [8, 9, 13, 14],   # Nf, Nc, NRf, NRc
    "Flow":     [12, 15, 20, 21], # phi, BPR, W31, W32
}


def standardize(v):
    return (v - v.mean()) / v.std()


def load_hydraulic():
    print("downloading UCI hydraulic dataset ...")
    zf = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(HYDRAULIC_URL).read()))
    want = {s for v in HYDRAULIC_DOMAINS.values() for s in v}
    raw = {}
    for name in zf.namelist():
        key = name.split("/")[-1].replace(".txt", "")
        if key in want:
            raw[key] = np.loadtxt(io.BytesIO(zf.read(name)))
    cols = []
    for sensors in HYDRAULIC_DOMAINS.values():
        z = [standardize(raw[s].mean(axis=1)) for s in sensors]   # mean over the 60s cycle
        cols.append(standardize(np.column_stack(z).mean(axis=1)))
    return np.column_stack(cols), list(HYDRAULIC_DOMAINS)


def load_engine():
    print("downloading NASA C-MAPSS FD001 ...")
    A = np.loadtxt(io.BytesIO(urllib.request.urlopen(ENGINE_URL).read()))
    S = A[:, 5:]                                                   # 21 sensors, one row per cycle
    cols = []
    for idxs in ENGINE_DOMAINS.values():
        z = [standardize(S[:, c - 1]) for c in idxs]
        cols.append(standardize(np.column_stack(z).mean(axis=1)))
    return np.column_stack(cols), list(ENGINE_DOMAINS)


def coupling_matrix(X):
    R = np.corrcoef(X, rowvar=False)
    P = np.linalg.inv(R)
    n = R.shape[0]
    pc = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                pc[i, j] = -P[i, j] / np.sqrt(P[i, i] * P[j, j])
    M = np.abs(pc)
    np.fill_diagonal(M, 0.0)            # nonnegative coupling matrix
    return M


def seam_readings(M, names):
    n = len(names)
    w, V = np.linalg.eigh(M)
    rho = w[-1]
    v = np.abs(V[:, -1]); v /= np.linalg.norm(v)
    print(f"  coupling load rho(M) = {rho:.3f}")
    print("  weakest seam:", ", ".join(f"{d} {val:.2f}" for d, val in
          sorted(zip(names, v), key=lambda t: -t[1])))
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    top = sorted(edges, key=lambda e: -(v[e[0]] * v[e[1]]))[0]
    print(f"  most dangerous coupling: {names[top[0]]} <-> {names[top[1]]} "
          f"(strength {M[top]:.2f}, sensitivity {v[top[0]]*v[top[1]]:.2f})")
    return v, edges


def intervention(M, v, edges):
    rho0 = np.linalg.eigvalsh(M)[-1]
    U = sum(M[e] for e in edges)
    sens = {e: v[e[0]] * v[e[1]] for e in edges}

    def remove(d):
        A = M.copy()
        for (i, j), a in d.items():
            A[i, j] = max(A[i, j] - a, 0); A[j, i] = A[i, j]
        return np.linalg.eigvalsh(A)[-1]

    def greedy(b):
        d, rem = {}, b
        for e in sorted(edges, key=lambda e: -sens[e]):
            if rem <= 0: break
            t = min(M[e], rem); d[e] = t; rem -= t
        return remove(d)

    def naive(b):
        per = b / len(edges); return remove({e: min(M[e], per) for e in edges})

    def strict(b):
        tot = sum(M[e] for e in edges); f = b / tot
        return remove({e: f * M[e] for e in edges})

    print(f"  {'budget':>6} | {'targeted':>8} | {'vs naive':>8} | {'vs strict':>9}")
    for B in (0.10, 0.20, 0.30, 0.40):
        b = B * U
        dT = rho0 - greedy(b); dN = rho0 - naive(b); dS = rho0 - strict(b)
        print(f"  {B:6.0%} | {dT:8.3f} | {dT/dN:7.2f}x | {dT/dS:8.2f}x")


def run(name, loader):
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)
    X, names = loader()
    M = coupling_matrix(X)
    v, edges = seam_readings(M, names)
    intervention(M, v, edges)


if __name__ == "__main__":
    run("MACHINE 1 - hydraulic rig (UCI, real)", load_hydraulic)
    run("MACHINE 2 - turbofan engine (NASA C-MAPSS FD001, real)", load_engine)
    print("\nThe seam reading transfers across both machines. The targeted-repair")
    print("advantage holds on the uneven hydraulic rig and vanishes on the")
    print("near-uniform engine cluster. Both reported honestly.")
