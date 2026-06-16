from flask import Flask, render_template, request, redirect, session, flash
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from urllib.parse import quote
 
app = Flask(__name__)
 
app.config['SECRET_KEY'] = 'perfumetester4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///perfumes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
from models import *
 
db.init_app(app)
 
 
# ════════════════════════════════════════════════════════════
#  RUTAS PÚBLICAS
# ════════════════════════════════════════════════════════════
 
@app.route('/')
def inicio():
    busqueda = request.args.get('buscar', '')
 
    if busqueda:
        todos = Perfume.query.filter(Perfume.nombre.contains(busqueda)).all()
        nicho     = [p for p in todos if p.categoria == 'Nicho']
        diseñador = [p for p in todos if p.categoria == 'Diseñador']
        arabes    = [p for p in todos if p.categoria == 'Arabes']
        tester    = [p for p in todos if p.categoria == 'Tester']
        decant    = [p for p in todos if p.categoria == 'Decant']
    else:
        nicho     = Perfume.query.filter_by(categoria='Nicho').all()
        diseñador = Perfume.query.filter_by(categoria='Diseñador').all()
        arabes    = Perfume.query.filter_by(categoria='Arabes').all()
        tester    = Perfume.query.filter_by(categoria='Tester').all()
        decant    = Perfume.query.filter_by(categoria='Decant').all()
 
    carrito = session.get('carrito', {})
    cantidad_carrito = sum(carrito.values())
 
    return render_template(
        'index.html',
        nicho=nicho, diseñador=diseñador, arabes=arabes,
        tester=tester, decant=decant,
        cantidad_carrito=cantidad_carrito,
        busqueda=busqueda
    )
 
 
@app.route('/perfume/<int:id>')
def detallePerfume(id):
    perfume = Perfume.query.get_or_404(id)
    carrito = session.get('carrito', {})
    cantidad_carrito = sum(carrito.values())
    return render_template('perfume.html', perfume=perfume, cantidad_carrito=cantidad_carrito)
 
 
# ════════════════════════════════════════════════════════════
#  CARRITO
# ════════════════════════════════════════════════════════════
 
@app.route('/agregar_carrito/<int:id>')
def agregarCarrito(id):
    if 'carrito' not in session:
        session['carrito'] = {}
    carrito = session['carrito']
    carrito[str(id)] = carrito.get(str(id), 0) + 1
    session['carrito'] = carrito
    return redirect('/')
 
 
@app.route('/eliminar_carrito/<int:id>')
def eliminarCarrito(id):
    carrito = session.get('carrito', {})
    key = str(id)
    if key in carrito:
        if carrito[key] > 1:
            carrito[key] -= 1
        else:
            del carrito[key]
    session['carrito'] = carrito
    return redirect('/carrito')
 
 
@app.route('/carrito')
def carrito():
    ids = session.get('carrito', {})
    perfumes = []
    total = 0
    for id_perfume, cantidad in ids.items():
        perfume = Perfume.query.get(int(id_perfume))
        if perfume is None:
            continue
        perfumes.append({
            'perfume': perfume,
            'cantidad': cantidad,
            'subtotal': perfume.precio * cantidad
        })
        total += perfume.precio * cantidad
    cantidad_carrito = sum(ids.values())
    return render_template('carrito.html', perfumes=perfumes, total=total, cantidad_carrito=cantidad_carrito)
 
 
@app.route('/finalizar_pedido')
def finalizarPedido():
    carrito = session.get('carrito', {})
    cantidad_carrito = sum(carrito.values())
    return render_template('finalizar_pedido.html', cantidad_carrito=cantidad_carrito)
 
 
