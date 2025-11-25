from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box

# Inicializamos la consola globalmente
console = Console()

# --- TU FIRMA ---
NOMBRE_ALUMNO = "Victoria"  # <--- Puedes agregar tu apellido aquí

def mostrar_encabezado():
    """Limpia la pantalla y muestra el título con tu nombre."""
    console.clear()
    titulo = f"""
    [bold cyan]SIMULADOR DE CIRCUITOS CC (MNA)[/bold cyan]
    [italic]Coloquio de Física 2 - Sistema Interactivo[/italic]
    
    [dim]Desarrollado por:[/dim] [bold yellow]{NOMBRE_ALUMNO}[/bold yellow]
    """
    console.print(Panel(Align.center(titulo), border_style="blue"))

def mostrar_ayuda_navegacion():
    """Muestra la barra de atajos de teclado."""
    console.print(
        "[dim]Atajos:[/dim] [bold red]Q[/] Salir | [bold yellow]R[/] Reiniciar | [bold cyan]B[/] Volver atrás\n"
        "[dim]Formatos aceptados:[/dim] 10k (10000), 5m (0.005), 220 (220)",
        justify="center", style="dim"
    )
    console.print("")

def mostrar_resultados(voltages, res_currents, vsrc_currents):
    """
    Recibe los datos matemáticos y dibuja las tablas bonitas.
    """
    # 1. Tabla de Voltajes
    table_nodes = Table(title="⚡ Voltajes en Nodos", show_header=True, header_style="bold magenta", expand=True, box=box.ROUNDED)
    table_nodes.add_column("Nodo", style="dim", justify="center")
    table_nodes.add_column("Voltaje (V)", justify="right", style="bold green")

    # Intentamos ordenar numéricamente los nodos para que salga (0, 1, 2...)
    try:
        sorted_nodes = sorted(voltages.items(), key=lambda x: int(x[0]))
    except ValueError:
        sorted_nodes = sorted(voltages.items(), key=lambda x: x[0])

    for n, v in sorted_nodes:
        # Resaltamos la Tierra (Nodo 0)
        estilo = "bold white" if str(n) == "0" else "cyan"
        etiqueta = "TIERRA (GND)" if str(n) == "0" else str(n)
        table_nodes.add_row(f"[{estilo}]{etiqueta}[/{estilo}]", f"{v:.4f}")

    # 2. Tabla de Componentes (Resistencias y Fuentes)
    table_comp = Table(title="🔌 Análisis de Componentes", show_header=True, header_style="bold yellow", expand=True, box=box.ROUNDED)
    table_comp.add_column("Componente", style="bold cyan")
    table_comp.add_column("Valor", justify="right")
    table_comp.add_column("Corriente (A)", justify="right", style="bold white")
    table_comp.add_column("Potencia (W)", justify="right", style="bold red")
    table_comp.add_column("Conexión", style="dim")

    total_power = 0.0
    
    # Filas de Resistencias
    for name, data in res_currents.items():
        I, n1, n2, R = data
        P = (I**2) * R
        total_power += P
        table_comp.add_row(
            name, 
            f"{R:.1f} Ω", 
            f"{I:.5f}", 
            f"{P:.5f}", 
            f"N{n1} → N{n2}"
        )

    # Filas de Fuentes
    for name, I in vsrc_currents.items():
        table_comp.add_row(name, "Fuente V", f"{I:.5f}", "-", "Suministro")

    # Pie de página con totales
    table_comp.add_section()
    table_comp.add_row("TOTAL DISIPADO", "", "", f"[bold underline red]{total_power:.5f}[/]", "Ef. Joule")

    console.print("\n", table_nodes, "\n", table_comp)