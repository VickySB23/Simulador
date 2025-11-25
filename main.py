import sys
import os
import time

# --- CONFIGURACIÓN DE RUTAS ---
# Asegura que Python encuentre la carpeta 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importamos las clases de TU simulador original
try:
    from circuit_sim import load_netlist, Circuit
except ImportError:
    print("Error: No se encuentra 'src/circuit_sim.py'. Asegúrate de estar en la raíz del proyecto.")
    sys.exit(1)

# Importamos Rich para la interfaz
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, FloatPrompt, Confirm
    from rich.align import Align
    from rich import box
except ImportError:
    print("Error: Falta la librería 'rich'. Instálala con: pip install rich")
    sys.exit(1)

console = Console()

# --- FUNCIONES DE VISUALIZACIÓN ---

def mostrar_encabezado():
    console.clear()
    titulo = """
    [bold cyan]SIMULADOR DE CIRCUITOS CC (MNA)[/bold cyan]
    [italic]Coloquio de Física 2 - Sistema Interactivo[/italic]
    """
    console.print(Panel(Align.center(titulo), border_style="blue"))

def mostrar_resultados_rich(voltages, res_currents, vsrc_currents):
    """Muestra los resultados del cálculo en tablas ordenadas."""
    
    # Tabla de Voltajes
    table_nodes = Table(title="⚡ Voltajes en Nodos", show_header=True, header_style="bold magenta", expand=True, box=box.ROUNDED)
    table_nodes.add_column("Nodo", style="dim", justify="center")
    table_nodes.add_column("Voltaje (V)", justify="right", style="bold green")

    for n, v in sorted(voltages.items(), key=lambda x: x[0]):
        estilo = "bold white" if str(n) == "0" else "cyan"
        table_nodes.add_row(f"[{estilo}]{n}[/{estilo}]", f"{v:.4f}")

    # Tabla de Componentes
    table_comp = Table(title="🔌 Análisis de Componentes", show_header=True, header_style="bold yellow", expand=True, box=box.ROUNDED)
    table_comp.add_column("Componente", style="bold cyan")
    table_comp.add_column("Valor", justify="right")
    table_comp.add_column("Corriente (A)", justify="right", style="bold white")
    table_comp.add_column("Potencia (W)", justify="right", style="bold red")
    table_comp.add_column("Detalle", style="dim")

    total_power = 0.0
    
    # Resistencias
    for name, data in res_currents.items():
        I, n1, n2, R = data
        P = (I**2) * R
        total_power += P
        table_comp.add_row(name, f"{R} Ω", f"{I:.5f}", f"{P:.5f}", f"N{n1} → N{n2}")

    # Fuentes
    for name, I in vsrc_currents.items():
        table_comp.add_row(name, "Fuente V", f"{I:.5f}", "-", "Suministro")

    table_comp.add_section()
    table_comp.add_row("TOTAL DISIPADO", "", "", f"[bold underline red]{total_power:.5f}[/]", "Ef. Joule")

    console.print("\n", table_nodes, "\n", table_comp)

# --- FUNCIONES DEL ASISTENTE (WIZARD) ---

