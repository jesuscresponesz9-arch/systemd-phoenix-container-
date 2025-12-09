# 🔥 Phoenix Container: Arquitectura de Autocuración con Systemd + Podman

## 📋 Resumen Ejecutivo

**Phoenix Container** es una demostración técnica de servicios de misión crítica con recuperación automática. Combina Systemd Watchdog, Podman Quadlets y hardening de contenedores para servicios resistentes a congelamientos (hangs).

### Puntos Clave
- **Zero-downtime**: Recuperación automática en segundos
- **Rootless**: Ejecución segura sin privilegios
- **Production-ready**: Configuraciones listas para producción
- **Minimalista**: Sin dependencias externas complejas

---

## 🏗️ Arquitectura Técnica

### Componentes Principales

```text
┌─────────────────────────────────────────────────────────┐
│                    Host System (Linux)                   │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────┐  │
│  │                Systemd User Service               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │  │
│  │  │  Watchdog   │◄─┤   Quadlet   │◄─┤  Socket   │ │  │
│  │  │  (10s)      │  │  .container │  │  UNIX     │ │  │
│  │  └─────────────┘  └─────────────┘  └───────────┘ │  │
│  └─────────────┬─────────────────────────────────────┘  │
│                ▼                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Container (Podman)                   │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │            Phoenix Application              │  │  │
│  │  │  • Python 3.11+                            │  │  │
│  │  │  • sd_notify() heartbeat                   │  │  │
│  │  │  • Graceful shutdown                       │  │  │
│  │  │  • Read-only filesystem                    │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Flujo de Autocuración
1. **Heartbeat**: Aplicación notifica a Systemd cada 5 segundos
2. **Fallo**: App se congela, deja de enviar heartbeats
3. **Timeout**: Systemd espera 10 segundos
4. **Terminación**: Systemd envía SIGABRT → SIGKILL
5. **Recuperación**: Systemd reinicia automáticamente
6. **Verificación**: Nueva instancia funciona

---

## 📁 Estructura del Proyecto

```
phoenix-systemd/
├── src/
│   ├── app.py                 # Aplicación principal con watchdog
│   └── Containerfile          # Definición de imagen OCI
├── config/
│   └── phoenix.container      # Definición Quadlet
└── README.md                 # Este archivo
```

---

## 🚀 Despliegue Rápido

### Requisitos
```bash
# Distribución Linux con Systemd
# Podman 4.0+
# Python 3.11+ (para desarrollo)
```

### Instalación
```bash
# 1. Construir imagen
cd phoenix-systemd
podman build -t phoenix-app ./src

# 2. Configurar Quadlet
mkdir -p ~/.config/containers/systemd/
cp config/phoenix.container ~/.config/containers/systemd/

# 3. Activar servicio
systemctl --user daemon-reload
systemctl --user start phoenix
```

---

## 🔧 Configuración

### Archivo Quadlet (`phoenix.container`)
```ini
[Unit]
Description=Phoenix Self-Healing Container
After=network-online.target

[Container]
Image=localhost/phoenix-app:latest
ContainerName=phoenix-service
Notify=yes
WatchdogSec=10
Restart=always
RestartSec=5

# Seguridad
ReadOnly=true
NoNewPrivileges=true
DropCapability=ALL
MemoryMax=50M
CPUQuota=10%

# Networking
PublishPort=8080:8080

[Install]
WantedBy=default.target
```

### Aplicación Python (`app.py`)
```python
#!/usr/bin/env python3
import time
import signal
from systemd.daemon import notify

class PhoenixService:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def shutdown(self, signum, frame):
        self.running = False
    
    def run(self):
        notify('READY=1')
        notify('WATCHDOG_USEC=5000000')  # 5 segundos
        
        while self.running:
            try:
                # Trabajo normal
                print("Procesando...")
                
                # Heartbeat para Systemd
                notify('WATCHDOG=1')
                
                time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == '__main__':
    PhoenixService().run()
```

---

## 🧪 Pruebas

### Simular Fallo
```bash
# Congelar servicio
podman exec phoenix-service touch /tmp/phoenix-crash

# Ver recuperación
journalctl --user -f -u phoenix
```

### Ver Estado
```bash
# Estado del servicio
systemctl --user status phoenix

# Logs en tiempo real
journalctl --user -u phoenix -f

# Métricas del contenedor
podman stats phoenix-service
```

---

## 🛡️ Seguridad

### Hardening Implementado
- **Rootless**: Usuario sin privilegios
- **Read-only**: Filesystem inmutable
- **No capabilities**: Sin privilegios del kernel
- **Resource limits**: CPU/Memoria controlados
- **No new privileges**: Bloquea escalada

### Verificación
```bash
# Verificar seguridad
podman inspect phoenix-service | jq '.[0].HostConfig'

# Probar privilegios
podman exec phoenix-service whoami  # Debe ser "phoenix"
podman exec phoenix-service touch /test  # Debe fallar
```

---

## 📊 Monitoreo

### Métricas Disponibles
```bash
# Heartbeats por minuto
journalctl --user -u phoenix --since "5 minutes ago" | grep "Heartbeat" | wc -l

# Reinicios del servicio
systemctl --user show phoenix | grep NRestarts

# Uso de recursos
podman stats --no-stream phoenix-service
```

### Integración con Systemd
```bash
# Ver propiedades del watchdog
systemctl --user show phoenix | grep Watchdog

# Forzar verificación
systemctl --user kill -s ALRM phoenix
```

---

## 🔍 Troubleshooting

### Problemas Comunes

1. **Servicio no inicia**
   ```bash
   # Ver errores de inicio
   journalctl --user -u phoenix -b
   
   # Verificar imagen
   podman images | grep phoenix
   ```

2. **Watchdog no funciona**
   ```bash
   # Verificar notificaciones
   journalctl --user -u phoenix | grep "WATCHDOG"
   
   # Verificar socket
   ls -la /run/user/$UID/systemd/notify
   ```

3. **Permisos denegados**
   ```bash
   # Verificar usuario
   podman exec phoenix-service id
   
   # Verificar capabilities
   podman exec phoenix-service capsh --print
   ```

---

## 📚 Referencias

### Documentación Oficial
- [Systemd Watchdog](https://www.freedesktop.org/software/systemd/man/watchdog.html)
- [Podman Quadlets](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)
- [Linux Capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html)

### Herramientas Relacionadas
- **Podman**: Containers sin daemon
- **Systemd**: Init system y watchdog
- **Python systemd**: Biblioteca para integración

---

## 🏆 Casos de Uso

### Ideal Para
- Servicios de misión crítica
- Dispositivos edge/IoT
- Kioskos y terminales públicos
- Pasarelas de pago

### Ventajas
1. **Autonomía**: Se repara solo
2. **Seguridad**: Configuración hardened
3. **Simplicidad**: Sin orquestadores complejos
4. **Eficiencia**: Bajo overhead

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE) para detalles.

---

## 👤 Autor
**Jesus Crespo**  