@app.route('/enviar_whatsapp', methods=['POST'])
def enviarWhatsapp():
    cliente  = request.form['cliente']
    telefono = request.form['telefono']
    carrito  = session.get('carrito', {})
 
    mensaje  = "🛍️ Pedido - Tester Edition\n\n"
    mensaje += f"Cliente: {cliente}\n"
    mensaje += f"Telefono: {telefono}\n\n"
 
    total = 0
    for id_perfume, cantidad in carrito.items():
        perfume  = Perfume.query.get(int(id_perfume))
        subtotal = perfume.precio * cantidad
        total   += subtotal
        mensaje += f"{perfume.nombre} x{cantidad} - ${int(subtotal)}\n"
        perfume.stock -= cantidad
        if perfume.stock <= 0:
            perfume.stock   = 0
            perfume.agotado = True
 
    db.session.commit()
    mensaje += f"\nTOTAL: ${int(total)}"
    numero_negocio = "5492646315621"
    session.pop('carrito', None)
    return redirect(f"https://wa.me/{numero_negocio}?text={quote(mensaje)}")
 
 
# ════════════════════════════════════════════════════════════
#  ADMIN — LOGIN / LOGOUT
# ════════════════════════════════════════════════════════════
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        clave  = request.form['clave']
        admin  = Administrador.query.filter_by(correo=correo).first()
        if admin and admin.verificaClave(clave):
            session['admin'] = admin.id
            return redirect('/panel')
        flash('Datos incorrectos')
    return render_template('login.html', cantidad_carrito=0)
 
 
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')
 
 
# ════════════════════════════════════════════════════════════
#  ADMIN — PANEL
# ════════════════════════════════════════════════════════════
 
@app.route('/panel')
def panel():
    if 'admin' not in session:
        return redirect('/login')
    perfumes = Perfume.query.order_by(Perfume.categoria, Perfume.nombre).all()
    return render_template('panel_admin.html', perfumes=perfumes, cantidad_carrito=0)
 
 
@app.route('/agregar_perfume', methods=['GET', 'POST'])
def agregarPerfume():
    if 'admin' not in session:
        return redirect('/login')
 
    if request.method == 'POST':
        imagen = request.files['imagen']
        if not imagen or imagen.filename == '':
            flash('Tenés que elegir una imagen')
            return redirect('/agregar_perfume')
 
        nombre_imagen = secure_filename(imagen.filename)
        ruta = os.path.join(app.root_path, 'static', 'img')
        os.makedirs(ruta, exist_ok=True)
        imagen.save(os.path.join(ruta, nombre_imagen))
 
        perfume = Perfume(
            nombre       = request.form['nombre'],
            categoria    = request.form['categoria'],
            precio       = float(request.form['precio']),
            nota_salida  = request.form['salida'],
            nota_corazon = request.form['corazon'],
            nota_fondo   = request.form['fondo'],
            stock        = int(request.form['stock']),
            agotado      = False,
            imagen       = nombre_imagen
        )
        db.session.add(perfume)
        db.session.commit()
        return redirect('/panel')
 
    return render_template('agregar_perfume.html', cantidad_carrito=0)
 
 
@app.route('/editar_perfume/<int:id>', methods=['GET', 'POST'])
def editarPerfume(id):
    if 'admin' not in session:
        return redirect('/login')
 
    perfume = Perfume.query.get_or_404(id)
 
    if request.method == 'POST':
        perfume.nombre       = request.form['nombre']
        perfume.categoria    = request.form['categoria']
        perfume.precio       = float(request.form['precio'])
        perfume.nota_salida  = request.form['salida']
        perfume.nota_corazon = request.form['corazon']
        perfume.nota_fondo   = request.form['fondo']
        perfume.stock        = int(request.form['stock'])
        perfume.agotado      = perfume.stock <= 0
 
        # Imagen opcional — solo actualiza si se subió una nueva
        imagen = request.files.get('imagen')
        if imagen and imagen.filename != '':
            nombre_imagen = secure_filename(imagen.filename)
            ruta = os.path.join(app.root_path, 'static', 'img')
            os.makedirs(ruta, exist_ok=True)
            imagen.save(os.path.join(ruta, nombre_imagen))
            perfume.imagen = nombre_imagen
 
        db.session.commit()
        return redirect('/panel')
 
    return render_template('editar_perfume.html', perfume=perfume, cantidad_carrito=0)
 
 
@app.route('/eliminar_perfume/<int:id>')
def eliminarPerfume(id):
    if 'admin' not in session:
        return redirect('/login')
    perfume = Perfume.query.get_or_404(id)
    db.session.delete(perfume)
    db.session.commit()
    return redirect('/panel')
 
 
