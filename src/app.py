#!/usr/bin/env python3
import time
import signal
import os
import sys

# Importa la función de notificación de Systemd.
# En un entorno de contenedores, la biblioteca 'python-systemd' (o similar) 
# debe estar instalada en la imagen.
try:
    from systemd.daemon import notify
except ImportError:
    # Si la librería no está instalada (ej: desarrollo en Windows/Mac),
    # definimos una función dummy para que el código no falle.
    def notify(status):
        #print(f"Systemd NO NOTIFICADO (simulado): {status}")
        pass

# Archivo de detonación de fallo crítico para simular el congelamiento
CRASH_FILE = '/tmp/crash' 

class PhoenixService:
    """
    Servicio de Python que implementa el patrón Systemd Watchdog.
    """
    def __init__(self):
        self.running = True
        self.cycle = 0
        
        # 1. Manejo de señales: Interceptamos SIGTERM para un cierre limpio
        signal.signal(signal.SIGTERM, self.shutdown)
        print("🔥 Phoenix App: Handler de SIGTERM configurado.")
    
    def shutdown(self, signum, frame):
        """Maneja la señal de terminación (Graceful Shutdown)."""
        print("🚨 SIGTERM recibido. Iniciando cierre ordenado...")
        self.running = False
    
    def simulate_crash(self):
        """Simula un fallo lógico (congelamiento) si existe el archivo detonante."""
        if os.path.exists(CRASH_FILE):
            print(f"CRITICAL - 💀 ERROR CRÍTICO DETECTADO: El archivo de fallo '{CRASH_FILE}' existe.")
            print("El servicio ha entrado en un bucle infinito y ha dejado de latir.")
            
            # Entramos en un bucle infinito. 
            # El proceso está VIVO pero CONGELADO.
            # El Watchdog de Systemd lo matará por falta de latido (heartbeat).
            while True:
                time.sleep(1)

    def run(self):
        """Bucle principal del servicio."""
        print("🔥 Phoenix App Iniciada. ID de proceso (PID):", os.getpid())
        
        # 2. Notificación READY: Avisa a Systemd que la inicialización terminó
        notify('READY=1')
        
        # 3. Configuración del Heartbeat: Avisa a Systemd cada cuánto esperamos un latido.
        # En este caso, cada 5 segundos (5,000,000 microsegundos).
        notify('WATCHDOG_USEC=5000000') 
        
        # Bucle de procesamiento principal
        while self.running:
            self.simulate_crash()
            
            try:
                # Lógica del servicio
                print(f"INFO - Procesando... ciclo {self.cycle}")
                
                # 4. Latido (Heartbeat): Mantiene vivo el contador de Systemd
                notify('WATCHDOG=1')
                
                self.cycle += 1
                
                # Esperamos un tiempo menor al del Watchdog (10s) 
                # y al WATCHDOG_USEC (5s)
                time.sleep(1) 
            
            except Exception as e:
                print(f"FATAL: Excepción inesperada: {e}")
                self.running = False
            
        print("INFO - El servicio Phoenix ha finalizado su ciclo.")

if __name__ == '__main__':
    PhoenixService().run()
