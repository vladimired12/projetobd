from app import app, db
from models2 import Filme, Sessao, Hora, Categoria_Ingresso, Produto
from flask import render_template, redirect, request, url_for
from helpers import FormIngresso
from funcs import verifica_ingressos, insert_ingresso, verifica_produtos, insert_produtos
import datetime

@app.route("/")
def index():
     q = f'select * from verfilme'
     filmes = db.session.execute(q)

     return render_template('index.html', filmes=filmes)


@app.route("/sessoes/<int:idFilme>")
def sessoes(idFilme):
     filme = Filme.query.filter_by(idFilme=idFilme).first()
     dia = f"'{datetime.date.today()}'"
     q = f'select * from versessao \
          WHERE versessao."idFilme" = {idFilme} and versessao."dia" >= {dia} and versessao."disponibilidade" > 0'

     sessoes = db.session.execute(q)
     return render_template('sessoes.html', sessao_filme=sessoes, filme=filme, Hora=Hora)


@app.route("/compraringresso/<int:idSessao>%<int:idFilme>")
def comprarIngresso(idSessao,idFilme):
     form = FormIngresso()
     
     sessao = Sessao.query.filter_by(idSessao=idSessao).first()
     filme = Filme.query.filter_by(idFilme=idFilme).first()
     tipo_ingresso = Categoria_Ingresso.query.order_by(Categoria_Ingresso.idCategoria)
     
     return render_template('ingresso.html', sessao=sessao, filme=filme, tipos=tipo_ingresso, form=form)


#ESTA e UMA URL INTERMEDIARIA
@app.route("/venda_ingresso/<int:idSessao>", methods=['POST','GET'])
def venda_ingresso(idSessao):

     form = FormIngresso(request.form)
     preco = Sessao.query.filter_by(idSessao=idSessao)
     preco_sessao = 0

     for i in preco:
          if(i.idSessao == idSessao):
               preco_sessao = float(i.valor)
     
     if not verifica_ingressos(form.data, idSessao):
          return redirect(url_for('index'))
     else:
          id_venda = insert_ingresso(form.data, idSessao, preco_sessao)

     return redirect(url_for('comprar_produto', id_venda=id_venda))


@app.route("/comprar_produto/<int:id_venda>")
def comprar_produto(id_venda):
     produtos = Produto.query.order_by(Produto.idProduto)
     return render_template('produto.html', produtos=produtos, id_venda=id_venda)


@app.route("/venda_produto/<int:id_venda>", methods=['POST','GET'])
def venda_produto(id_venda):
     form = request.form

     if verifica_produtos(form):
          insert_produtos(form,id_venda)
     else:
          redirect(url_for('comprar_produto', id_venda=id_venda))

     return redirect(url_for('finalizar_venda', id_venda=id_venda))


@app.route("/finalizar_venda/<int:id_venda>")
def finalizar_venda(id_venda):

     q1 = f'SELECT iv."idVenda", iv."idIngresso", iv.preco, iv."fkCategoria", v.nome, v.numero_da_sala, v.experiencia, v.formato, v.idioma, v.dia, v.horario FROM (SELECT vi."idVenda", i.* FROM "Venda_Ingresso" vi \
          INNER JOIN "Ingresso" i  ON vi."idIngresso"  = i."idIngresso" WHERE vi."idVenda" = {id_venda}) \
          AS iv INNER JOIN versessao v \
          ON iv."fkSessao" = v."idSessao"'
     
     q2 = f'SELECT * FROM (SELECT * FROM "Venda_Produto" vp \
          INNER JOIN "Produto" p ON vp."idproduto"  = p."idProduto" WHERE vp."idVenda" = {id_venda}) as produto_venda'

     venda_ingressos = db.session.execute(q1)
     venda_produtos = db.session.execute(q2)

     return render_template('venda.html', venda_ingressos=venda_ingressos, venda_produtos=venda_produtos, id_venda=id_venda)


@app.route("/cancelar_venda/<int:id_venda>", methods=['POST','GET'])
def cancelar_venda(id_venda):

     delete = f'delete from "Ingresso" where "idIngresso" in (select vi."idIngresso" from "Venda_Ingresso" vi where "idVenda" = {id_venda}); \
                 delete from "Venda" where "idVenda" = {id_venda};'
     
     db.session.execute(delete)
     db.session.commit()

     return redirect(url_for("index"))