def crear_circuito_interactivo():
    """Guía al usuario paso a paso para armar un circuito."""
    circ = Circuit()
    console.print("\n[bold green]🛠️  MODO CONSTRUCTOR DE CIRCUITOS[/bold green]")
    console.print("[dim]Ingresa los componentes uno por uno. Recuerda que el nodo '0' es Tierra (GND).[/dim]\n")

    cont_r = 1
    cont_v = 1

    while True:
        console.print(Panel("[1] Agregar Resistencia (R)\n[2] Agregar Fuente de Voltaje (V)\n[3] Terminar y Simular", title="¿Qué deseas agregar?", border_style="green"))
        opcion = Prompt.ask("Selecciona", choices=["1", "2", "3"])

        if opcion == "3":
            if not circ.resistors and not circ.vsources:
                console.print("[red]¡El circuito está vacío! Agrega algo primero.[/red]")
                continue
            break

        # Agregar Resistencia
        if opcion == "1":
            nombre = f"R{cont_r}"
            console.print(f"[cyan]Agregando {nombre}...[/cyan]")
            
            val = FloatPrompt.ask(f"  Valor de {nombre} (Ohms)")
            n1 = Prompt.ask(f"  Nodo de entrada")
            n2 = Prompt.ask(f"  Nodo de salida")
            
            # Usamos el método de tu clase Circuit original
            circ.add_resistor(nombre, n1, n2, val)
            console.print(f"[green]✓ {nombre} agregado entre {n1} y {n2}[/green]\n")
            cont_r += 1

        # Agregar Fuente
        elif opcion == "2":
            nombre = f"V{cont_v}"
            console.print(f"[cyan]Agregando {nombre}...[/cyan]")
            
            val = FloatPrompt.ask(f"  Voltaje de {nombre} (Volts)")
            n_pos = Prompt.ask(f"  Nodo Positivo (+)")
            n_neg = Prompt.ask(f"  Nodo Negativo (-)")
            
            # Usamos el método de tu clase Circuit original
            circ.add_vsource(nombre, n_pos, n_neg, val)
            console.print(f"[green]✓ {nombre} agregado ({n_pos} -> {n_neg})[/green]\n")
            cont_v += 1

    return circ

# --- BUCLE PRINCIPAL ---

def main():
    mostrar_encabezado()
    
    # 1. Selección de Modo
    console.print("\n[bold reverse] BIENVENIDO [/bold reverse]")
    console.print("¿Cómo deseas trabajar hoy?")
    console.print("  [1] Cargar circuito desde archivo (Ej: example.net)")
    console.print("  [2] Crear circuito paso a paso (Asistente)")
    
    modo = Prompt.ask("Opción", choices=["1", "2"], default="2")

    circ = None

    if modo == "1":
        path = "examples/example.net"
        if not os.path.exists(path):
            path = Prompt.ask("Ingresa la ruta del archivo .net")
        try:
            circ = load_netlist(path)
            console.print(f"[green]✓ Archivo cargado: {path}[/green]")
        except Exception as e:
            console.print(f"[bold red]Error cargando archivo:[/bold red] {e}")
            return
    else:
        circ = crear_circuito_interactivo()

    # 2. Ciclo de Simulación y Edición
    while True:
        mostrar_encabezado()
        
        try:
            # Resolver usando tu lógica MNA
            voltages, res_currents, vsrc_currents = circ.solve()
            mostrar_resultados_rich(voltages, res_currents, vsrc_currents)
        except Exception as e:
            console.print(Panel(f"[bold red]Error Matemático:[/bold red] {e}\nRevisa que el circuito tenga tierra (nodo 0) y lazos cerrados.", title="ERROR DE CÁLCULO"))

        # Menú de edición posterior
        console.print("\n[bold reverse] PANEL DE CONTROL [/bold reverse]")
        console.print(" [1] Editar valor de Resistencia")
        console.print(" [2] Editar valor de Fuente")
        console.print(" [3] Reiniciar / Cargar otro")
        console.print(" [Q] Salir")

        acc = Prompt.ask("Selecciona", choices=["1", "2", "3", "q", "Q"], default="Q")

        if acc.lower() == 'q':
            console.print("[yellow]Fin de la simulación.[/yellow]")
            break
        
        elif acc == "3":
            main() # Reiniciar programa
            break

        elif acc == "1":
            if not circ.resistors:
                console.print("[red]No hay resistencias.[/red]"); time.sleep(1); continue
            
            r_names = [r.name for r in circ.resistors]
            name = Prompt.ask("¿Cuál resistencia?", choices=r_names)
            r_obj = next(r for r in circ.resistors if r.name == name)
            new_val = FloatPrompt.ask(f"Nuevo valor para {name} (Actual: {r_obj.value})")
            r_obj.value = new_val

        elif acc == "2":
            if not circ.vsources:
                console.print("[red]No hay fuentes.[/red]"); time.sleep(1); continue

            v_names = [v.name for v in circ.vsources]
            name = Prompt.ask("¿Cuál fuente?", choices=v_names)
            v_obj = next(v for v in circ.vsources if v.name == name)
            new_val = FloatPrompt.ask(f"Nuevo voltaje para {name} (Actual: {v_obj.value})")
            v_obj.value = new_val

if __name__ == "__main__":
    main()