from pathlib import Path

from dotenv import dotenv_values, set_key


# Raíz del repositorio SIGRH.
RAIZ = Path(__file__).resolve().parent.parent

# Archivo privado que Docker Compose lee automáticamente.
ENV_RAIZ = RAIZ / ".env"

SERVICIOS = {
    "Reclutamiento": (
        "reclutamiento_service",
        "RECL",
    ),
    "Usuarios": (
        "usuarios_service",
        "USU",
    ),
    "Vacaciones": (
        "vacaciones_service",
        "VAC",
    ),
    "Nómina": (
        "nomina_service",
        "NOM",
    ),
}


def preparar():
    if not ENV_RAIZ.is_file():
        raise SystemExit(
            "ERROR: falta el archivo .env de SIGRH."
        )

    for nombre, (carpeta, prefijo) in SERVICIOS.items():
        ruta = RAIZ / "servicios" / carpeta / ".env"

        if not ruta.is_file():
            raise SystemExit(
                f"ERROR: falta el .env de {nombre}."
            )

        origen = dotenv_values(ruta)

        claves = [
            f"{prefijo}_DB_NAME",
            f"{prefijo}_DB_USER",
            f"{prefijo}_DB_PASSWORD",
        ]

        for clave in claves:
            valor = origen.get(clave)

            if not valor:
                raise SystemExit(
                    f"ERROR: falta {clave} en {nombre}."
                )

        for clave in claves:
            set_key(
                str(ENV_RAIZ),
                clave,
                origen[clave],
            )

        print(f"OK: {nombre}")

    print("Configuración de Compose preparada.")
    print("No se modificaron las bases de datos.")


if __name__ == "__main__":
    preparar()
