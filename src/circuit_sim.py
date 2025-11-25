"""
circuit_sim.py

Simulador de circuitos en Corriente Continua (DC) usando MNA (Modified Nodal Analysis).
Características:
- Soporta resistencias (R), fuentes de tensión (V) y fuentes de corriente (I).
- Parser simple de netlist (texto): líneas del tipo `Rname n1 n2 value` / `Vname n+ n- value` / `Iname n+ n- value`.
- Maneja etiquetas de nodo arbitrarias (strings). Nodo de referencia/masa: 0 o GND.
- Resuelve por MNA y devuelve voltajes nodales, corrientes en fuentes de tensión y corrientes en resistencias.
- Exporta resultados a CSV y guarda una figura con la representación del circuito.
- CLI sencillo: `python circuit_sim.py example.net`.

Formato netlist de ejemplo (example.net):
# ejemplo de circuito
V1 1 0 10
R1 1 2 100
R2 2 0 200
R3 1 0 1000
I1 2 0 0.005

Dependencias: numpy, matplotlib. Opcionales: networkx (mejor layout), scipy (sparse solvers).
"""

from __future__ import annotations
import argparse
import csv
import math
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import matplotlib.pyplot as plt

# Tratar de usar networkx para mejor layout si está disponible
try:
    import networkx as nx
    _HAS_NETWORKX = True
except Exception:
    _HAS_NETWORKX = False

# Tratar de usar scipy.sparse para circuitos grandes
try:
    from scipy import sparse
    from scipy.sparse.linalg import spsolve
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False


SI_PREFIXES = {
    'G': 1e9,
    'M': 1e6,
    'k': 1e3,
    'K': 1e3,
    'm': 1e-3,
    'u': 1e-6,
    'µ': 1e-6,
    'n': 1e-9,
    'p': 1e-12,
}

def parse_value(token: str) -> float:
    """Parsea un valor numérico con sufijo SI opcional (ej: 10k, 5m, 2.2u).
    Si no reconoce el formato, lanza ValueError.
    """
    token = token.strip()
    # permitir notación científica directamente
    try:
        return float(token)
    except ValueError:
        pass

    # buscar sufijo letra/s
    m = re.fullmatch(r"([+-]?[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)([a-zA-Zµ%]+)", token)
    if not m:
        raise ValueError(f"No se pudo parsear el valor: '{token}'")
    base = float(m.group(1))
    suf = m.group(2)
    # soportar porcentaje (por ejemplo tolerancia) - no se usa aquí, pero lo dejamos: 10% -> 0.10
    if suf.endswith('%'):
        return base * (float(suf[:-1]) / 100.0)
    # prefijo SI simple (una letra)
    if suf in SI_PREFIXES:
        return base * SI_PREFIXES[suf]
    # si el sufijo es algo como 'mA' o 'kOhm', intentar reducir a la letra final
    for ch in suf:
        if ch in SI_PREFIXES:
            return base * SI_PREFIXES[ch]
    raise ValueError(f"Sufijo desconocido al parsear valor: '{suf}'")


@dataclass
class Resistor:
    name: str
    n1: str
    n2: str
    value: float  # ohms


@dataclass
class VSource:
    name: str
    n_plus: str
    n_minus: str
    value: float  # volts


@dataclass
class ISource:
    name: str
    n_plus: str
    n_minus: str
    value: float  # amperes


