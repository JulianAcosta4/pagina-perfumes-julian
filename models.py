from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
 
db = SQLAlchemy()
 
 
class Administrador(db.Model):
    __tablename__ = 'administrador'
 
    id = db.Column(db.Integer, primary_key=True)
 
    correo = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )
 
    clave = db.Column(
        db.String(255),
        nullable=False
    )
 
    def verificaClave(self, password):
        return check_password_hash(self.clave, password)
 
 
class Perfume(db.Model):
    __tablename__ = 'perfume'
 
    id = db.Column(db.Integer, primary_key=True)
 
    nombre = db.Column(db.String(100), nullable=False)
 
    categoria = db.Column(db.String(30), nullable=False)
 
    precio = db.Column(db.Float, nullable=False)
 
    nota_salida = db.Column(db.String(150))
 
    nota_corazon = db.Column(db.String(150))
 
    nota_fondo = db.Column(db.String(150))
 
    stock = db.Column(db.Integer, default=0)
 
    agotado = db.Column(db.Boolean, default=False)
 
    imagen = db.Column(db.String(200))
 
    detalles = db.relationship(
        'DetallePedido',
        backref='perfume',
        cascade='all, delete-orphan'
    )
 
    def disponible(self):
        return self.stock > 0 and not self.agotado
 
    def getPrecio(self):
        return self.precio
 
    def getNombre(self):
        return self.nombre
 
 
class Pedido(db.Model):
    __tablename__ = 'pedido'
 
    id = db.Column(db.Integer, primary_key=True)
 
    cliente = db.Column(db.String(100), nullable=False)
 
    telefono = db.Column(db.String(30), nullable=False)
 
    fecha = db.Column(db.DateTime, nullable=False)
 
    total = db.Column(db.Float, default=0)
 
    detalles = db.relationship(
        'DetallePedido',
        backref='pedido',
        cascade='all, delete-orphan'
    )
 
    def calcularTotal(self):
        total = 0
        for detalle in self.detalles:
            total += detalle.subtotal
        self.total = total
        return total
 
 
class DetallePedido(db.Model):
    __tablename__ = 'detallepedido'
 
    id = db.Column(db.Integer, primary_key=True)
 
    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey('pedido.id')
    )
 
    perfume_id = db.Column(
        db.Integer,
        db.ForeignKey('perfume.id')
    )
 
    cantidad = db.Column(db.Integer, nullable=False)
 
    subtotal = db.Column(db.Float, nullable=False)
 