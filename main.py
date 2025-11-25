import sys
import os
from rich.prompt import Confirm

# Rutas
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import ui
import interaccion
from circuit_sim import load_netlist

def sesion_usuario():
    ui.mostrar_encabezado()
    ui.mostrar_ayuda_navegacion()

    ui.console.print("\n[1] Cargar circuito desde archivo")
    ui.console.print("[2] Crear circuito nuevo paso a paso")
    
    try:
        opcion = interaccion.input_inteligente("Seleccione", tipo="str")
        circ = None

        if opcion == "1":
            ruta_default = "examples/ejercicio_10_tp4.net"
            ruta = interaccion.input_inteligente(f"Ruta archivo", tipo="str", default=ruta_default)
            
            if not os.path.exists(ruta):
                ui.console.print(f"[bold red]Error:[/bold red] No existe '{ruta}'")
                time.sleep(2)
                return 
            
            circ = load_netlist(ruta)
            ui.console.print(f"[green]✓ Cargado: {ruta}[/green]")
        
        elif opcion == "2":
            circ = interaccion.modo_crear_circuito()
        
        else:
            return # Opción inválida, recarga menú

        # --- CÁLCULO ---
        if circ:
            ui.mostrar_encabezado()
            try:
                voltages, res_currents, vsrc_currents = circ.solve()
                ui.mostrar_resultados(voltages, res_currents, vsrc_currents)
                
                interaccion.input_inteligente("\n[Presione Enter para Reiniciar]", tipo="str", default="")
                
            except Exception as e:
                # AQUÍ ESTÁ EL CAMBIO: Manejo elegante del error
                ui.console.print(Panel(f"[bold red]Error Matemático:[/bold red] {e}\n\nProbable causa: Circuito abierto o sin conexión a Tierra (nodo 0).", title="ERROR", border_style="red"))
                
                # Preguntar si quiere reintentar
                if Confirm.ask("¿Desea intentar corregir el circuito? (S/N)"):
                    # Si dice Sí, volvemos al menú principal (donde podría elegir crear de nuevo)
                    # En una versión más avanzada podríamos dejarle editar, 
                    # pero por ahora reiniciar es lo más seguro para el coloquio.
                    return 
                else:
                    sys.exit(0)

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
            ui.console.print(f"[bold red]Error Inesperado:[/bold red] {e}")
            input("Presione Enter para salir...")
            break

if __name__ == "__main__":
    main()