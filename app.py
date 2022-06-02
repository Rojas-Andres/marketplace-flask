from flask import Flask, render_template, request, redirect, url_for, flash,session,jsonify, make_response
# from db.db import Session , engine,connection_db
from core.config import settings
from flask_sqlalchemy import SQLAlchemy
import csv
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean,DateTime
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import func

app = Flask(__name__)
app.config['SECRET_KEY']='Th1s1ss3cr3t'
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
engine = create_engine(settings.DATABASE_URL)

carrito = {}
class Producto(db.Model):
    __tablename__ = "producto"
    id_producto = db.Column(db.Integer,primary_key=True)
    codigo_producto = db.Column(db.String)
    nombre = db.Column(db.String)
    marca = db.Column(db.String)
    referencia = db.Column(db.String)
    precio = db.Column(db.Integer)
    cantidad = db.Column(db.Integer)
    pedido = relationship("Pedidos",backref="producto",cascade="delete,merge")

class Pedidos(db.Model):
    __tablename__="pedido"
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    id_pedido = db.Column(db.Integer)
    producto_id = db.Column(db.Integer,ForeignKey("producto.id_producto",ondelete="CASCADE"))
    cantidad = db.Column(db.Integer)
    precio_total = db.Column(db.Integer)

def create_tables():
    db.create_all()
def insertar_datos_productos():
    data = Producto.query.all()
    if len(data) == 0:
        with open("productos.csv") as archivo:
            datos = csv.reader(archivo,delimiter=",")
            for i in datos:
                prd = Producto(id_producto=i[0],codigo_producto=i[0],nombre=i[1],marca=i[2],referencia=i[3],precio=int(i[4]),cantidad=int(i[5]))        
                db.session.add(prd)
            db.session.commit()
    
create_tables()
insertar_datos_productos()

def get_all_prds():
    prds = Producto.query.all()
    return prds

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/productos', methods=['GET'])
def productos():
    prds = Producto.query.all()
    return render_template('productos.html',prds=get_all_prds())

@app.route('/producto/<id>',methods=["GET","POST"])
def ver_producto(id):
    prd = Producto.query.filter(Producto.id_producto==id).first()
    imagen = f"{prd.codigo_producto}.png"
    return render_template('producto.html',prd=prd,imagen=imagen)
@app.route('/carrito/eliminar/<id>',methods=["GET","POST"])
def eliminar_carrito(id):
    prd = Producto.query.filter(Producto.id_producto==id).first()
    prd.cantidad = prd.cantidad+carrito[id]["cantidad"]
    db.session.commit()
    carrito.pop(id)
    return render_template('index.html',mensaje=f"El producto {id} eliminado del carrito satisfactoriamente!")
    
@app.route('/carrito/adicionar/<id>',methods=["GET","POST"])
@app.route('/carrito/adicionar',methods=["GET","POST"])
def adicionar_carrito(id=None):
    if request.method=="POST":
        id_producto = int(request.form["id_producto"])
        cantidad = int(request.form["cantidad_prd"])
        prd = Producto.query.filter(Producto.id_producto==id_producto).first() 
        
        if cantidad > prd.cantidad:
            return render_template('productos.html',prds=get_all_prds(),mensaje=f"No puede agregar al carrito el \
            producto {id_producto} la cantidad solicitada({cantidad}) supera el stock actual {prd.cantidad}")
            
        if prd.codigo_producto in carrito:
            carrito[prd.codigo_producto]["cantidad"]+=cantidad
            nuevo_total = prd.precio * carrito[prd.codigo_producto]["cantidad"]
            carrito[prd.codigo_producto]["total"] = nuevo_total 
        else:
            carrito[prd.codigo_producto] = {
                "nombre":prd.nombre,
                "cantidad":cantidad,
                "precio":prd.precio,
                "total":prd.precio*cantidad
            }
        prd.cantidad = prd.cantidad - cantidad
        db.session.commit()    
        return render_template('productos.html',prds=get_all_prds(),mensaje=f"Producto {id_producto} con la cantidad \
        {cantidad} añadido satisfactoriamente")
    prd = Producto.query.filter(Producto.id_producto==id).first() 
    return render_template('add_carrito.html',prd=prd)

@app.route('/carrito',methods=["GET","POST"])
def ver_carrito():
    if len(carrito)==0:
        return render_template('index.html',mensaje="Aun no tiene nada en el carrito!")
    total_pagar = 0
    for i,j in carrito.items():
        print(j)
        total_pagar+=j["total"]
    print("asdasd sa total_pagar",total_pagar)
    return render_template('carrito.html',prds=carrito,total_pagar=total_pagar)
@app.route('/comprar',methods=["GET","POST"])
def comprar():
    global carrito
    a = db.session.query(func.max(Pedidos.id_pedido)).first()
    if a[0] is None:
        start = 1 
    else:
        start = a[0]+1
    
    for i,j in carrito.items():
        pedido = Pedidos(
            id_pedido = start ,
            producto_id=int(i),
            cantidad=j["cantidad"],
            precio_total=j["total"]
        )  
        db.session.add(pedido)
    db.session.commit()
    carrito = {}
    return render_template('index.html',mensaje=f"Felicitaciones por realizar la compra!!")

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0")