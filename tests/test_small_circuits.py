import math
from circuit_sim import parse_netlist_lines

def test_voltage_divider():
    lines = [
        'V1 1 0 12',
        'R1 1 2 1000',
        'R2 2 0 2000'
    ]
    circ = parse_netlist_lines(lines)
    voltages, res_currents, vsrc_currents = circ.solve()
    V2 = voltages['2']
    expected = 12 * (2000 / (1000 + 2000))
    assert abs(V2 - expected) < 1e-9
