#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Empresarial - Versão de Produção
Hospedado no Render
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
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
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configurar logging mais detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log de inicialização
logger.info("🚀 Iniciando configuração do Sistema Empresarial")
logger.info(f"📁 Diretório de trabalho: {os.getcwd()}")
logger.info(f"🌐 Porta: {os.environ.get('PORT', '5000')}")
logger.info(f"🔑 Secret Key: {'Configurada' if app.config['SECRET_KEY'] else 'Não configurada'}")

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Configurar sessão de forma mais robusta
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutos
app.config['SESSION_COOKIE_SECURE'] = False  # Render pode não ter HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Variável global para controlar disponibilidade do Supabase
SUPABASE_AVAILABLE = False

# Importações com tratamento de erro robusto
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
        logger.info(f"👤 Carregando usuário: {user_id}")
        
        if SUPABASE_AVAILABLE:
            # Tentar carregar do Supabase
            try:
                user = Usuario.get_by_id(user_id)
                if user:
                    logger.info(f"✅ Usuário {user_id} carregado do Supabase")
                    return user
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar usuário {user_id} do Supabase: {e}")
        
        # Fallback para usuário mock
        if user_id == 'admin':
            logger.info(f"✅ Usuário {user_id} carregado como mock")
            return MockUser('admin', 'admin', 'Administrador')
        
        logger.warning(f"❌ Usuário {user_id} não encontrado")
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar usuário {user_id}: {e}")
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

# Classe de usuário mock para Flask-Login
class MockUser:
    def __init__(self, user_id, username, nome):
        self.id = user_id
        self.username = username
        self.nome = nome
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)

def authenticate_user(username, password):
    """Autentica usuário"""
    try:
        logger.info(f"🔐 Tentando autenticar usuário: {username}")
        
        # Autenticação simples para admin
        if username == 'admin' and password == 'admin123':
            logger.info(f"✅ Usuário {username} autenticado com sucesso")
            return MockUser('admin', 'admin', 'Administrador')
        
        logger.warning(f"❌ Falha na autenticação para usuário: {username}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro na autenticação: {e}")
        return None

def save_image(file):
    """Salva imagem de upload"""
    try:
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Gerar nome único
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Criar diretório de upload se não existir
            upload_folder = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            
            filepath = os.path.join(upload_folder, unique_filename)
            
            logger.info(f"💾 Salvando imagem: {filepath}")
            file.save(filepath)
            logger.info(f"✅ Imagem salva com sucesso: {unique_filename}")
            return unique_filename
    except Exception as e:
        logger.error(f"❌ Erro ao salvar imagem: {e}")
        return None

