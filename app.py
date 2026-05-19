from flask import Flask, render_template, request, redirect
from neo4j import GraphDatabase

app = Flask(__name__)

# 🔹 CONEXIÓN NEO4J AURA
driver = GraphDatabase.driver(
    "neo4j+s://c47fef96.databases.neo4j.io",
    auth=(
        "neo4j",
        "ueWoDr4tsrOoPVmsS6vbItFPBLT-pG9oxOvzxJJW9Rw"
    )
)

# 🔹 PÁGINA PRINCIPAL
@app.route("/")
def inicio():

    with driver.session() as session:

        resultado = session.run("""
        MATCH (p:Producto)
        RETURN p.nombre AS nombre,
               p.categoria AS categoria,
               p.precio AS precio,
               p.cantidad AS cantidad,
               p.marca AS marca
        """)

        datos = []

        total = 0
        bajos = 0

        for p in resultado:

            producto = {
                "nombre": p["nombre"],
                "categoria": p["categoria"],
                "precio": p["precio"],
                "cantidad": p["cantidad"],
                "marca": p["marca"]
            }

            datos.append(producto)

            total += float(p["precio"]) * int(p["cantidad"])

            if int(p["cantidad"]) < 5:
                bajos += 1

    return render_template(
        "index.html",
        datos=datos,
        total=total,
        bajos=bajos
    )


# 🔹 AGREGAR PRODUCTO
@app.route("/agregar", methods=["POST"])
def agregar():

    nombre = request.form["producto"]
    categoria = request.form["categoria"]
    precio = float(request.form["precio"])
    cantidad = int(request.form["cantidad"])
    marca = request.form["marca"]

    with driver.session() as session:

        session.run("""
        CREATE (p:Producto {
            nombre:$nombre,
            categoria:$categoria,
            precio:$precio,
            cantidad:$cantidad,
            marca:$marca
        })
        """,

        nombre=nombre,
        categoria=categoria,
        precio=precio,
        cantidad=cantidad,
        marca=marca)

    return redirect("/")


# 🔹 ACTUALIZAR PRODUCTO
@app.route("/actualizar", methods=["POST"])
def actualizar():

    nombre = request.form["producto"]

    with driver.session() as session:

        session.run("""
        MATCH (p:Producto {nombre:$nombre})

        SET p.categoria=$categoria,
            p.precio=$precio,
            p.cantidad=$cantidad,
            p.marca=$marca
        """,

        nombre=nombre,
        categoria=request.form["categoria"],
        precio=float(request.form["precio"]),
        cantidad=int(request.form["cantidad"]),
        marca=request.form["marca"])

    return redirect("/")


# 🔹 ELIMINAR PRODUCTO
@app.route("/eliminar/<nombre>")
def eliminar(nombre):

    with driver.session() as session:

        session.run("""
        MATCH (p:Producto {nombre:$nombre})
        DETACH DELETE p
        """, nombre=nombre)

    return redirect("/")


# 🔹 EJECUTAR APP
if __name__ == "__main__":
    app.run(debug=True)