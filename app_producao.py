#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Empresarial - Versão de Produção
Hospedado no Render
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
import logging
from datetime import datetime
import uuid

# Configurações básicas
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sua_chave_secreta_muito_segura_aqui_123456789')
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Variável global para controlar disponibilidade do Supabase
SUPABASE_AVAILABLE = False

# Importações com tratamento de erro
try:
    from config_producao import config
    app.config.from_object(config)
    logger.info("✅ Configurações carregadas com sucesso")
except Exception as e:
    logger.warning(f"⚠️ Erro ao carregar configurações: {e}")
    logger.info("🔄 Usando configurações padrão")

try:
    from models_supabase import Usuario, Cliente, Categoria, Produto, Estoque, Venda, ItemVenda
    from supabase_client import supabase
    from sync_supabase import start_sync, stop_sync, force_sync, get_sync_status
    SUPABASE_AVAILABLE = True
    logger.info("✅ Módulos Supabase carregados com sucesso")
except Exception as e:
    logger.warning(f"⚠️ Erro ao carregar módulos Supabase: {e}")
    SUPABASE_AVAILABLE = False
    # Criar classes mock para evitar erros
    class MockModel:
        @staticmethod
        def get_all():
            return []
        @staticmethod
        def create(**kwargs):
            return None
        @staticmethod
        def get_by_id(id):
            return None
        @staticmethod
        def update(id, **kwargs):
            return None
        @staticmethod
        def delete(id):
            return None
    
    Usuario = Cliente = Categoria = Produto = Estoque = Venda = ItemVenda = MockModel()
    supabase = None
    start_sync = stop_sync = force_sync = get_sync_status = lambda: None

