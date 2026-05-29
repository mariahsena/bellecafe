from flask import Flask, render_template, request, redirect, session
import sqlite3

from datetime import datetime

from flask_socketio import SocketIO

import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "segredo"

socketio = SocketIO(app)


def conectar():
    return sqlite3.connect("cafeteria.db")


# =========================
# LOGIN
# =========================

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email, senha))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['usuario'] = user[1]
        return redirect('/dashboard')
    return "Login inválido"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# =========================
# DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM clientes")
    clientes = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM vendas")
    vendas = cursor.fetchone()[0]

    conn.close()

    return render_template('dashboard.html', p=produtos, c=clientes, v=vendas)

# =========================
# PRODUTOS
# =========================

@app.route('/produtos')
def produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos")
    dados = cursor.fetchall()
    conn.close()
    return render_template('produtos.html', produtos=dados)

@app.route('/produtos/novo')
def novo_produto():
    return render_template('novo_produto.html')

@app.route('/produtos/salvar', methods=['POST'])
def salvar_produto():

    nome = request.form['nome']
    categoria = request.form['categoria']
    preco = request.form['preco']
    estoque = request.form['estoque']

    imagem = request.files['imagem']

    nome_imagem = secure_filename(imagem.filename)

    imagem.save("static/img/" + nome_imagem)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO produtos
        (nome, categoria, preco, estoque, imagem)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            nome,
            categoria,
            preco,
            estoque,
            nome_imagem
        )
    )

    conn.commit()
    conn.close()

    return redirect('/produtos')

@app.route('/produtos/editar/<int:id>')
def editar_produto(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id=?", (id,))
    produto = cursor.fetchone()
    conn.close()
    return render_template('editar_produto.html', produto=produto)

@app.route('/produtos/atualizar/<int:id>', methods=['POST'])
def atualizar_produto(id):

    nome = request.form['nome']
    categoria = request.form['categoria']
    preco = request.form['preco']
    estoque = request.form['estoque']

    imagem = request.files['imagem']

    conn = conectar()
    cursor = conn.cursor()

    # pega imagem antiga
    cursor.execute(
        "SELECT imagem FROM produtos WHERE id=?",
        (id,)
    )

    imagem_antiga = cursor.fetchone()[0]

    nome_imagem = imagem_antiga

    # se enviou nova imagem
    if imagem.filename != "":

        # apaga antiga
        caminho = "static/img/" + imagem_antiga

        if os.path.exists(caminho):

            os.remove(caminho)

        nome_imagem = secure_filename(imagem.filename)

        imagem.save("static/img/" + nome_imagem)

    cursor.execute(
        """
        UPDATE produtos
        SET nome=?, categoria=?, preco=?, estoque=?, imagem=?
        WHERE id=?
        """,
        (
            nome,
            categoria,
            preco,
            estoque,
            nome_imagem,
            id
        )
    )

    conn.commit()
    conn.close()

    return redirect('/produtos')

@app.route('/produtos/deletar/<int:id>')
def deletar_produto(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT imagem FROM produtos WHERE id=?",
        (id,)
    )

    imagem = cursor.fetchone()[0]

    caminho = "static/img/" + imagem

    if os.path.exists(caminho):

        os.remove(caminho)

    cursor.execute(
        "DELETE FROM produtos WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/produtos')

# =========================
# CLIENTES
# =========================

@app.route('/clientes')
def clientes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    dados = cursor.fetchall()
    conn.close()
    return render_template('clientes.html', clientes=dados)

@app.route('/clientes/novo')
def novo_cliente():
    return render_template('novo_cliente.html')

@app.route('/clientes/salvar', methods=['POST'])
def salvar_cliente():
    dados = request.form
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO clientes (nome, email, telefone) VALUES (?, ?, ?)",
        (dados['nome'], dados['email'], dados['telefone'])
    )

    conn.commit()
    conn.close()

    return redirect('/clientes')

@app.route('/clientes/editar/<int:id>')
def editar_cliente(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM clientes WHERE id=?",
        (id,)
    )

    cliente = cursor.fetchone()

    conn.close()

    return render_template(
        'editar_cliente.html',
        cliente=cliente
    )

@app.route('/clientes/atualizar/<int:id>', methods=['POST'])
def atualizar_cliente(id):

    nome = request.form['nome']
    email = request.form['email']
    telefone = request.form['telefone']

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE clientes
        SET nome=?, email=?, telefone=?
        WHERE id=?
        """,
        (nome, email, telefone, id)
    )

    conn.commit()
    conn.close()

    return redirect('/clientes')

@app.route('/clientes/deletar/<int:id>')
def deletar_cliente(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM clientes WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/clientes')

# =========================
# VENDAS
# =========================

@app.route('/vendas')
def vendas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""

    SELECT
        vendas.id,
        clientes.nome,
        vendas.data,
        vendas.total

    FROM vendas

    INNER JOIN clientes
    ON vendas.cliente_id = clientes.id

    """)

    dados = cursor.fetchall()

    conn.close()

    return render_template(
        'vendas.html',
        vendas=dados
    )


