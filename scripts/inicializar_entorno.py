from pathlib import Path
import secrets
import subprocess

RAIZ = Path(__file__).resolve().parent.parent

SERVICIOS = {
    "RECL": ("reclutamiento_service", "reclutamiento", "8001"),
    "USU": ("usuarios_service", "usuarios", "8002"),
    "VAC": ("vacaciones_service", "vacaciones", "8003"),
    "NOM": ("nomina_service", "nomina", "8004"),
}

VOLUMENES = [
    "reclutamiento_service_reclutamiento_pgdata",
    "usuarios_service_usuarios_pgdata",
    "vacaciones_service_vacaciones_pgdata",
    "nomina_service_nomina_pgdata",
]


def guardar_env(ruta, variables):
    ruta.parent.mkdir(parents=True, exist_ok=True)

    contenido = "".join(
        f"{clave}={valor}\n"
        for clave, valor in variables.items()
    )

    # El modo x evita sobrescribir archivos existentes.
    with ruta.open("x", encoding="utf-8") as archivo:
        archivo.write(contenido)


def preparar_variables():
    rutas = [RAIZ / ".env"]

    for carpeta, _, _ in SERVICIOS.values():
        rutas.append(
            RAIZ / "servicios" / carpeta / ".env"
        )

    existentes = [
        ruta for ruta in rutas if ruta.exists()
    ]

    if existentes:
        if len(existentes) != len(rutas):
            raise SystemExit(
                "Hay archivos .env incompletos. "
                "Revísalos antes de continuar."
            )

        print("OK: .env existentes conservados")
        return

    raiz = {
        "SIGRH_DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
        "RABBITMQ_PASSWORD": secrets.token_hex(24),
    }

    configuraciones = {}

    for prefijo, (_, nombre, puerto) in SERVICIOS.items():
        datos = {
            f"{prefijo}_DB_NAME": f"sigrh_{nombre}",
            f"{prefijo}_DB_USER": f"sigrh_{nombre}",
            f"{prefijo}_DB_PASSWORD": secrets.token_hex(24),
            f"{prefijo}_INTERNAL_TOKEN": secrets.token_urlsafe(32),
            f"{prefijo}_DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
        }

        raiz.update(datos)
        raiz[f"{prefijo}_API_URL"] = (
            f"http://127.0.0.1:{puerto}/api/"
        )

        configuraciones[prefijo] = datos

    # Vacaciones y Nómina deben poder consultar Usuarios.
    for prefijo in ("VAC", "NOM"):
        configuraciones[prefijo]["USU_INTERNAL_TOKEN"] = (
            raiz["USU_INTERNAL_TOKEN"]
        )
        configuraciones[prefijo]["USU_API_URL"] = (
            "http://127.0.0.1:8002/api/"
        )

    configuraciones["NOM"]["NOM_DB_HOST"] = "127.0.0.1"
    configuraciones["NOM"]["NOM_DB_PORT"] = "55435"

    guardar_env(rutas[0], raiz)

    for indice, prefijo in enumerate(SERVICIOS, start=1):
        guardar_env(
            rutas[indice],
            configuraciones[prefijo],
        )

    print("OK: cinco .env creados sin mostrar secretos")


def preparar_volumen(nombre):
    resultado = subprocess.run(
        ["docker", "volume", "inspect", nombre],
        capture_output=True,
        text=True,
        check=False,
    )

    if resultado.returncode == 0:
        print(f"OK: volumen existente {nombre}")
        return

    if "no such volume" not in resultado.stderr.lower():
        raise SystemExit(
            f"No se pudo comprobar {nombre}: "
            f"{resultado.stderr.strip()}"
        )

    subprocess.run(
        ["docker", "volume", "create", nombre],
        check=True,
    )

    print(f"OK: volumen creado {nombre}")


def main():
    preparar_variables()

    sqlite = RAIZ / "db.sqlite3"

    if not sqlite.exists():
        sqlite.touch()
        print("OK: SQLite vacío creado")
    else:
        print("OK: SQLite existente conservado")

    for nombre in VOLUMENES:
        preparar_volumen(nombre)

    print("Preparación del entorno completada")


if __name__ == "__main__":
    main()
