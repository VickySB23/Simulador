import sys
import time
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
import ui
from circuit_sim import Circuit, parse_value

# Excepciones para control de flujo
class ReiniciarSistema(Exception): pass
class VolverAtras(Exception): pass

def input_inteligente(mensaje, tipo="float", default=None):
    """
    Pide un dato al usuario.
    - Soporta comandos Q (Salir), R (Reiniciar), B (Atrás).
    - Convierte unidades (10k -> 10000).
    - Maneja Enter vacío si hay default.
    """
    while True:
        # Si hay default, lo mostramos en el prompt
        msg_final = mensaje
        
        valor_raw = Prompt.ask(msg_final, default=default)
        
        # Si el usuario da Enter y hay default, Prompt.ask ya devuelve el default.
        # Pero si devuelve None (caso raro), lo convertimos a string vacío.
        if valor_raw is None:
            val = ""
        else:
            val = str(valor_raw).strip()
        
        # Comandos Globales
        if val.lower() == 'q':
            ui.console.print("[bold red]👋 Cerrando simulador...[/bold red]")
            sys.exit(0)
        if val.lower() == 'r':
            raise ReiniciarSistema()
        if val.lower() == 'b':
            raise VolverAtras()

        # Si esperamos texto
        if tipo == "str":
            return val
        
        # Si esperamos número
        if tipo == "float":
            if val == "": return None # Si es vacio, devolvemos None
            try:
                return parse_value(val)
            except ValueError:
                ui.console.print(f"[red]❌ Valor no válido ('{val}').[/red] Intente números como: 10, 1k, 5m")

def modo_crear_circuito():
    """Menú interactivo para armar un circuito."""
    circ = Circuit()
    cont_r = 1
    cont_v = 1

    while True:
        ui.mostrar_encabezado()
        ui.mostrar_ayuda_navegacion()
        
        info = f"[green]{len(circ.resistors)}[/] Resistencias | [green]{len(circ.vsources)}[/] Fuentes de Tensión"
        ui.console.print(Panel(info, title="Estado del Circuito", style="cyan"))

        ui.console.print("\n[1] Agregar Resistencia (R)")
        ui.console.print("[2] Agregar Fuente de Voltaje (V)")
        ui.console.print("[3] [bold green]CALCULAR Y SIMULAR[/bold green]")
        
        try:
            opcion = input_inteligente("\nSeleccione opción", tipo="str")

            if opcion == "3":
                if not circ.resistors and not circ.vsources:
                    ui.console.print("[red]¡El circuito está vacío![/red]")
                    time.sleep(1.5)
                    continue
                return circ

            # --- RESISTENCIA ---
            if opcion == "1":
                ui.console.print(f"\n[cyan]--- Nueva Resistencia R{cont_r} ---[/cyan]")
                val = input_inteligente("  Valor en Ohms (ej: 1k)", default="1k")
                n1 = input_inteligente("  Nodo Entrada", tipo="str")
                n2 = input_inteligente("  Nodo Salida [dim](0=Tierra)[/dim]", tipo="str", default="0")
                
                circ.add_resistor(f"R{cont_r}", n1, n2, val)
                ui.console.print(f"[green]✓ R{cont_r} agregada[/green]")
                cont_r += 1
                time.sleep(0.5)

            # --- FUENTE ---
            elif opcion == "2":
                ui.console.print(f"\n[cyan]--- Nueva Fuente V{cont_v} ---[/cyan]")
                val = input_inteligente("  Voltaje en Volts (ej: 12)", default="12")
                n_pos = input_inteligente("  Nodo Positivo (+)", tipo="str")
                n_neg = input_inteligente("  Nodo Negativo (-) [dim](Enter para 0)[/dim]", tipo="str", default="0")
                
                circ.add_vsource(f"V{cont_v}", n_pos, n_neg, val)
                ui.console.print(f"[green]✓ V{cont_v} agregada[/green]")
                cont_v += 1
                time.sleep(0.5)
                
        except VolverAtras:
            continue