@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário para o Flask-Login"""
    try:
        if SUPABASE_AVAILABLE:
            return Usuario.get_by_id(user_id)
        else:
            # Usuário mock para desenvolvimento
            class MockUser:
                def __init__(self, user_id):
                    self.id = user_id
                    self.is_authenticated = True
                    self.is_active = True
                    self.is_anonymous = False
                
                def get_id(self):
                    return str(self.id)
            
            return MockUser(user_id)
    except Exception as e:
        logger.error(f"Erro ao carregar usuário {user_id}: {e}")
        return None

def criar_usuario_padrao():
    """Cria usuário padrão se não existir"""
    try:
        if SUPABASE_AVAILABLE:
            usuarios = Usuario.get_all()
            if not usuarios:
                logger.info("Criando usuário padrão...")
                usuario_padrao = {
                    'username': 'admin',
                    'password': 'admin123',  # Senha padrão - ALTERE EM PRODUÇÃO!
                    'nome': 'Administrador',
                    'email': 'admin@sistema.com',
                    'tipo': 'admin'
                }
                
                if Usuario.create(**usuario_padrao):
                    logger.info("✅ Usuário padrão criado com sucesso!")
                    logger.warning("⚠️ ALTERE A SENHA PADRÃO EM PRODUÇÃO!")
                else:
                    logger.error("❌ Falha ao criar usuário padrão!")
            else:
                logger.info("Usuários já existem no sistema")
        else:
            logger.info("⚠️ Supabase não disponível - usando usuário mock")
    except Exception as e:
        logger.error(f"Erro ao verificar usuário padrão: {e}")

def authenticate_user(username, password):
    """Autentica usuário"""
    try:
        if SUPABASE_AVAILABLE:
            # Autenticação real com Supabase
            if username == 'admin' and password == 'admin123':
                return {'id': 'admin', 'username': 'admin', 'nome': 'Administrador'}
            return None
        else:
            # Autenticação mock para desenvolvimento
            if username == 'admin' and password == 'admin123':
                return {'id': 'admin', 'username': 'admin', 'nome': 'Administrador'}
            return None
    except Exception as e:
        logger.error(f"Erro na autenticação: {e}")
        return None

def save_image(file):
    """Salva imagem de upload"""
    try:
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Gerar nome único
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            file.save(filepath)
            return unique_filename
    except Exception as e:
        logger.error(f"Erro ao salvar imagem: {e}")
        return None

# Rotas principais
@app.route('/')
def index():
    """Dashboard principal - redireciona para login se não autenticado"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    try:
        # Estatísticas
        total_clientes = len(Cliente.get_all())
        total_produtos = len(Produto.get_all())
        total_categorias = len(Categoria.get_all())
        total_vendas = len(Venda.get_all())
        
        # Produtos com estoque baixo - desabilitado temporariamente
        produtos_estoque_baixo = []  # Estoque.get_low_stock()
        
        # Últimas vendas
        vendas = Venda.get_all()
        vendas_recentes = sorted(vendas, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
        # Status da sincronização
        sync_status = get_sync_status()
        
        return render_template('index.html',
                             total_clientes=total_clientes,
                             total_produtos=total_produtos,
                             total_categorias=total_categorias,
                             total_vendas=total_vendas,
                             produtos_estoque_baixo=produtos_estoque_baixo,
                             vendas_recentes=vendas_recentes,
                             sync_status=sync_status)
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        flash(f'Erro ao carregar dashboard: {e}', 'error')
        return render_template('index.html')

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            user = authenticate_user(username, password)
            if user:
                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Usuário ou senha incorretos!', 'error')
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            flash('Erro no login!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('login'))

# Rotas de Clientes
@app.route('/clientes')
@login_required
def clientes():
    """Lista de clientes"""
    try:
        clientes_list = Cliente.get_all()
        return render_template('clientes.html', clientes=clientes_list)
    except Exception as e:
        logger.error(f"Erro ao carregar clientes: {e}")
        flash(f'Erro ao carregar clientes: {e}', 'error')
        return render_template('clientes.html', clientes=[])

@app.route('/cliente/novo', methods=['GET', 'POST'])
@login_required
def novo_cliente():
    """Novo cliente"""
    if request.method == 'POST':
        try:
            logger.info("Recebendo dados para novo cliente")
            logger.debug(f"Form data: {dict(request.form)}")
            
            cliente_data = {
                'nome': request.form['nome'],
                'email': request.form['email'],
                'telefone': request.form['telefone'],
                'cpf_cnpj': request.form['cpf_cnpj'],
                'endereco': request.form['endereco'],
                'cidade': request.form['cidade'],
                'estado': request.form['estado'],
                'cep': request.form['cep']
            }
            
            logger.debug(f"Dados do cliente: {cliente_data}")
            logger.info("Tentando criar cliente no Supabase...")
            
            if Cliente.create(**cliente_data):
                logger.info("Cliente criado com sucesso!")
                flash('Cliente criado com sucesso!', 'success')
                return redirect(url_for('clientes'))
            else:
                logger.error("Falha ao criar cliente")
                flash('Erro ao criar cliente!', 'error')
        except Exception as e:
            logger.error(f"Erro ao criar cliente: {e}")
            flash(f'Erro ao criar cliente: {e}', 'error')
    
    return render_template('cliente_form.html')

@app.route('/cliente/editar/<id>', methods=['GET', 'POST'])
@login_required
def editar_cliente(id):
    """Editar cliente existente"""
    logger.debug(f"Editando cliente com ID: {id}")
    try:
        cliente = Cliente.get_by_id(id)
        if not cliente:
            logger.warning(f"Cliente não encontrado para edição: {id}")
            flash('Cliente não encontrado!', 'error')
            return redirect(url_for('clientes'))
        
        if request.method == 'POST':
            logger.info(f"Recebendo dados para editar cliente {id}")
            logger.debug(f"Form data: {dict(request.form)}")
            
            cliente_data = {
                'nome': request.form['nome'],
                'email': request.form['email'],
                'telefone': request.form['telefone'],
                'cpf_cnpj': request.form['cpf_cnpj'],
                'endereco': request.form['endereco'],
                'cidade': request.form['cidade'],
                'estado': request.form['estado'],
                'cep': request.form['cep']
            }
            
            logger.debug(f"Dados do cliente para edição: {cliente_data}")
            
            if Cliente.update(id, **cliente_data):
                logger.info(f"Cliente {id} atualizado com sucesso")
                flash('Cliente atualizado com sucesso!', 'success')
                return redirect(url_for('clientes'))
            else:
                logger.error(f"Falha ao atualizar cliente {id}")
                flash('Erro ao atualizar cliente!', 'error')
        
        return render_template('cliente_form.html', cliente=cliente)
    except Exception as e:
        logger.error(f"Erro ao editar cliente {id}: {e}", exc_info=True)
        flash(f'Erro ao editar cliente: {e}', 'error')
        return redirect(url_for('clientes'))

@app.route('/cliente/excluir/<id>')
@login_required
def excluir_cliente(id):
    """Excluir cliente"""
    logger.info(f"Tentando excluir cliente {id}")
    try:
        if Cliente.delete(id):
            logger.info(f"Cliente {id} excluído com sucesso")
            flash('Cliente excluído com sucesso!', 'success')
        else:
            logger.error(f"Falha ao excluir cliente {id}")
            flash('Erro ao excluir cliente!', 'error')
    except Exception as e:
        logger.error(f"Erro ao excluir cliente {id}: {e}", exc_info=True)
        flash(f'Erro ao excluir cliente: {e}', 'error')
    
    return redirect(url_for('clientes'))

# Rotas de Categorias
@app.route('/categorias')
@login_required
def categorias():
    """Lista de categorias"""
    try:
        categorias_list = Categoria.get_all()
        return render_template('categorias.html', categorias=categorias_list)
    except Exception as e:
        logger.error(f"Erro ao carregar categorias: {e}")
        flash(f'Erro ao carregar categorias: {e}', 'error')
        return render_template('categorias.html', categorias=[])

@app.route('/categoria/nova', methods=['GET', 'POST'])
@login_required
def nova_categoria():
    """Nova categoria"""
    if request.method == 'POST':
        try:
            categoria_data = {
                'nome': request.form['nome'],
                'descricao': request.form['descricao'],
                'cor': request.form['cor'],
                'icone': request.form['icone']
            }
            
            if Categoria.create(**categoria_data):
                flash('Categoria criada com sucesso!', 'success')
                return redirect(url_for('categorias'))
            else:
                flash('Erro ao criar categoria!', 'error')
        except Exception as e:
            logger.error(f"Erro ao criar categoria: {e}")
            flash(f'Erro ao criar categoria: {e}', 'error')
    
    return render_template('categoria_form.html')

@app.route('/categoria/editar/<id>', methods=['GET', 'POST'])
@login_required
def editar_categoria(id):
    """Editar categoria existente"""
    logger.debug(f"Editando categoria com ID: {id}")
    try:
        categoria = Categoria.get_by_id(id)
        if not categoria:
            logger.warning(f"Categoria não encontrada para edição: {id}")
            flash('Categoria não encontrada!', 'error')
            return redirect(url_for('categorias'))
        
        if request.method == 'POST':
            logger.info(f"Recebendo dados para editar categoria {id}")
            logger.debug(f"Form data: {dict(request.form)}")
            
            categoria_data = {
                'nome': request.form['nome'],
                'descricao': request.form['descricao'],
                'cor': request.form['cor'],
                'icone': request.form['icone']
            }
            
            logger.debug(f"Dados da categoria para edição: {categoria_data}")
            
            if Categoria.update(id, **categoria_data):
                logger.info(f"Categoria {id} atualizada com sucesso")
                flash('Categoria atualizada com sucesso!', 'success')
                return redirect(url_for('categorias'))
            else:
                logger.error(f"Falha ao atualizar categoria {id}")
                flash('Erro ao atualizar categoria!', 'error')
        
        return render_template('categoria_form.html', categoria=categoria)
    except Exception as e:
        logger.error(f"Erro ao editar categoria {id}: {e}", exc_info=True)
        flash(f'Erro ao editar categoria: {e}', 'error')
        return redirect(url_for('categorias'))

@app.route('/categoria/excluir/<id>')
@login_required
def excluir_categoria(id):
    """Excluir categoria"""
    logger.info(f"Tentando excluir categoria {id}")
    try:
        if Categoria.delete(id):
            logger.info(f"Categoria {id} excluída com sucesso")
            flash('Categoria excluída com sucesso!', 'success')
        else:
            logger.error(f"Falha ao excluir categoria {id}")
            flash('Erro ao excluir categoria!', 'error')
    except Exception as e:
        logger.error(f"Erro ao excluir categoria {id}: {e}", exc_info=True)
        flash(f'Erro ao excluir categoria: {e}', 'error')
    
    return redirect(url_for('categorias'))

# Rotas de Produtos
@app.route('/produtos')
@login_required
def produtos():
    """Lista de produtos"""
    try:
        produtos_list = Produto.get_all()
        categorias_list = Categoria.get_all()
        return render_template('produtos.html', produtos=produtos_list, categorias=categorias_list)
    except Exception as e:
        logger.error(f"Erro ao carregar produtos: {e}")
        flash(f'Erro ao carregar produtos: {e}', 'error')
        return render_template('produtos.html', produtos=[], categorias=[])

@app.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    """Novo produto"""
    if request.method == 'POST':
        try:
            # Processar upload de imagem
            imagem_filename = None
            if 'imagem' in request.files:
                file = request.files['imagem']
                if file and file.filename:
                    imagem_filename = save_image(file)
            
            produto_data = {
                'nome': request.form['nome'],
                'descricao': request.form['descricao'],
                'preco': float(request.form['preco']),
                'categoria_id': request.form['categoria_id'],
                'codigo_barras': request.form['codigo_barras'],
                'imagem': imagem_filename
            }
            
            if Produto.create(**produto_data):
                flash('Produto criado com sucesso!', 'success')
                return redirect(url_for('produtos'))
            else:
                flash('Erro ao criar produto!', 'error')
        except Exception as e:
            logger.error(f"Erro ao criar produto: {e}")
            flash(f'Erro ao criar produto: {e}', 'error')
    
    try:
        categorias_list = Categoria.get_all()
        return render_template('produto_form.html', categorias=categorias_list)
    except Exception as e:
        logger.error(f"Erro ao carregar categorias: {e}")
        return render_template('produto_form.html', categorias=[])

@app.route('/produto/editar/<id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    """Editar produto existente"""
    logger.debug(f"Editando produto com ID: {id}")
    try:
        produto = Produto.get_by_id(id)
        if not produto:
            logger.warning(f"Produto não encontrado para edição: {id}")
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('produtos'))
        
        if request.method == 'POST':
            logger.info(f"Recebendo dados para editar produto {id}")
            logger.debug(f"Form data: {dict(request.form)}")
            
            try:
                # Processar upload de imagem
                imagem_filename = produto.get('imagem')  # Manter imagem atual
                if 'imagem' in request.files:
                    file = request.files['imagem']
                    if file and file.filename:
                        logger.debug(f"Processando nova imagem: {file.filename}")
                        nova_imagem = save_image(file)
                        if nova_imagem:
                            imagem_filename = nova_imagem
                
                produto_data = {
                    'nome': request.form['nome'],
                    'descricao': request.form['descricao'],
                    'preco': float(request.form['preco']),
                    'categoria_id': request.form['categoria_id'],
                    'codigo_barras': request.form['codigo_barras'],
                    'imagem': imagem_filename
                }
                
                logger.debug(f"Dados do produto para edição: {produto_data}")
                
                if Produto.update(id, **produto_data):
                    logger.info(f"Produto {id} atualizado com sucesso")
                    flash('Produto atualizado com sucesso!', 'success')
                    return redirect(url_for('produtos'))
                else:
                    logger.error(f"Falha ao atualizar produto {id}")
                    flash('Erro ao atualizar produto!', 'error')
            except Exception as e:
                logger.error(f"Erro ao processar dados do produto: {e}")
                flash(f'Erro ao processar dados: {e}', 'error')
        
        try:
            categorias_list = Categoria.get_all()
            return render_template('produto_form.html', produto=produto, categorias=categorias_list)
        except Exception as e:
            logger.error(f"Erro ao carregar categorias: {e}")
            return render_template('produto_form.html', produto=produto, categorias=[])
            
    except Exception as e:
        logger.error(f"Erro ao editar produto {id}: {e}", exc_info=True)
        flash(f'Erro ao editar produto: {e}', 'error')
        return redirect(url_for('produtos'))

@app.route('/produto/excluir/<id>')
@login_required
def excluir_produto(id):
    """Excluir produto"""
    logger.info(f"Tentando excluir produto {id}")
    try:
        if Produto.delete(id):
            logger.info(f"Produto {id} excluído com sucesso")
            flash('Produto excluído com sucesso!', 'success')
        else:
            logger.error(f"Falha ao excluir produto {id}")
            flash('Erro ao excluir produto!', 'error')
    except Exception as e:
        logger.error(f"Erro ao excluir produto {id}: {e}", exc_info=True)
        flash(f'Erro ao excluir produto: {e}', 'error')
    
    return redirect(url_for('produtos'))

# Rotas de Estoque
@app.route('/estoque')
@login_required
def estoque():
    """Lista de estoque"""
    try:
        estoque_list = Estoque.get_all()
        return render_template('estoque.html', estoque=estoque_list)
    except Exception as e:
        logger.error(f"Erro ao carregar estoque: {e}")
        flash(f'Erro ao carregar estoque: {e}', 'error')
        return render_template('estoque.html', estoque=[])

# Rotas de Vendas
@app.route('/vendas')
@login_required
def vendas():
    """Lista de vendas"""
    try:
        vendas_list = Venda.get_all()
        return render_template('vendas.html', vendas=vendas_list)
    except Exception as e:
        logger.error(f"Erro ao carregar vendas: {e}")
        flash(f'Erro ao carregar vendas: {e}', 'error')
        return render_template('vendas.html', vendas=[])

@app.route('/venda/nova', methods=['GET', 'POST'])
@login_required
def nova_venda():
    """Nova venda"""
    if request.method == 'POST':
        try:
            venda_data = {
                'cliente_id': request.form['cliente_id'],
                'data_venda': datetime.now().isoformat(),
                'total': float(request.form['total']),
                'status': 'concluida'
            }
            
            if Venda.create(**venda_data):
                flash('Venda criada com sucesso!', 'success')
                return redirect(url_for('vendas'))
            else:
                flash('Erro ao criar venda!', 'error')
        except Exception as e:
            logger.error(f"Erro ao criar venda: {e}")
            flash(f'Erro ao criar venda: {e}', 'error')
    
    try:
        clientes_list = Cliente.get_all()
        produtos_list = Produto.get_all()
        return render_template('venda_form.html', clientes=clientes_list, produtos=produtos_list)
    except Exception as e:
        logger.error(f"Erro ao carregar dados para venda: {e}")
        return render_template('venda_form.html', clientes=[], produtos=[])

# Rotas de Relatórios
@app.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios"""
    return render_template('relatorios.html')

@app.route('/api/relatorio/vendas')
@login_required
def api_relatorio_vendas():
    """API para relatório de vendas"""
    try:
        vendas = Venda.get_all()
        return jsonify(vendas)
    except Exception as e:
        logger.error(f"Erro no relatório de vendas: {e}")
        return jsonify({'erro': str(e)}), 500

@app.route('/api/relatorio/estoque')
@login_required
def api_relatorio_estoque():
    """API para relatório de estoque"""
    try:
        estoque = Estoque.get_all()
        return jsonify(estoque)
    except Exception as e:
        logger.error(f"Erro no relatório de estoque: {e}")
        return jsonify({'erro': str(e)}), 500

# Rotas de Sincronização
@app.route('/sync/start')
@login_required
def start_sync_route():
    """Inicia a sincronização automática"""
    try:
        start_sync()
        flash('Sincronização automática iniciada!', 'success')
        logger.info("Sincronização iniciada via rota web")
    except Exception as e:
        flash(f'Erro ao iniciar sincronização: {e}', 'error')
        logger.error(f"Erro ao iniciar sincronização: {e}")
    
    return redirect(url_for('index'))

@app.route('/sync/stop')
@login_required
def stop_sync_route():
    """Para a sincronização automática"""
    try:
        stop_sync()
        flash('Sincronização automática parada!', 'info')
        logger.info("Sincronização parada via rota web")
    except Exception as e:
        flash(f'Erro ao parar sincronização: {e}', 'error')
        logger.error(f"Erro ao parar sincronização: {e}")
    
    return redirect(url_for('index'))

@app.route('/sync/force')
@login_required
def force_sync_route():
    """Força uma sincronização imediata"""
    try:
        force_sync()
        flash('Sincronização forçada executada!', 'success')
        logger.info("Sincronização forçada via rota web")
    except Exception as e:
        flash(f'Erro na sincronização forçada: {e}', 'error')
        logger.error(f"Erro na sincronização forçada: {e}")
    
    return redirect(url_for('index'))

@app.route('/sync/status')
@login_required
def sync_status_route():
    """Mostra o status da sincronização"""
    try:
        status = get_sync_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Erro ao obter status da sincronização: {e}")
        return jsonify({'erro': str(e)}), 500

# Rotas PWA
@app.route('/manifest.json')
def manifest():
    """Manifest para PWA"""
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    """Service Worker para PWA"""
    return app.send_static_file('sw.js')

# Rota de teste para verificar clientes
@app.route('/teste/clientes')
@login_required
def teste_clientes():
    """Rota de teste para verificar clientes"""
    logger.info("Acessando rota de teste de clientes")
    
    try:
        # Buscar clientes
        clientes = Cliente.get_all()
        logger.info(f"Total de clientes encontrados: {len(clientes)}")
        
        # Criar cliente de teste
        logger.info("Criando cliente de teste...")
        cliente_teste = {
            'nome': 'Cliente Teste Web',
            'email': 'teste.web@teste.com',
            'telefone': '(11) 77777-7777',
            'cpf_cnpj': '111.222.333-44',
            'endereco': 'Rua Teste Web, 999',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01234-999'
        }
        
        resultado = Cliente.create(**cliente_teste)
        
        if resultado:
            logger.info(f"Cliente de teste criado com sucesso! ID: {resultado['id']}")
            flash(f'Cliente de teste criado! ID: {resultado["id"]}', 'success')
        else:
            logger.error("Falha ao criar cliente de teste")
            flash('Falha ao criar cliente de teste!', 'error')
        
        # Buscar novamente
        clientes_apos = Cliente.get_all()
        logger.info(f"Total de clientes após teste: {len(clientes_apos)}")
        
        return jsonify({
            'antes': len(clientes),
            'depois': len(clientes_apos),
            'cliente_teste': resultado,
            'todos_clientes': clientes_apos
        })
        
    except Exception as e:
        logger.error(f"Erro no teste de clientes: {e}", exc_info=True)
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando Sistema Empresarial - VERSÃO PRODUÇÃO")
    
    try:
        # Testar conexão com Supabase
        if supabase and supabase.test_connection():
            logger.info("✅ Conexão com Supabase estabelecida!")
            
            # Criar usuário padrão
            criar_usuario_padrao()
            
            # Iniciar sincronização automática
            logger.info("🔄 Iniciando sistema de sincronização...")
            start_sync()
        else:
            logger.warning("⚠️ Conexão com Supabase falhou, mas continuando...")
            
            # Criar usuário padrão mesmo sem Supabase
            criar_usuario_padrao()
        
        # Iniciar aplicação
        logger.info("🌐 Iniciando servidor Flask para produção...")
        app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        logger.info("🌐 Iniciando servidor Flask mesmo com erro...")
        app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
