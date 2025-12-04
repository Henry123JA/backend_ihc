import csv
from models import models
from core.auth import hash_password
from models.models import ProductoImagen  # ← Import correcto


def insertar_datos_iniciales(db):
    print("✅ Cargando datos iniciales...")

    # ===================================================
    # 🟦 1) PRODUCTOS
    # ===================================================
    with open("seeds/productos.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existente = db.query(models.Producto).filter_by(
                nombre=row["nombre"]
            ).first()

            if not existente:
                producto = models.Producto(
                    nombre=row["nombre"],
                    precio=float(row["precio"]),
                    descripcion=row["descripcion"]
                )
                db.add(producto)

    db.commit()  # IMPORTANTE: guardar antes de enlazar imágenes



    # ===================================================
    # 🟩 2) IMÁGENES DE PRODUCTO
    # ===================================================
    with open("seeds/imagenes.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:

            producto = db.query(models.Producto).filter_by(
                nombre=row["producto"]
            ).first()

            if not producto:
                print(f"⚠ Producto no encontrado para imagen: {row['producto']}")
                continue

            existente = db.query(ProductoImagen).filter_by(
                producto_id=producto.id,
                archivo=row["archivo"]
            ).first()

            if not existente:
                imagen = ProductoImagen(
                    producto_id=producto.id,
                    archivo=row["archivo"]
                )
                db.add(imagen)



    # ===================================================
    # 🚗 3) CONDUCTORES
    # ===================================================
    with open("seeds/conductores.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:

            existente = db.query(models.Conductor).filter_by(
                email=row["email"]
            ).first()

            if not existente:
                conductor = models.Conductor(
                    nombre=row["nombre"],
                    telefono=row["telefono"],
                    vehiculo=row["vehiculo"],
                    email=row["email"],
                    password_hash=hash_password(row["password"])
                )
                db.add(conductor)

    db.commit()
    print("🌱 Datos iniciales cargados correctamente.")