@app.route('/vendas/nova')
def nova_venda():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    conn.close()

    return render_template('nova_venda.html', clientes=clientes, produtos=produtos)

@app.route('/vendas/salvar', methods=['POST'])
def salvar_venda():

    cliente_id = request.form['cliente_id']
    produto_id = request.form['produto_id']
    quantidade = int(request.form['quantidade'])

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT preco, estoque FROM produtos WHERE id=?",
        (produto_id,)
    )

    produto = cursor.fetchone()

    preco = produto[0]
    estoque = produto[1]

    if quantidade > estoque:

        conn.close()

        return "Estoque insuficiente"

    total = preco * quantidade

    data = datetime.now().strftime("%d/%m/%Y")

    cursor.execute(
    """
    INSERT INTO vendas (cliente_id, data, total)
    VALUES (?, date('now'), ?)
    """,
    (cliente_id, total)
)
    venda_id = cursor.lastrowid

    cursor.execute(
        """
        INSERT INTO itens_venda
        (venda_id, produto_id, quantidade, preco_unit)
        VALUES (?, ?, ?, ?)
        """,
        (
            venda_id,
            produto_id,
            quantidade,
            preco
        )
    )

    cursor.execute(
        """
        UPDATE produtos
        SET estoque=?
        WHERE id=?
        """,
        (
            estoque - quantidade,
            produto_id
        )
    )

    conn.commit()
    conn.close()

    return redirect('/vendas')

@app.route('/vendas/deletar/<int:id>')
def deletar_venda(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM vendas WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/vendas')


@app.route('/vendas/editar/<int:id>')
def editar_venda(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM vendas WHERE id=?",
        (id,)
    )

    venda = cursor.fetchone()

    cursor.execute(
        """
        SELECT produto_id, quantidade
        FROM itens_venda
        WHERE venda_id=?
        """,
        (id,)
    )

    item = cursor.fetchone()

    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    conn.close()

    return render_template(
        'editar_venda.html',
        venda=venda,
        item=item,
        clientes=clientes,
        produtos=produtos
    )


@app.route('/vendas/atualizar/<int:id>', methods=['POST'])
def atualizar_venda(id):

    cliente_id = request.form['cliente_id']
    produto_id = request.form['produto_id']
    quantidade = int(request.form['quantidade'])

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT preco FROM produtos WHERE id=?",
        (produto_id,)
    )

    preco = float(cursor.fetchone()[0])

    total = round(preco * quantidade, 2)

    # atualiza venda
    cursor.execute(
        """
        UPDATE vendas
        SET cliente_id=?, total=?
        WHERE id=?
        """,
        (cliente_id, total, id)
    )

    # atualiza item venda
    cursor.execute(
        """
        UPDATE itens_venda
        SET produto_id=?, quantidade=?, preco_unit=?
        WHERE venda_id=?
        """,
        (produto_id, quantidade, preco, id)
    )

    conn.commit()
    conn.close()

    return redirect('/vendas')

# =========================
# USUÁRIOS
# =========================

@app.route('/usuarios/novo')
def novo_usuario():
    return render_template('novo_usuario.html')


@app.route('/usuarios/salvar', methods=['POST'])
def salvar_usuario():

    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO usuarios (nome, email, senha)
        VALUES (?, ?, ?)
        """,
        (nome, email, senha)
    )

    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/usuarios')
def usuarios():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios")

    dados = cursor.fetchall()

    conn.close()

    return render_template('usuarios.html', usuarios=dados)

@app.route('/usuarios/deletar/<int:id>')
def deletar_usuario(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect('/usuarios')

@app.route('/usuarios/editar/<int:id>')
def editar_usuario(id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id=?", (id,))

    usuario = cursor.fetchone()

    conn.close()

    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/usuarios/atualizar/<int:id>', methods=['POST'])
def atualizar_usuario(id):

    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE usuarios
        SET nome=?, email=?, senha=?
        WHERE id=?
        """,
        (nome, email, senha, id)
    )

    conn.commit()
    conn.close()

    return redirect('/usuarios')


if __name__ == '__main__':

    socketio.run(app, debug=True)