# Rotas principais
@app.route('/')
def index():
    """Dashboard principal - redireciona para login se não autenticado"""
    logger.info("📍 Acessando rota raiz /")
    
    try:
        # Verificar se o usuário está autenticado de forma segura
        if not current_user or not current_user.is_authenticated:
            logger.info("👤 Usuário não autenticado, redirecionando para login")
            return redirect(url_for('login'))
        
        logger.info("✅ Usuário autenticado, carregando dashboard")
        
        # Estatísticas básicas com tratamento de erro robusto
        total_clientes = 0
        total_produtos = 0
        total_categorias = 0
        total_vendas = 0
        
        try:
            if hasattr(Cliente, 'get_all') and callable(Cliente.get_all):
                total_clientes = len(Cliente.get_all())
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar clientes: {e}")
            total_clientes = 0
            
        try:
            if hasattr(Produto, 'get_all') and callable(Produto.get_all):
                total_produtos = len(Produto.get_all())
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar produtos: {e}")
            total_produtos = 0
            
        try:
            if hasattr(Categoria, 'get_all') and callable(Categoria.get_all):
                total_categorias = len(Categoria.get_all())
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar categorias: {e}")
            total_categorias = 0
            
        try:
            if hasattr(Venda, 'get_all') and callable(Venda.get_all):
                total_vendas = len(Venda.get_all())
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar vendas: {e}")
            total_vendas = 0
        
        # Retornar HTML simples e funcional
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Sistema Empresarial</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: #667eea; color: white; padding: 30px; text-align: center; }}
                .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
                .header p {{ font-size: 1.2em; opacity: 0.9; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 30px; }}
                .stat-card {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
                .stat-card h3 {{ font-size: 1.3em; margin-bottom: 15px; opacity: 0.9; }}
                .stat-card .number {{ font-size: 3em; font-weight: bold; margin-bottom: 10px; }}
                .actions {{ padding: 30px; text-align: center; background: #f8f9fa; }}
                .btn {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 10px; display: inline-block; font-weight: 600; transition: all 0.3s ease; }}
                .btn:hover {{ background: #5a6fd8; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }}
                .btn-secondary {{ background: #6c757d; }}
                .btn-secondary:hover {{ background: #5a6268; }}
                .logout {{ text-align: right; padding: 20px 30px; background: #f8f9fa; border-top: 1px solid #dee2e6; }}
                .logout a {{ color: #dc3545; text-decoration: none; font-weight: 600; }}
                .logout a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 Sistema Empresarial</h1>
                    <p>Bem-vindo ao seu painel de controle!</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>👥 Clientes</h3>
                        <div class="number">{total_clientes}</div>
                        <p>Cadastrados</p>
                    </div>
                    <div class="stat-card">
                        <h3>📦 Produtos</h3>
                        <div class="number">{total_produtos}</div>
                        <p>Em estoque</p>
                    </div>
                    <div class="stat-card">
                        <h3>🏷️ Categorias</h3>
                        <div class="number">{total_categorias}</div>
                        <p>Ativas</p>
                    </div>
                    <div class="stat-card">
                        <h3>💰 Vendas</h3>
                        <div class="number">{total_vendas}</div>
                        <p>Realizadas</p>
                    </div>
                </div>
                
                <div class="actions">
                    <a href="/clientes" class="btn">👥 Gerenciar Clientes</a>
                    <a href="/produtos" class="btn">📦 Gerenciar Produtos</a>
                    <a href="/categorias" class="btn">🏷️ Gerenciar Categorias</a>
                    <a href="/vendas" class="btn">💰 Gerenciar Vendas</a>
                    <a href="/estoque" class="btn">📊 Controle de Estoque</a>
                </div>
                
                <div class="logout">
                    <a href="/logout">🚪 Sair do Sistema</a>
                </div>
            </div>
        </body>
        </html>
        """
            
    except Exception as e:
        logger.error(f"❌ Erro crítico na rota raiz: {e}")
        # Página de erro de emergência
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erro - Sistema Empresarial</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
                .error-container {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; max-width: 600px; margin: 0 auto; }}
                .error-icon {{ font-size: 4em; margin-bottom: 20px; }}
                .btn {{ background: #667eea; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; margin: 10px; display: inline-block; }}
                .btn:hover {{ background: #5a6fd8; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <h1>Erro no Sistema</h1>
                <p>Ocorreu um erro inesperado. Por favor, tente novamente.</p>
                <p><strong>Erro:</strong> {e}</p>
                <hr style="margin: 30px 0;">
                <a href="/login" class="btn">🔐 Tentar Login</a>
                <a href="/teste" class="btn">🧪 Teste</a>
                <a href="/fallback" class="btn">📱 Versão JavaScript</a>
            </div>
        </body>
        </html>
        """

@app.route('/fallback')
def fallback():
    """Página de fallback com JavaScript puro"""
    return app.send_static_file('fallback.html')

@app.route('/teste')
def teste():
    """Rota de teste simples"""
    logger.info("🧪 Acessando rota de teste")
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teste - Sistema Empresarial</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; color: white; }
            .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; backdrop-filter: blur(10px); text-align: center; }
            h1 { font-size: 3em; margin-bottom: 20px; }
            .status { background: rgba(255,255,255,0.2); padding: 25px; border-radius: 15px; margin: 30px 0; }
            .btn { background: rgba(255,255,255,0.2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 10px; margin: 15px; display: inline-block; font-weight: 600; transition: all 0.3s ease; }
            .btn:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 TESTE FUNCIONANDO!</h1>
            <p style="font-size: 1.3em; margin-bottom: 30px;">✅ O Flask está rodando corretamente no Render!</p>
            
            <div class="status">
                <h3>📊 Status do Sistema:</h3>
                <p><strong>Flask:</strong> ✅ Funcionando</p>
                <p><strong>Render:</strong> ✅ Hospedado</p>
                <p><strong>URL:</strong> controle-visual.onrender.com</p>
                <p><strong>Timestamp:</strong> """ + str(datetime.now()) + """</p>
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/" class="btn">🏠 Tentar Dashboard</a>
                <a href="/login" class="btn">🔐 Tentar Login</a>
                <a href="/fallback" class="btn">📱 Versão JavaScript</a>
                <a href="/api/status" class="btn">🔍 API Status</a>
            </div>
            
            <hr style="margin: 30px 0; border: 1px solid rgba(255,255,255,0.3);">
            <p style="font-size: 14px; opacity: 0.8;">
                Se você vê esta página, o Flask está funcionando!<br>
                O problema pode estar nas outras rotas ou templates.
            </p>
        </div>
    </body>
    </html>
    """

@app.route('/debug')
def debug():
    """Rota de debug para verificar o status"""
    logger.info("🔍 Acessando rota de debug")
    try:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Debug - Sistema Empresarial</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f8f9fa; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
                h1 {{ color: #667eea; text-align: center; margin-bottom: 30px; }}
                .status {{ background: #e9ecef; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .status h3 {{ color: #495057; margin-bottom: 15px; }}
                .status p {{ margin: 5px 0; }}
                .routes {{ background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .routes ul {{ list-style: none; padding: 0; }}
                .routes li {{ padding: 8px 0; border-bottom: 1px solid #dee2e6; }}
                .routes li:last-child {{ border-bottom: none; }}
                .routes a {{ color: #667eea; text-decoration: none; font-weight: 600; }}
                .routes a:hover {{ text-decoration: underline; }}
                .btn {{ background: #667eea; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; margin: 10px; display: inline-block; }}
                .btn:hover {{ background: #5a6fd8; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 DEBUG - Sistema Empresarial</h1>
                
                <div class="status">
                    <h3>Status da Aplicação:</h3>
                    <p><strong>Flask:</strong> ✅ Funcionando</p>
                    <p><strong>Supabase:</strong> {'✅ Disponível' if SUPABASE_AVAILABLE else '❌ Não disponível'}</p>
                    <p><strong>Usuário atual:</strong> {current_user.is_authenticated if current_user else 'Não logado'}</p>
                    <p><strong>ID do usuário:</strong> {current_user.get_id() if current_user else 'N/A'}</p>
                    <p><strong>Username:</strong> {getattr(current_user, 'username', 'N/A') if current_user else 'N/A'}</p>
                    <p><strong>Sessão ativa:</strong> {session.get('_user_id', 'N/A')}</p>
                    <p><strong>Timestamp:</strong> {datetime.now()}</p>
                    <p><strong>Porta:</strong> {os.environ.get('PORT', '5000')}</p>
                </div>
                
                <div class="routes">
                    <h3>Rotas disponíveis:</h3>
                    <ul>
                        <li><a href="/">/ (Dashboard)</a></li>
                        <li><a href="/login">/login</a></li>
                        <li><a href="/teste">/teste</a></li>
                        <li><a href="/debug">/debug</a></li>
                        <li><a href="/fallback">/fallback</a></li>
                        <li><a href="/api/status">/api/status</a></li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/" class="btn">← Voltar para Dashboard</a>
                    <a href="/teste" class="btn">🧪 Teste</a>
                    <a href="/logout" class="btn">🚪 Logout</a>
                </div>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"❌ Erro na rota de debug: {e}")
        return f"Erro no debug: {e}"

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    logger.info("🔐 Acessando rota de login")
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        logger.info(f"👤 Tentativa de login para usuário: {username}")
        
        try:
            user = authenticate_user(username, password)
            if user:
                logger.info(f"✅ Usuário autenticado: {user.username}")
                login_user(user)
                logger.info(f"✅ Login bem-sucedido para usuário: {username}")
                logger.info(f"🔗 Redirecionando para: {url_for('index')}")
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                logger.warning(f"❌ Login falhou para usuário: {username}")
                flash('Usuário ou senha incorretos!', 'error')
        except Exception as e:
            logger.error(f"❌ Erro no login: {e}")
            flash('Erro no login!', 'error')
    
    try:
        return render_template('login.html')
    except Exception as template_error:
        logger.error(f"⚠️ Erro ao renderizar template de login: {template_error}")
        # Fallback para HTML simples
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login - Sistema Empresarial</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .login-container {{ background: white; padding: 40px; border-radius: 20px; box-shadow: 0 25px 50px rgba(0,0,0,0.15); max-width: 400px; width: 100%; margin: 20px; }}
                h1 {{ text-align: center; color: #667eea; margin-bottom: 30px; font-size: 2.2em; }}
                .form-group {{ margin-bottom: 25px; }}
                label {{ display: block; margin-bottom: 8px; font-weight: 600; color: #555; font-size: 0.95em; }}
                input {{ width: 100%; padding: 15px; border: 2px solid #e9ecef; border-radius: 10px; font-size: 16px; box-sizing: border-box; transition: all 0.3s ease; }}
                input:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }}
                .btn {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 20px; border: none; border-radius: 10px; font-size: 16px; cursor: pointer; width: 100%; font-weight: 600; transition: all 0.3s ease; }}
                .btn:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }}
                .info {{ text-align: center; margin-top: 25px; color: #666; font-size: 14px; line-height: 1.5; }}
                .info a {{ color: #667eea; text-decoration: none; font-weight: 600; }}
                .info a:hover {{ text-decoration: underline; }}
                .credentials {{ background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 20px; border-left: 4px solid #667eea; }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <h1>🔐 Login</h1>
                <form method="POST" action="/login">
                    <div class="form-group">
                        <label>Usuário:</label>
                        <input type="text" name="username" value="admin" required>
                    </div>
                    <div class="form-group">
                        <label>Senha:</label>
                        <input type="password" name="password" value="admin123" required>
                    </div>
                    <button type="submit" class="btn">Entrar no Sistema</button>
                </form>
                
                <div class="credentials">
                    <p><strong>🔑 Credenciais padrão:</strong></p>
                    <p><strong>Usuário:</strong> admin</p>
                    <p><strong>Senha:</strong> admin123</p>
                </div>
                
                <div class="info">
                    <p><a href="/">← Voltar para Dashboard</a></p>
                    <p><a href="/teste">🧪 Teste do Sistema</a></p>
                </div>
            </div>
        </body>
        </html>
        """

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
                'quantidade': int(request.form.get('quantidade', 0)),  # ADICIONANDO QUANTIDADE!
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
                # Log dos dados recebidos do formulário
                logger.info(f"📝 Dados do formulário recebidos:")
                for key, value in request.form.items():
                    logger.info(f"   {key}: {value}")
                
                # Processar upload de imagem
                imagem_filename = produto.get('imagem')  # Manter imagem atual
                if 'imagem' in request.files:
                    file = request.files['imagem']
                    if file and file.filename:
                        logger.debug(f"Processando nova imagem: {file.filename}")
                        nova_imagem = save_image(file)
                        if nova_imagem:
                            imagem_filename = nova_imagem
                
                # Validar campos obrigatórios
                if not request.form.get('nome'):
                    flash('Nome do produto é obrigatório!', 'error')
                    raise ValueError("Nome não informado")
                
                if not request.form.get('categoria_id'):
                    flash('Categoria é obrigatória!', 'error')
                    raise ValueError("Categoria não informada")
                
                produto_data = {
                    'nome': request.form['nome'],
                    'descricao': request.form.get('descricao', ''),
                    'preco': float(request.form.get('preco', 0)),
                    'quantidade': int(request.form.get('quantidade', 0)),
                    'categoria_id': request.form['categoria_id'],
                    'codigo_barras': request.form.get('codigo_barras', ''),
                    'imagem': imagem_filename
                }
                
                logger.info(f"✅ Dados preparados para atualização: {produto_data}")
                
                resultado = Produto.update(id, **produto_data)
                logger.info(f"📊 Resultado da atualização: {resultado}")
                
                if resultado:
                    logger.info(f"✅ Produto {id} atualizado com sucesso")
                    flash('Produto atualizado com sucesso!', 'success')
                    return redirect(url_for('produtos'))
                else:
                    logger.error(f"❌ Falha ao atualizar produto {id}")
                    flash('Erro ao atualizar produto! Verifique os dados e tente novamente.', 'error')
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
        logger.info("📊 Acessando rota de estoque")
        
        # Buscar produtos (que contêm as informações de estoque)
        try:
            produtos_list = Produto.get_all()
            logger.info(f"✅ Produtos carregados: {len(produtos_list)} itens")
            
            # Converter produtos para formato de estoque
            estoque_list = []
            for produto in produtos_list:
                estoque_item = {
                    'id': produto.get('id', ''),
                    'nome': produto.get('nome', 'Produto'),
                    'descricao': produto.get('descricao', ''),
                    'quantidade': produto.get('quantidade', 0),
                    'preco': produto.get('preco', 0.0),
                    'categoria': produto.get('categoria', 'Sem categoria'),
                    'imagem': produto.get('imagem', ''),
                    'codigo_barras': produto.get('codigo_barras', ''),
                    'status': 'Em estoque' if produto.get('quantidade', 0) > 0 else 'Sem estoque'
                }
                estoque_list.append(estoque_item)
            
            logger.info(f"📊 Estoque convertido: {len(estoque_list)} itens")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar produtos: {e}")
            estoque_list = []
        
        # Criar HTML inline seguindo o padrão das outras telas
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Estoque - Sistema Empresarial</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: #667eea; color: white; padding: 30px; text-align: center; }}
                .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
                .header p {{ font-size: 1.2em; opacity: 0.9; }}
                .content {{ padding: 30px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
                .stat-card {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
                .stat-card h3 {{ font-size: 1.3em; margin-bottom: 15px; opacity: 0.9; }}
                .stat-card .number {{ font-size: 3em; font-weight: bold; margin-bottom: 10px; }}
                .table-container {{ overflow-x: auto; margin: 30px 0; }}
                table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
                th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #dee2e6; }}
                th {{ background: #667eea; color: white; font-weight: 600; }}
                tr:hover {{ background: #f8f9fa; }}
                .btn {{ background: #667eea; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; margin: 10px; display: inline-block; font-weight: 600; transition: all 0.3s ease; }}
                .btn:hover {{ background: #5a6fd8; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }}
                .actions {{ text-align: center; margin-top: 30px; background: #f8f9fa; padding: 30px; border-top: 1px solid #dee2e6; }}
                .produto-imagem {{ width: 50px; height: 50px; object-fit: cover; border-radius: 8px; }}
                .status-estoque {{ padding: 5px 10px; border-radius: 15px; font-size: 0.9em; font-weight: 600; }}
                .status-em-estoque {{ background: #d4edda; color: #155724; }}
                .status-sem-estoque {{ background: #f8d7da; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Controle de Estoque</h1>
                    <p>Gerencie o estoque dos seus produtos</p>
                </div>
                
                <div class="content">
                    <div class="stats">
                        <div class="stat-card">
                            <h3>📦 Total de Produtos</h3>
                            <div class="number">{len(estoque_list)}</div>
                            <p>Cadastrados</p>
                        </div>
                        <div class="stat-card">
                            <h3>✅ Em Estoque</h3>
                            <div class="number">{len([item for item in estoque_list if item.get('quantidade', 0) > 0])}</div>
                            <p>Disponíveis</p>
                        </div>
                        <div class="stat-card">
                            <h3>❌ Sem Estoque</h3>
                            <div class="number">{len([item for item in estoque_list if item.get('quantidade', 0) <= 0])}</div>
                            <p>Indisponíveis</p>
                        </div>
                    </div>
                    
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Imagem</th>
                                    <th>Produto</th>
                                    <th>Descrição</th>
                                    <th>Quantidade</th>
                                    <th>Preço</th>
                                    <th>Categoria</th>
                                    <th>Status</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'''
                                <tr>
                                    <td>
                                        {f'<img src="/uploads/{item.get("imagem")}" class="produto-imagem" alt="{item.get("nome")}">' if item.get('imagem') else '<div class="produto-imagem" style="background: #e9ecef; display: flex; align-items: center; justify-content: center; color: #6c757d;">📦</div>'}
                                    </td>
                                    <td><strong>{item.get('nome', 'N/A')}</strong></td>
                                    <td>{item.get('descricao', 'Sem descrição')[:50]}{'...' if len(item.get('descricao', '')) > 50 else ''}</td>
                                    <td><strong>{item.get('quantidade', 0)}</strong></td>
                                    <td><strong>R$ {float(item.get('preco', 0)):.2f}</strong></td>
                                    <td>{item.get('categoria', 'Sem categoria')}</td>
                                    <td>
                                        <span class="status-estoque {'status-em-estoque' if int(item.get('quantidade', 0)) > 0 else 'status-sem-estoque'}">
                                            {'✅ Em estoque' if int(item.get('quantidade', 0)) > 0 else '❌ Sem estoque'}
                                        </span>
                                    </td>
                                    <td>
                                        <a href="/produto/editar/{item.get('id')}" class="btn" style="background: #28a745;">📊 Editar Estoque</a>
                                    </td>
                                </tr>
                                ''' for item in estoque_list]) if estoque_list else '<tr><td colspan="8" style="text-align: center; padding: 30px;">Nenhum produto encontrado</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="actions">
                        <a href="/" class="btn">🏠 Dashboard</a>
                        <a href="/produtos" class="btn">📦 Gerenciar Produtos</a>
                        <a href="/vendas" class="btn">💰 Vendas</a>
                        <a href="/logout" class="btn">🚪 Sair</a>
                    </div>
                    

                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        logger.error(f"❌ Erro crítico na rota de estoque: {e}")
        # Página de erro de emergência
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erro - Estoque</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
                .error-container {{ background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; max-width: 600px; margin: 0 auto; }}
                .error-icon {{ font-size: 4em; margin-bottom: 20px; }}
                .btn {{ background: #667eea; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; margin: 10px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <h1>Erro no Estoque</h1>
                <p>Ocorreu um erro ao carregar o estoque.</p>
                <p><strong>Erro:</strong> {e}</p>
                <hr style="margin: 30px 0;">
                <a href="/" class="btn">🏠 Dashboard</a>
                <a href="/teste" class="btn">🧪 Teste</a>
            </div>
        </body>
        </html>
        """

@app.route('/estoque/atualizar/<id>', methods=['POST'])
@login_required
def atualizar_estoque(id):
    """Atualiza a quantidade em estoque de um produto"""
    try:
        logger.info(f"📊 Atualizando estoque do produto {id}")
        
        quantidade = int(request.form.get('quantidade', 0))
        
        # Buscar produto atual
        produto = Produto.get_by_id(id)
        if not produto:
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('estoque'))
        
        # Atualizar quantidade
        produto_data = {
            'quantidade': quantidade
        }
        
        if Produto.update(id, **produto_data):
            flash(f'Estoque atualizado com sucesso! Nova quantidade: {quantidade}', 'success')
            logger.info(f"✅ Estoque do produto {id} atualizado para {quantidade}")
        else:
            flash('Erro ao atualizar estoque!', 'error')
            logger.error(f"❌ Falha ao atualizar estoque do produto {id}")
        
        return redirect(url_for('estoque'))
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar estoque: {e}")
        flash(f'Erro ao atualizar estoque: {e}', 'error')
        return redirect(url_for('estoque'))

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

@app.route('/api/teste')
def api_teste():
    """Rota de teste que retorna JSON"""
    return jsonify({
        'status': 'success',
        'message': 'API funcionando!',
        'timestamp': str(datetime.now()),
        'flask_version': '2.3.0+',
        'supabase_available': SUPABASE_AVAILABLE,
        'routes': ['/', '/login', '/teste', '/debug', '/fallback', '/api/teste']
    })

@app.route('/api/status')
def api_status():
    """Rota de status da aplicação"""
    try:
        return jsonify({
            'status': 'online',
            'app': 'Sistema Empresarial',
            'version': '1.0.0',
            'environment': 'production',
            'timestamp': str(datetime.now()),
            'supabase': 'available' if SUPABASE_AVAILABLE else 'unavailable',
            'flask_login': 'configured',
            'gunicorn': 'ready'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': str(datetime.now())
        }), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Rota para servir arquivos de upload"""
    try:
        logger.info(f"📁 Servindo arquivo: {filename}")
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"❌ Erro ao servir arquivo {filename}: {e}")
        # Retornar imagem padrão ou erro
        return "Arquivo não encontrado", 404

@app.route('/teste-sessao')
def teste_sessao():
    """Rota para testar a sessão e autenticação"""
    logger.info("🧪 Testando sessão e autenticação")
    
    try:
        # Verificar status da sessão
        session_info = {
            'session_id': session.get('_user_id', 'N/A'),
            'current_user': str(current_user) if current_user else 'None',
            'is_authenticated': current_user.is_authenticated if current_user else False,
            'user_id': current_user.get_id() if current_user else 'N/A',
            'username': getattr(current_user, 'username', 'N/A') if current_user else 'N/A'
        }
        
        logger.info(f"📊 Informações da sessão: {session_info}")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Teste de Sessão - Sistema Empresarial</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; color: white; }}
                .container {{ max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; backdrop-filter: blur(10px); text-align: center; }}
                h1 {{ font-size: 2.5em; margin-bottom: 30px; }}
                .status {{ background: rgba(255,255,255,0.2); padding: 25px; border-radius: 15px; margin: 30px 0; text-align: left; }}
                .status h3 {{ margin-bottom: 20px; text-align: center; }}
                .status p {{ margin: 10px 0; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 8px; }}
                .btn {{ background: rgba(255,255,255,0.2); color: white; padding: 15px 30px; text-decoration: none; border-radius: 10px; margin: 15px; display: inline-block; font-weight: 600; }}
                .btn:hover {{ background: rgba(255,255,255,0.3); }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧪 Teste de Sessão</h1>
                
                <div class="status">
                    <h3>📊 Status da Sessão:</h3>
                    <p><strong>Session ID:</strong> {session_info['session_id']}</p>
                    <p><strong>Current User:</strong> {session_info['current_user']}</p>
                    <p><strong>Is Authenticated:</strong> {session_info['is_authenticated']}</p>
                    <p><strong>User ID:</strong> {session_info['user_id']}</p>
                    <p><strong>Username:</strong> {session_info['username']}</p>
                </div>
                
                <div style="margin-top: 30px;">
                    <a href="/login" class="btn">🔐 Fazer Login</a>
                    <a href="/" class="btn">🏠 Dashboard</a>
                    <a href="/debug" class="btn">🔍 Debug</a>
                    <a href="/logout" class="btn">🚪 Logout</a>
                </div>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de sessão: {e}")
        return f"Erro no teste de sessão: {e}"

if __name__ == '__main__':
    logger.info("🚀 Iniciando Sistema Empresarial - VERSÃO PRODUÇÃO")
    logger.info("=" * 60)
    
    try:
        # Testar conexão com Supabase
        if supabase and hasattr(supabase, 'test_connection') and supabase.test_connection():
            logger.info("✅ Conexão com Supabase estabelecida!")
            
            # Criar usuário padrão
            criar_usuario_padrao()
            
            # Iniciar sincronização automática
            logger.info("🔄 Iniciando sistema de sincronização...")
            try:
                start_sync()
            except Exception as sync_error:
                logger.warning(f"⚠️ Erro ao iniciar sincronização: {sync_error}")
        else:
            logger.warning("⚠️ Conexão com Supabase falhou ou não disponível, mas continuando...")
            
            # Criar usuário padrão mesmo sem Supabase
            criar_usuario_padrao()
        
        # Iniciar aplicação
        logger.info("🌐 Iniciando servidor Flask para produção...")
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"🚀 Servidor rodando na porta {port}")
        logger.info(f"🌍 Acesse: http://localhost:{port}")
        logger.info("=" * 60)
        app.run(debug=False, host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        logger.info("🌐 Iniciando servidor Flask mesmo com erro...")
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"🚀 Servidor rodando na porta {port} (modo de emergência)")
        logger.info(f"🌍 Acesse: http://localhost:{port}")
        logger.info("=" * 60)
        app.run(debug=False, host='0.0.0.0', port=port)
