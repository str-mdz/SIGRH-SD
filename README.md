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


## Instalación desde cero

### Requisitos

- Docker Desktop con motor Linux funcionando.
- Docker Compose.
- Python 3.12 o superior.
- Puertos 8080 y 15672 disponibles.

### 1. Clonar el proyecto

```powershell
git clone -b distribucion https://github.com/str-mdz/SIGRH-SD.git
cd SIGRH-SD
```

### 2. Preparar el entorno

```powershell
python scripts/inicializar_entorno.py
```

El script genera los archivos privados de configuración,
crea SQLite si falta y prepara los volúmenes de PostgreSQL.


### 3. Levantar SIGRH

```powershell
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

### 4. Crear los usuarios administradores iniciales

La interfaz web y Usuarios utilizan
almacenamientos de identidad separados.

Crear primero un administrador para la interfaz:

```powershell
docker compose exec web python manage.py createsuperuser
```

Crear después un administrador en Usuarios:

```powershell
docker compose exec usuarios python manage.py createsuperuser
```

Para una instalación nueva, utilizar el mismo identificador
y crear ambos como primeros usuarios.

### 5. Verificar la instalación

```powershell
python scripts/verificar_sigrh.py
```

### 6. Abrir el sistema

Interfaz SIGRH:
http://127.0.0.1:8080/

RabbitMQ Management:
http://127.0.0.1:15672/

El usuario de RabbitMQ es `sigrh`.
Su contraseña se genera en el archivo .env de la raíz.

### Apagar el sistema

```powershell
docker compose down
```

No usar `down -v`.

## Arquitectura

SIGRH utiliza cuatro microservicios Django:

- Usuarios
- Reclutamiento
- Vacaciones
- Nómina

Cada servicio administra su base PostgreSQL.

Nginx actúa como gateway y distribuye solicitudes
entre dos instancias del servicio Usuarios.

Docker Compose proporciona una red interna y DNS.

RabbitMQ permite comunicar Vacaciones con Nómina
mediante eventos asíncronos, Transactional Outbox,
reintentos, DLQ e idempotencia básica.

## Limitaciones

La autenticación web utiliza SQLite.

La creación de empleados no se sincroniza
automáticamente entre SQLite y Usuarios.

El balanceo se ha demostrado en las rutas de Usuarios
publicadas por Nginx, no en todas las llamadas internas.

Esta es una implementación académica para desarrollo local.
No debe exponerse a Internet sin reforzar su seguridad.

## Documentación

- docs/ARRANQUE_DOCKER.md
- docs/DECISIONES_ARQUITECTURA.md
- docs/reporte-final.pdf


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
