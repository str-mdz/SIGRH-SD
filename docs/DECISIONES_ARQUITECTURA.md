
# Decisiones de arquitectura de SIGRH

## 1. Separación en cuatro microservicios

**Decisión:** separar Usuarios, Reclutamiento,
Vacaciones y Nómina.

**Alternativa descartada:** mantener toda la lógica
y los datos en un único monolito.

**Motivo:** permitir que cada módulo evolucione y
gestione sus datos de forma independiente.

**Costo:** mayor complejidad de despliegue y
comunicación entre componentes.

## 2. Bases de datos independientes

**Decisión:** PostgreSQL por microservicio.

**Alternativa descartada:** una base PostgreSQL
compartida por todos.

**Motivo:** reducir el acoplamiento entre servicios.

**Costo:** no se pueden utilizar transacciones SQL
directas entre todos los servicios.

## 3. HTTP y RabbitMQ

**Decisión:** utilizar HTTP para consultas inmediatas
y RabbitMQ para eventos asíncronos.

**Alternativa descartada:** resolver toda la
comunicación mediante peticiones HTTP síncronas.

**Motivo:** permitir que las operaciones de Vacaciones
no dependan de la disponibilidad inmediata de Nómina.

**Costo:** aceptar consistencia eventual y posibles
entregas repetidas.

**Mitigación:** Transactional Outbox e idempotencia.

## 4. Gateway y balanceo

**Decisión:** utilizar Nginx como entrada HTTP.

**Alternativa descartada:** publicar directamente
todos los servicios al navegador.

**Motivo:** centralizar las rutas y distribuir
peticiones entre réplicas de Usuarios.

**Limitación observada:** durante la caída de una
réplica apareció un error HTTP 504 transitorio.
El tráfico posterior se atendió con la otra
instancia y el balanceo se recuperó.

## 5. Manejo de mensajes fallidos

**Decisión:** utilizar tres reintentos y una DLQ.

**Alternativa descartada:** descartar inmediatamente
los mensajes que no pudieran procesarse.

**Motivo:** conservar evidencia de los errores
y permitir su revisión posterior.

**Prueba realizada:** un mensaje inválido pasó
por reintentos de 5, 15 y 45 segundos y terminó
en la DLQ.

## 6. Limitaciones

- Autenticación web parcialmente centralizada.
- Empleados sin sincronización automática completa.
- Balanceo limitado a determinadas rutas HTTP.
