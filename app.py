from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from neo4j import GraphDatabase

app = Flask(__name__)

# 🔹 MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["Tienda_de_Abarrotes"]
coleccion = db["productos"]

# 🔹 Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "Fernanda0204")
)

# 🔹 Página principal
@app.route("/")
def inicio():

    # OBTENER PRODUCTOS
    datos = list(coleccion.find())

    # 💰 TOTAL INVENTARIO
    total = 0

    for p in datos:

        precio = float(p.get("precio", 0))
        cantidad = int(p.get("cantidad", 0))

        total += precio * cantidad

    # ⚠ PRODUCTOS CON BAJO STOCK
    bajos = 0

    for p in datos:

        if int(p.get("cantidad", 0)) < 5:
            bajos += 1

    return render_template(
        "index.html",
        datos=datos,
        total=total,
        bajos=bajos
    )


# 🔹 Agregar producto
@app.route("/agregar", methods=["POST"])
def agregar():

    nombre = request.form["producto"]
    categoria = request.form["categoria"]
    precio = float(request.form["precio"])
    cantidad = int(request.form["cantidad"])
    marca = request.form["marca"]

    # MongoDB
    coleccion.insert_one({
        "nombre": nombre,
        "categoria": categoria,
        "precio": precio,
        "cantidad": cantidad,
        "marca": marca
    })

    # Neo4j
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


# 🔹 Actualizar producto
@app.route("/actualizar", methods=["POST"])
def actualizar():

    nombre = request.form["producto"]

    # MongoDB
    coleccion.update_one(

        {"nombre": nombre},

        {"$set": {
            "categoria": request.form["categoria"],
            "precio": float(request.form["precio"]),
            "cantidad": int(request.form["cantidad"]),
            "marca": request.form["marca"]
        }}

    )

    # Neo4j
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


# 🔹 Eliminar producto
@app.route("/eliminar/<nombre>")
def eliminar(nombre):

    # MongoDB
    coleccion.delete_one({"nombre": nombre})

    # Neo4j
    with driver.session() as session:

        session.run("""
        MATCH (p:Producto {nombre:$nombre})
        DETACH DELETE p
        """, nombre=nombre)

    return redirect("/")


# 🔥 SINCRONIZAR Mongo → Neo4j
@app.route("/sincronizar")
def sincronizar():

    productos = list(coleccion.find())

    with driver.session() as session:

        # BORRAR TODO
        session.run("MATCH (n:Producto) DETACH DELETE n")

        # INSERTAR DE NUEVO
        for p in productos:

            nombre = p.get("nombre")

            if nombre and str(nombre).strip():

                session.run("""
                MERGE (n:Producto {nombre:$nombre})

                SET n.categoria=$categoria,
                    n.precio=$precio,
                    n.cantidad=$cantidad,
                    n.marca=$marca
                """,

                nombre=nombre,
                categoria=p.get("categoria"),
                precio=p.get("precio"),
                cantidad=p.get("cantidad"),
                marca=p.get("marca"))

            else:
                print("⚠️ Producto inválido:", p)

    return redirect("/")


# 🔹 Ejecutar app
if __name__ == "__main__":
    app.run(debug=True)