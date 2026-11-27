# Arranque de SIGRH con Docker Compose

## 1. Objetivo

Ejecutar la interfaz SIGRH, cuatro microservicios
Django y cuatro bases PostgreSQL mediante
Docker Compose.

## 2. Componentes

| Componente | Responsabilidad |
|---|---|
| gateway | Entrada HTTP con Nginx |
| web | Interfaz SIGRH |
| usuarios | Identidad y empleados |
| reclutamiento | Vacantes y candidatos |
| vacaciones | Solicitudes y autorizaciones |
| nomina | Cálculos de nómina |

Cada microservicio tiene una base PostgreSQL propia.

## 3. Comunicación

El navegador utiliza la entrada HTTP de Nginx.

Nginx envía las peticiones web a SIGRH.

La interfaz SIGRH consulta las APIs internas
mediante HTTP.

Los microservicios utilizan nombres de servicio
proporcionados por el DNS interno de Docker.

## 4. Persistencia

Los datos de PostgreSQL se almacenan en
volúmenes Docker persistentes.

El entorno actual reutiliza los volúmenes
de los cuatro servicios previamente creados.

El monolito utiliza un archivo SQLite local
montado como volumen para conservar sus sesiones
y usuarios durante la transición.

## 5. Preparación

Comprobar que Docker Desktop esté funcionando.

Verificar que existan:

- El `.env` de SIGRH.
- Los `.env` de los cuatro microservicios.
- El archivo `db.sqlite3` original.
- Los cuatro volúmenes PostgreSQL existentes.

Los archivos privados no deben publicarse
en GitHub.

## 6. Arranque

Desde la raíz:

```powershell
python scripts/preparar_compose.py
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

## 7. Acceso

Interfaz principal:

http://127.0.0.1:8080/

Endpoints de salud:

- http://127.0.0.1:8080/salud/usuarios
- http://127.0.0.1:8080/salud/reclutamiento
- http://127.0.0.1:8080/salud/vacaciones
- http://127.0.0.1:8080/salud/nomina

## 8. Diagnóstico

Ver los contenedores:

```powershell
docker compose ps
```

Consultar registros de un servicio:

```powershell
docker compose logs --tail=50 usuarios
```

Consultar registros de la interfaz:

```powershell
docker compose logs --tail=50 web
```

Consultar registros del gateway:

```powershell
docker compose logs --tail=50 gateway
```

## 9. Manejo de fallas

Las solicitudes HTTP cuentan con tiempos máximos
de espera configurados en los clientes Python.

Cuando un servicio no responde, las vistas web
muestran errores o mensajes de indisponibilidad
según la operación.

La recuperación automática de eventos pendientes
requiere mensajería asíncrona y se implementará
como una etapa independiente.

## 10. Apagado

Para detener los contenedores:

```powershell
docker compose down
```

No utilizar `down -v` porque podría eliminar
volúmenes administrados por Compose.

Los volúmenes PostgreSQL actuales son externos
y deben conservarse.