class Circuit:
    def __init__(self):
        self.resistors: List[Resistor] = []
        self.vsources: List[VSource] = []
        self.isources: List[ISource] = []
        self.nodes: set = set()

    def _add_node(self, node: str):
        if node.upper() == 'GND':
            node = '0'
        self.nodes.add(str(node))

    def add_resistor(self, name: str, n1: str, n2: str, R: float):
        self.resistors.append(Resistor(name, str(n1), str(n2), float(R)))
        self._add_node(n1); self._add_node(n2)

    def add_vsource(self, name: str, n_plus: str, n_minus: str, V: float):
        self.vsources.append(VSource(name, str(n_plus), str(n_minus), float(V)))
        self._add_node(n_plus); self._add_node(n_minus)

    def add_isource(self, name: str, n_plus: str, n_minus: str, I: float):
        self.isources.append(ISource(name, str(n_plus), str(n_minus), float(I)))
        self._add_node(n_plus); self._add_node(n_minus)

    def node_index_map(self) -> Tuple[Dict[str,int], List[str]]:
        # nodo de referencia tierra: '0' (si no existe, agregamos)
        if '0' not in self.nodes:
            self.nodes.add('0')
        # Excluir tierra de incógnitas de voltaje
        unknowns = sorted([n for n in self.nodes if n != '0'])
        idx = {n:i for i,n in enumerate(unknowns)}
        return idx, unknowns

    # --- Montaje y solución MNA ---
    def assemble_mna(self):
        idx_map, nodes = self.node_index_map()
        N = len(nodes)  # number of unknown node voltages
        M = len(self.vsources)  # number of voltage sources (additional unknown currents)

        # G matrix (NxN), I vector (N)
        G = np.zeros((N,N), dtype=float)
        Ivec = np.zeros((N,), dtype=float)

        # B matrix (NxM) and E vector (M)
        B = np.zeros((N,M), dtype=float)
        E = np.zeros((M,), dtype=float)

        # Resistances -> G
        for r in self.resistors:
            g = 1.0 / r.value
            n1 = r.n1; n2 = r.n2
            if n1 != '0':
                i = idx_map[n1]; G[i,i] += g
            if n2 != '0':
                j = idx_map[n2]; G[j,j] += g
            if n1 != '0' and n2 != '0':
                i = idx_map[n1]; j = idx_map[n2]
                G[i,j] -= g; G[j,i] -= g

        # Current sources -> Ivec. Convención: la corriente 'value' va de n_plus -> n_minus.
        for src in self.isources:
            n_plus = src.n_plus; n_minus = src.n_minus; val = src.value
            if n_plus != '0':
                Ivec[idx_map[n_plus]] -= val
            if n_minus != '0':
                Ivec[idx_map[n_minus]] += val

        # Voltage sources -> B and E
        for k, vs in enumerate(self.vsources):
            E[k] = vs.value
            if vs.n_plus != '0':
                B[idx_map[vs.n_plus], k] = 1.0
            if vs.n_minus != '0':
                B[idx_map[vs.n_minus], k] = -1.0

        # Montar sistema A * x = z
        if M > 0:
            top = np.hstack((G, B))
            bottom = np.hstack((B.T, np.zeros((M, M), dtype=float)))
            A = np.vstack((top, bottom))
            z = np.concatenate((Ivec, E))
        else:
            A = G
            z = Ivec

        return A, z, idx_map, nodes

    def solve(self, use_sparse_if_possible: bool = True):
        """Resuelve el circuito. Devuelve (voltages_dict, res_currents_dict, vsrc_currents_dict)
        voltages_dict: {node_label: voltage}
        res_currents_dict: {resistor_name: (I, n1, n2, R)} corriente positiva n1 -> n2
        vsrc_currents_dict: {vsource_name: I} corriente positiva salida del terminal + de la fuente
        """
        A, z, idx_map, nodes = self.assemble_mna()
        size = A.shape[0]

        # Resolver A x = z
        try:
            if _HAS_SCIPY and use_sparse_if_possible and size > 50:
                # intentar resolver en sparse
                A_sp = sparse.csr_matrix(A)
                sol = spsolve(A_sp, z)
            else:
                sol = np.linalg.solve(A, z)
        except np.linalg.LinAlgError as e:
            raise RuntimeError(f"No se pudo resolver el sistema lineal: {e}")

        # Extraer soluciones
        M = len(self.vsources)
        N = len(nodes)
        if M > 0:
            Vsol = sol[:N]
            Isrc = sol[N: N+M]
        else:
            Vsol = sol
            Isrc = np.array([])

        # Construir diccionario de voltajes (incluir tierra '0')
        voltages = {'0': 0.0}
        for n, i in idx_map.items():
            voltages[n] = float(Vsol[i])

        # Corrientes en resistencias (convención: n1 -> n2)
        res_currents = {}
        for r in self.resistors:
            v1 = voltages.get(r.n1, 0.0)
            v2 = voltages.get(r.n2, 0.0)
            I_R = (v1 - v2) / r.value
            res_currents[r.name] = (float(I_R), r.n1, r.n2, float(r.value))

        # Corrientes en fuentes de tensión (según solución Isrc)
        vsrc_currents = {}
        for k, vs in enumerate(self.vsources):
            vsrc_currents[vs.name] = float(Isrc[k]) if M > 0 else 0.0

        return voltages, res_currents, vsrc_currents


