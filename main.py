import sys
import os

# Hacemos que Python encuentre la carpeta 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importamos nuestros módulos
import ui
import interaccion
from circuit_sim import load_netlist

def sesion_usuario():
    """Maneja una sesión completa hasta que el usuario quiera salir o reiniciar."""
    ui.mostrar_encabezado()
    ui.mostrar_ayuda_navegacion()

    ui.console.print("\n[1] Cargar circuito desde archivo (ej: TP4)")
    ui.console.print("[2] Crear circuito nuevo paso a paso")
    
    try:
        opcion = interaccion.input_inteligente("Seleccione", tipo="str")
        circ = None

        # --- MODO ARCHIVO ---
        if opcion == "1":
            ruta_default = "examples/ejercicio_10_tp4.net" # Sugerimos el ejercicio del TP
            ruta = interaccion.input_inteligente(f"Ruta del archivo", tipo="str", default=ruta_default)
            
            if not os.path.exists(ruta):
                ui.console.print(f"[bold red]Error:[/bold red] No se encuentra '{ruta}'")
                interaccion.input_inteligente("Presione Enter para volver", tipo="str")
                return # Vuelve al inicio
            
            circ = load_netlist(ruta)
            ui.console.print(f"[green]✓ Circuito cargado: {ruta}[/green]")
        
        # --- MODO INTERACTIVO ---
        elif opcion == "2":
            circ = interaccion.modo_crear_circuito()
        
        else:
            ui.console.print("[red]Opción no válida[/red]")
            return

        # --- CÁLCULO Y RESULTADOS ---
        if circ:
            ui.mostrar_encabezado()
            try:
                # 1. Resolvemos usando el motor matemático (MNA)
                voltages, res_currents, vsrc_currents = circ.solve()
                
                # 2. Mostramos los resultados visualmente
                ui.mostrar_resultados(voltages, res_currents, vsrc_currents)
                
                # 3. Pausa para ver los datos
                interaccion.input_inteligente("\n[Presione Enter para Reiniciar o Q para Salir]", tipo="str")
                
            except Exception as e:
                ui.console.print(f"[bold red]Error de Cálculo:[/bold red] {e}")
                ui.console.print("Verifique que el circuito tenga Tierra (Nodo 0) y esté cerrado.")
                interaccion.input_inteligente("Enter para continuar", tipo="str")

    except interaccion.VolverAtras:
        return # Al retornar, el bucle en main() vuelve a cargar el menú principal

def main():
    """Bucle infinito que mantiene el programa vivo."""
    while True:
        try:
            sesion_usuario()
        except interaccion.ReiniciarSistema:
            ui.console.print("[yellow]🔄 Reiniciando sistema...[/yellow]")
            continue
        except KeyboardInterrupt:
            print("\nSalida forzada.")
            break
        except Exception as e:
            ui.console.print(f"[bold red]Error Crítico:[/bold red] {e}")
            break

if __name__ == "__main__":
    main()