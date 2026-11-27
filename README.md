# SIGRH — Sistema Integral de Gestión de Recursos Humanos

Proyecto final de Sistemas Distribuidos.

## Descripción

SIGRH administra cuatro áreas de Recursos Humanos:

- Reclutamiento: vacantes y candidatos.
- Usuarios: identidad y datos básicos de empleados.
- Vacaciones: solicitudes, días disponibles y autorizaciones.
- Nómina: cálculo e historial de nóminas.

El proyecto parte de un monolito Django y separa sus
responsabilidades en cuatro microservicios.

## Arquitectura

La aplicación utiliza:

- Python y Django.
- PostgreSQL, con una base independiente por servicio.
- HTTP y JSON para comunicación entre servicios.
- Docker Compose para la ejecución conjunta.
- Nginx como punto de entrada HTTP.

La interfaz original de SIGRH conserva temporalmente
SQLite para sesiones y autenticación web.

## Estructura

- `SIGRH/`: configuración de la interfaz original.
- `usuarios/`: interfaz web de usuarios.
- `reclutamiento/`: interfaz de reclutamiento.
- `vacaciones/`: interfaz de vacaciones.
- `nomina/`: interfaz de nómina.
- `servicios/`: cuatro microservicios Django.
- `infra/nginx/`: configuración del gateway.
- `scripts/`: herramientas de preparación.
- `docs/`: documentación técnica.

## Requisitos

- Docker Desktop.
- Docker Compose.
- Python y las dependencias de `requirements.txt`.
- Archivos `.env` configurados.

## Preparación del entorno existente

Los archivos `.env` contienen información privada
y no se publican en GitHub.

El procedimiento detallado se encuentra en:

`docs/ARRANQUE_DOCKER.md`

## Inicio del sistema

Desde la raíz del proyecto:

```powershell
python scripts/preparar_compose.py
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Entrada web:

http://127.0.0.1:8080/

## Verificación

Consultar:

- `/salud/usuarios`
- `/salud/reclutamiento`
- `/salud/vacaciones`
- `/salud/nomina`

## Operaciones principales

1. Iniciar sesión.
2. Administrar vacantes y candidatos.
3. Consultar y solicitar vacaciones.
4. Aprobar o rechazar solicitudes.
5. Registrar nóminas con permisos administrativos.
6. Consultar historiales autorizados.

## Estado de implementación

Los cuatro microservicios cuentan con APIs HTTP
y bases PostgreSQL independientes.

La autenticación web sigue dependiendo parcialmente
del monolito.
