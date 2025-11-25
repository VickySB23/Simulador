import sys
import os
import time
from rich.prompt import Confirm

# Rutas
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import ui
import interaccion
from circuit_sim import load_netlist

def sesion_usuario():
    ui.mostrar_encabezado()
    
    # Menú Principal Simplificado
    ui.console.print("\n[1] Cargar Ejercicio 10 (TP4)")
    ui.console.print("[2] Crear circuito nuevo paso a paso")
    
    try:
        opcion = interaccion.input_inteligente("Seleccione", tipo="str")
        circ = None

        # --- OPCIÓN 1: CARGAR ARCHIVO ---
        if opcion == "1":
            ruta = "examples/ejercicio_10_tp4.net"
            
            if not os.path.exists(ruta):
                ui.console.print(f"[bold red]Error:[/bold red] No encuentro '{ruta}'.")
                time.sleep(3); return 
            
            circ = load_netlist(ruta)
            ui.console.print(f"[green]✓ Circuito cargado exitosamente[/green]")
            
            # Mostramos el esquema en la terminal
            ui.mostrar_resumen_vivo(circ)
            time.sleep(1.5) # Pequeña pausa para leer
        
        # --- OPCIÓN 2: MODO MANUAL ---
        elif opcion == "2":
            circ = interaccion.modo_crear_circuito()
        
        else:
            return 

        # --- MOTOR DE CÁLCULO ---
        if circ:
            try:
                # 1. Resolver
                voltages, res_currents, vsrc_currents = circ.solve()
                
                # 2. Mostrar Resultados (Tablas)
                if opcion == "1": ui.mostrar_encabezado() # Limpiar pantalla para ver limpio
                ui.mostrar_resultados(voltages, res_currents, vsrc_currents)
                
                # 3. Final
                interaccion.input_inteligente("\n[Presione Enter para Reiniciar]", tipo="str", default="")
                
            except Exception as e:
                ui.console.print(ui.Panel(f"[bold red]Error Matemático:[/bold red] {e}\n\nCausa probable: Circuito abierto o sin Tierra (0).", title="ERROR", border_style="red"))
                if Confirm.ask("¿Intentar corregir?"): return 
                else: sys.exit(0)

    except interaccion.VolverAtras:
        return 

def main():
    while True:
        try:
            sesion_usuario()
        except interaccion.ReiniciarSistema:
            ui.console.print("[yellow]🔄 Reiniciando...[/yellow]")
            continue
        except KeyboardInterrupt:
            break
        except Exception as e:
            # Captura general para que no se cierre de golpe
            ui.console.print(f"[bold red]Error Inesperado:[/bold red] {e}")
            input("Presione Enter para salir...")
            break

if __name__ == "__main__":
    main()