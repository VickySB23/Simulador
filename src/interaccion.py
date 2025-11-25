import sys
import time
from rich.prompt import Prompt
from rich.panel import Panel
# Importamos el módulo UI y el motor matemático (circuit_sim)
import ui
from circuit_sim import Circuit, parse_value

# Excepciones para controlar el flujo (Atrás / Reiniciar)
class ReiniciarSistema(Exception): pass
class VolverAtras(Exception): pass

def input_inteligente(mensaje, tipo="float", default=None):
    """
    Pide un dato al usuario. Detecta comandos (Q, R, B) y convierte unidades.
    Ejemplo: Si el usuario escribe '10k', devuelve 10000.0
    """
    while True:
        valor_raw = Prompt.ask(mensaje, default=default)
        val = valor_raw.strip()
        
        # Comandos de Navegación Global
        if val.lower() == 'q':
            ui.console.print("[bold red]👋 Cerrando simulador... ¡Éxitos![/bold red]")
            sys.exit(0)
        if val.lower() == 'r':
            raise ReiniciarSistema()
        if val.lower() == 'b':
            raise VolverAtras()

        # Si pedimos texto (ej: nombre de nodo)
        if tipo == "str":
            return val
        
        # Si pedimos número (ej: resistencia), usamos el parser del motor
        if tipo == "float":
            try:
                return parse_value(val)
            except ValueError:
                ui.console.print(f"[red]❌ Valor no válido.[/red] Intente: 10, 1k, 5m, 2.2M")

def modo_crear_circuito():
    """Menú interactivo para armar un circuito paso a paso."""
    circ = Circuit()
    cont_r = 1
    cont_v = 1

    while True:
        ui.mostrar_encabezado()
        ui.mostrar_ayuda_navegacion()
        
        # Resumen de lo que llevamos armado
        info = f"[green]{len(circ.resistors)}[/] Resistencias | [green]{len(circ.vsources)}[/] Fuentes de Tensión"
        ui.console.print(Panel(info, title="Estado del Circuito", style="cyan"))

        ui.console.print("\n[1] Agregar Resistencia (R)")
        ui.console.print("[2] Agregar Fuente de Voltaje (V)")
        ui.console.print("[3] [bold green]CALCULAR Y VER RESULTADOS[/bold green]")
        
        try:
            opcion = input_inteligente("\nSeleccione opción", tipo="str")

            if opcion == "3":
                # Validar que haya algo antes de calcular
                if not circ.resistors and not circ.vsources:
                    ui.console.print("[red]¡El circuito está vacío! Agrega componentes primero.[/red]")
                    time.sleep(1.5)
                    continue
                return circ

            # --- AGREGAR RESISTENCIA ---
            if opcion == "1":
                ui.console.print(f"\n[cyan]--- Nueva Resistencia R{cont_r} ---[/cyan]")
                val = input_inteligente("  Valor en Ohms (ej: 1k, 220)")
                n1 = input_inteligente("  Nodo Entrada (ej: 1)", tipo="str")
                n2 = input_inteligente("  Nodo Salida (0 es Tierra)", tipo="str")
                
                circ.add_resistor(f"R{cont_r}", n1, n2, val)
                ui.console.print(f"[green]✓ R{cont_r} agregada correctamente[/green]")
                cont_r += 1
                time.sleep(0.5)

            # --- AGREGAR FUENTE ---
            elif opcion == "2":
                ui.console.print(f"\n[cyan]--- Nueva Fuente V{cont_v} ---[/cyan]")
                val = input_inteligente("  Voltaje en Volts (ej: 12, 5)")
                n_pos = input_inteligente("  Nodo Positivo (+)", tipo="str")
                n_neg = input_inteligente("  Nodo Negativo (-)", tipo="str")
                
                circ.add_vsource(f"V{cont_v}", n_pos, n_neg, val)
                ui.console.print(f"[green]✓ V{cont_v} agregada correctamente[/green]")
                cont_v += 1
                time.sleep(0.5)
                
        except VolverAtras:
            # Si presiona 'B' en el menú principal, no hace nada (sigue ahí).
            # Si lo presiona dentro de una opción, el 'except' lo captura y vuelve al menú.
            continue