# ════════════════════════════════════════════════════════════
#  UTILIDADES
# ════════════════════════════════════════════════════════════
 
@app.route('/limpiar_sesion')
def limpiarSesion():
    session.clear()
    return redirect('/')
 
 
# ════════════════════════════════════════════════════════════
#  DATOS INICIALES
# ════════════════════════════════════════════════════════════
 
PERFUMES_INICIALES = [
    # ── TESTER (diseñador con tester) ─────────────────────────
    ("Toy Boy Moschino Tester 100ml",                 "Tester",   125000),
    ("Blue Jeans Tester 75ml",                        "Tester",    65000),
    ("Sauvage Dior EDP 100ml Tester",                 "Tester",   210000),
    ("Polo Red Parfum Tester 100ml",                  "Tester",   165000),
    ("Scandal Absolu Tester 100ml",                   "Tester",   185000),
    ("Versace Eros Najim Parfum Tester 100ml",        "Tester",   235000),
    ("Terre D'Hermes H24 Herbes Vives Tester 100ml",  "Tester",   190000),
    ("Carolina Herrera Bad Boy Extreme EDP Tester 100ml", "Tester", 165000),
    ("Acqua Di Gio Parfum Tester 100ml",              "Tester",   220000),
    ("La Nuit YSL Tester 100ml",                      "Tester",   165000),
    ("Gentleman Givenchy Reserve Privée Tester 100ml","Tester",   185000),
    ("Guerlain Habit Rouge Tester 100ml",             "Tester",   185000),
    ("Guerlain L'Homme Ideal Tester 100ml",           "Tester",   185000),
    ("Terre D'Hermes Tester 100ml",                   "Tester",   190000),
    ("Azzaro Forever Wanted Elixir Tester 100ml",     "Tester",   199500),
    ("One Million Elixir 100ml",                      "Tester",   210000),
    ("Dolce & Gabbana The One Tester 100ml",          "Tester",   140000),
    ("Dolce & Gabbana K Tester 100ml",                "Tester",   120000),
    # Tester de nicho
    ("Naxos Xerjoff Tester 100ml",                    "Tester",   400000),
    ("Naxos Erba Gold Tester 100ml",                  "Tester",   380000),
    ("Montale Paris Tester 100ml",                    "Tester",   150000),
    ("Mancera Wild Leather Tester 100ml",             "Tester",   180000),
    ("Montale Paris Boise Fruite Tester 100ml",       "Tester",   195000),
 
    # ── DISEÑADOR (sellados / regulares) ──────────────────────
    ("Ferrari 200ml",                                 "Diseñador",  70000),
    ("Calvin Klein Be 100ml Sellado",                 "Diseñador",  70000),
    ("CK Be 100ml",                                   "Diseñador",  80000),
    ("Burberry Hero Sellado 100ml",                   "Diseñador", 185000),
    ("Kenzo Home 100ml",                              "Diseñador", 165000),
    ("Invictus Parfum Sellado 200ml",                 "Diseñador", 250000),
    ("Kit Kenzo Homme EDT 110ml + Gel Sellado",       "Diseñador", 150000),
    ("Polo 67 Eau de Parfum Sellado 125ml",           "Diseñador", 210000),
    ("Calvin Klein One Sellado 200ml",                "Diseñador", 100000),
    ("Le Beau Le Parfum Sellado 125ml",               "Diseñador", 220000),
    ("Azzaro The Most Wanted Intense Sellado 100ml",  "Diseñador", 170000),
    ("Azzaro The Most Wanted Parfum Sellado 100ml",   "Diseñador", 175000),
    ("Valentino Uomo Born in Roma Sellado 100ml",     "Diseñador", 210000),
    ("Stronger With You Sellado 100ml",               "Diseñador", 220000),
 
    # ── NICHO (sellados / regulares) ──────────────────────────
    ("Mancera Cedrat Boise 120ml",                    "Nicho",     210000),
    ("Mancera Instant Crush 120ml",                   "Nicho",     205000),
    ("Montale Arabians Tonka 100ml",                  "Nicho",     235000),
 
    # ── ARABES ────────────────────────────────────────────────
    ("Mandarin Sky 100ml",                            "Arabes",     65000),
    ("Mandarin Sky Elixir 100ml",                     "Arabes",     90000),
    ("Club de Nuit Intense Man 100ml",                "Arabes",     70000),
    ("Club de Nuit Untold 105ml",                     "Arabes",     90000),
    ("Club de Nuit Woman 100ml",                      "Arabes",     70000),
    ("Al Haramain Acqua Dubai 100ml",                 "Arabes",    120000),
    ("Al Haramain Amber Oud 100ml",                   "Arabes",    120000),
    ("9PM 100ml",                                     "Arabes",     70000),
    ("9AM Dive 100ml",                                "Arabes",     80000),
    ("Lail Maleki Lattafa 100ml",                     "Arabes",     50000),
    ("Asad Zanzíbar Lattafa 100ml",                   "Arabes",     50000),
    ("Asad Clásico 100ml",                            "Arabes",     70000),
    ("Asad Bourbon 100ml",                            "Arabes",     70000),
    ("Yara Candid 100ml",                             "Arabes",     50000),
    ("Yara Rosa 100ml",                               "Arabes",     50000),
    ("Yara Tous 100ml",                               "Arabes",     50000),
    ("Muna Lattafa 100ml",                            "Arabes",     50000),
    ("Glacier Le Noir 100ml",                         "Arabes",     60000),
    ("Hercules 100ml",                                "Arabes",     50000),
    ("Sheikh Al Shuyukh Luke 100ml",                  "Arabes",     60000),
    ("La Rouge Baroque 100ml",                        "Arabes",     50000),
    ("Oud Mood 100ml",                                "Arabes",     50000),
    ("Kalos 100ml",                                   "Arabes",     50000),
    ("Shaheen Silver 100ml",                          "Arabes",     60000),
    ("Ethernal Oud 100ml",                            "Arabes",     70000),
    ("Qaed Al Fursan 90ml",                           "Arabes",     50000),
    ("Vintage Radio 100ml",                           "Arabes",     70000),
    ("His Confession 100ml",                          "Arabes",     80000),
    ("Her Confession 100ml",                          "Arabes",     80000),
    ("Fakhar Gold Extrait 100ml",                     "Arabes",     60000),
    ("Fakhar Black 100ml",                            "Arabes",     60000),
    ("Fakhar Rose 100ml",                             "Arabes",     60000),
    ("Jorge Di Profumo Aqua 100ml",                   "Arabes",     60000),
    ("Jorge Di Profumo Deep Blue 100ml",              "Arabes",     60000),
    ("Jean Lowe Fraiche 100ml",                       "Arabes",     50000),
    ("Jean Lowe Noir 100ml",                          "Arabes",     60000),
    ("Jean Lowe Immortel 100ml",                      "Arabes",     70000),
    ("Khanjar 100ml",                                 "Arabes",     90000),
    ("Vintage Castle 100ml",                          "Arabes",     95000),
    ("Ajwaa 100ml",                                   "Arabes",     60000),
    ("Maahir Black Edition 100ml",                    "Arabes",     50000),
    ("Maahir 100ml",                                  "Arabes",     60000),
    ("Shaheen Gold 100ml",                            "Arabes",     60000),
    ("So Candid Pour Homme 100ml",                    "Arabes",     50000),
    ("Hayaati Al Maleky 100ml",                       "Arabes",     50000),
    ("Hayaati Negro 100ml",                           "Arabes",     50000),
    ("Hayaati Gold Elixir 100ml",                     "Arabes",     60000),
    ("Haya 100ml",                                    "Arabes",     70000),
    ("Hayaam 100ml",                                  "Arabes",     60000),
    ("Khamrah 100ml",                                 "Arabes",     70000),
    ("Khamrah Qahwa 100ml",                           "Arabes",     70000),
    ("Oud for Glory 100ml",                           "Arabes",     60000),
    ("Amethyst 100ml",                                "Arabes",     60000),
    ("Sublime 100ml",                                 "Arabes",     70000),
    ("Honor & Glory 100ml",                           "Arabes",     70000),
    ("Glacier Ultra 100ml",                           "Arabes",     60000),
    ("Glacier Bella 100ml",                           "Arabes",     50000),
    ("Sakeena 100ml",                                 "Arabes",     70000),
    ("Your Touch Intense 100ml",                      "Arabes",     70000),
    ("Maison Alhambra Salvo 100ml",                   "Arabes",     50000),
    ("Maison Alhambra Salvo Elixir 60ml",             "Arabes",     45000),
    ("Maison Alhambra Salvo Intense 100ml",           "Arabes",     50000),
    ("Ishq Gold 100ml",                               "Arabes",     60000),
    ("The Kingdom 100ml",                             "Arabes",     75000),
    ("Ansaam Silver 100ml",                           "Arabes",     70000),
    ("Rayhaan Corium 100ml",                          "Arabes",     70000),
    ("Now Women 100ml",                               "Arabes",     65000),
    ("Reyna 100ml",                                   "Arabes",     60000),
    ("Alive Now 100ml",                               "Arabes",     50000),
    ("Your Touch for Women 100ml",                    "Arabes",     50000),
    ("Emman 100ml",                                   "Arabes",     65000),
    ("Eclaire 100ml",                                 "Arabes",     65000),
    ("Hayaati Florence 100ml",                        "Arabes",     60000),
    ("Delilah 100ml",                                 "Arabes",     50000),
    ("Philos Pura 100ml",                             "Arabes",     55000),
    ("Yeah 100ml",                                    "Arabes",     50000),
    ("Zimaya Sharaf Blend 100ml",                     "Arabes",     70000),
    ("La Voie 100ml",                                 "Arabes",     50000),
    ("9PM Rebel 100ml",                               "Arabes",     70000),
    ("Emeer 100ml",                                   "Arabes",     70000),
    ("Inta-Hayaati 100ml",                            "Arabes",     35000),
    ("9PM Elixir 100ml",                              "Arabes",     85000),
    ("Zimaya 100ml",                                  "Arabes",     60000),
    ("Dubai Chocolate 100ml",                         "Arabes",     65000),
    ("Odyssey White 100ml",                           "Arabes",     60000),
    ("Hawas Ice 100ml",                               "Arabes",     85000),
    ("Kit Yara 4 Perfumes 25ml",                      "Arabes",     70000),
    ("Elixir 88 120ml",                               "Arabes",     65000),
    ("Dark Door 100ml",                               "Arabes",     50000),
    ("Supreme 100ml",                                 "Arabes",     45000),
    ("Jean Lowe Vibe 100ml",                          "Arabes",     80000),
    ("Bharara King 100ml",                            "Arabes",     95000),
    ("Kit Bharara 7 Perfumes 10ml",                   "Arabes",     80000),
    ("Vulcan Feu 100ml",                              "Arabes",     85000),
    ("Turathi Blue 90ml",                             "Arabes",     80000),
    ("9PM Night Out 100ml",                           "Arabes",     90000),
    ("Ebene 100ml",                                   "Arabes",     50000),
    ("Sceptre 100ml",                                 "Arabes",     75000),
    ("Bareek 100ml",                                  "Arabes",     50000),
    ("Hawas Malibu 100ml",                            "Arabes",     85000),
]
 
 
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Admin
        if Administrador.query.count() == 0:
            admin = Administrador(
                correo='julian04aacosta@gmail.com',
                clave=generate_password_hash('PachuPerfumes')
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin creado.")
 
        # Perfumes iniciales (solo si la tabla está vacía)
        if Perfume.query.count() == 0:
            for nombre, categoria, precio in PERFUMES_INICIALES:
                p = Perfume(
                    nombre=nombre, categoria=categoria, precio=precio,
                    nota_salida='', nota_corazon='', nota_fondo='',
                    stock=1, agotado=False, imagen=None
                )
                db.session.add(p)
            db.session.commit()
            print(f"✅ {len(PERFUMES_INICIALES)} perfumes cargados.")
 
    app.run(host='0.0.0.0', port=5000)