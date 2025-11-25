"""CLI wrapper para ejecutar el simulador desde src/"""
import argparse
from circuit_sim import load_netlist

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='CLI wrapper para circuit_sim')
    p.add_argument('netlist', help='archivo netlist (.net)')
    p.add_argument('--out-csv', default=None)
    p.add_argument('--out-plot', default=None)
    p.add_argument('--no-plot', action='store_true')
    p.add_argument('--sparse', action='store_true')
    args = p.parse_args()

    circ = load_netlist(args.netlist)
    voltages, res_currents, vsrc_currents = circ.solve(use_sparse_if_possible=args.sparse)

    # Mostrar resultados
    print('\nVoltajes en nodos:')
    for n, v in sorted(voltages.items(), key=lambda x: x[0]):
        print(f"  nodo {n}: {v:.12g} V")

    # export CSV
    if args.out_csv:
        from circuit_sim import export_results_csv
        export_results_csv(args.out_csv, voltages, res_currents, vsrc_currents)
        print(f"Resultados exportados a CSV: {args.out_csv}")

    # plot
    if not args.no_plot:
        from circuit_sim import draw_circuit
        out_plot = args.out_plot or (args.netlist.rsplit('.',1)[0] + '_circuit.png')
        draw_circuit(circ, voltages, res_currents, vsrc_currents, save_path=out_plot)
