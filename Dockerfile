# Imagen base 
FROM python:3.13-slim

# Evita archivos temporales y muestra los logs inmediatamente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Instala las dependencias antes de copiar el proyecto
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia el código fuente del proyecto
COPY . /app