# ---------------- Netlist parsing ----------------

def parse_netlist_lines(lines: List[str]) -> Circuit:
    circ = Circuit()
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith('*') or line.startswith('#') or line.startswith(';'):
            continue
        parts = re.split(r"\s+", line)
        tok = parts[0]
        try:
            if tok[0].upper() == 'R' and len(parts) >= 4:
                name = parts[0]
                n1 = parts[1]
                n2 = parts[2]
                val = parse_value(parts[3])
                circ.add_resistor(name, n1, n2, val)
            elif tok[0].upper() == 'V' and len(parts) >= 4:
                name = parts[0]
                n_plus = parts[1]
                n_minus = parts[2]
                val = parse_value(parts[3])
                circ.add_vsource(name, n_plus, n_minus, val)
            elif tok[0].upper() == 'I' and len(parts) >= 4:
                name = parts[0]
                n_plus = parts[1]
                n_minus = parts[2]
                val = parse_value(parts[3])
                circ.add_isource(name, n_plus, n_minus, val)
            else:
                # ignorar líneas desconocidas pero avisar
                print(f"[WARN] Línea {lineno}: no se reconoce o tiene formato incorrecto: '{line}'")
        except Exception as e:
            raise RuntimeError(f"Error parseando línea {lineno} ('{line}'): {e}")
    return circ

def load_netlist(path: str) -> Circuit:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Netlist no encontrado: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return parse_netlist_lines(lines)


# ---------------- Utilities: export y dibujo ----------------

def export_results_csv(out_csv: str, voltages: Dict[str,float], res_currents: Dict[str,Tuple[float,str,str,float]], vsrc_currents: Dict[str,float]):
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Node', 'Voltage (V)'])
        for n, v in sorted(voltages.items()):
            w.writerow([n, f"{v:.12g}"])
        w.writerow([])
        w.writerow(['Resistor', 'I (A)', 'From', 'To', 'R (Ohm)', 'P (W)'])
        for name, (I, n1, n2, R) in res_currents.items():
            P = I*I*R
            w.writerow([name, f"{I:.12g}", n1, n2, f"{R:.12g}", f"{P:.12g}"])
        w.writerow([])
        w.writerow(['VoltageSource', 'I (A)'])
        for name, I in vsrc_currents.items():
            w.writerow([name, f"{I:.12g}"])

def draw_circuit(circ: Circuit, voltages: Dict[str,float], res_currents: Dict[str,Tuple[float,str,str,float]], vsrc_currents: Dict[str,float], save_path: str = None):
    # Construir grafo para layout
    nodes = sorted(list(circ.nodes))
    if '0' not in nodes:
        nodes.append('0')

    pos = {}
    if _HAS_NETWORKX:
        G = nx.Graph()
        for n in nodes:
            G.add_node(n)
        for r in circ.resistors:
            G.add_edge(r.n1, r.n2)
        for v in circ.vsources:
            G.add_edge(v.n_plus, v.n_minus)
        try:
            pos = nx.spring_layout(G, seed=42)
        except Exception:
            pos = None
    if not pos:
        # fallback: distribución circular
        num = len(nodes)
        radius = 3.0
        for i, n in enumerate(nodes):
            angle = 2*math.pi*i/num
            pos[n] = (radius*math.cos(angle), radius*math.sin(angle))

    fig, ax = plt.subplots(figsize=(8,6))
    ax.set_aspect('equal')
    ax.axis('off')

    # dibujar nodos
    for n,(x,y) in pos.items():
        ax.plot(x, y, 'o', markersize=6)
        ax.text(x, y+0.12, f"{n}\n{voltages.get(n,0.0):.3f} V", ha='center', fontsize=8)

    def draw_element(n1,n2,label, mid_offset=0.0):
        x1,y1 = pos[n1]; x2,y2 = pos[n2]
        ax.plot([x1,x2],[y1,y2], linewidth=2)
        xm,ym = (x1+x2)/2, (y1+y2)/2
        # pequeño corrimiento para que labels no se monten
        ax.text(xm+mid_offset, ym+mid_offset, label, ha='center', va='center', fontsize=8, bbox=dict(boxstyle='round', alpha=0.12))

    # resistors
    for r in circ.resistors:
        I, n1, n2, R = res_currents[r.name]
        draw_element(n1, n2, f"{r.name}\n{R:.3g}Ω")
        # flecha indicando sentido y valor
        x1,y1 = pos[n1]; x2,y2 = pos[n2]
        dx,dy = x2-x1, y2-y1
        xm,ym = x1 + 0.35*dx, y1 + 0.35*dy
        ax.annotate('', xy=(xm+0.06*dx, ym+0.06*dy), xytext=(xm-0.06*dx, ym-0.06*dy), arrowprops=dict(arrowstyle='->', linewidth=1.2))
        ax.text(xm + 0.09*dx, ym + 0.09*dy, f"{I:.4g} A", fontsize=7)

    # voltage sources
    for v in circ.vsources:
        draw_element(v.n_plus, v.n_minus, f"{v.name}\n{v.value:.3g} V", mid_offset=-0.08)
        I_v = vsrc_currents.get(v.name, 0.0)
        x1,y1 = pos[v.n_plus]; x2,y2 = pos[v.n_minus]
        xm,ym = (x1+x2)/2, (y1+y2)/2
        ax.text(xm, ym-0.18, f"I={I_v:.4g} A", fontsize=7)

    ax.set_title('Circuito DC - nodos (V) y corrientes (A)')
    if save_path:
        plt.tight_layout()
        fig.savefig(save_path, dpi=200)
        print(f"Figura guardada en: {save_path}")
    plt.close(fig)


# ----------------- CLI / Main -----------------

def main():
    p = argparse.ArgumentParser(description='Simulador DC (MNA) - circuit_sim.py')
    p.add_argument('netlist', help='archivo netlist (.net) con descripción del circuito')
    p.add_argument('--out-csv', default=None, help='archivo CSV donde exportar resultados')
    p.add_argument('--out-plot', default=None, help='ruta para guardar imagen del circuito (PNG)')
    p.add_argument('--no-plot', action='store_true', help='no generar figura')
    p.add_argument('--sparse', action='store_true', help='intentar usar solver sparse si está disponible')
    args = p.parse_args()

    circ = load_netlist(args.netlist)
    voltages, res_currents, vsrc_currents = circ.solve(use_sparse_if_possible=args.sparse)

    # Mostrar resultados en consola
    print('\nVoltajes en nodos:')
    for n, v in sorted(voltages.items(), key=lambda x: x[0]):
        print(f"  nodo {n}: {v:.12g} V")

    print('\nCorrientes en resistencias (convención: n1 -> n2):')
    for name, (I, n1, n2, R) in res_currents.items():
        P = I*I*R
        print(f"  {name}: I = {I:.12g} A  (de {n1} a {n2}), P = {P:.12g} W")

    print('\nCorrientes en fuentes de voltaje:')
    for name, I in vsrc_currents.items():
        print(f"  {name}: I = {I:.12g} A")

    # exportar CSV
    if args.out_csv:
        export_results_csv(args.out_csv, voltages, res_currents, vsrc_currents)
        print(f"Resultados exportados a CSV: {args.out_csv}")

    # dibujar y guardar figura
    if not args.no_plot:
        out_plot = args.out_plot or (os.path.splitext(args.netlist)[0] + '_circuit.png')
        draw_circuit(circ, voltages, res_currents, vsrc_currents, save_path=out_plot)


if __name__ == '__main__':
    main()
