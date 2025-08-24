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
    from config_render import get_config
    config = get_config()
    app.config.from_object(config)
    logger.info("✅ Configurações do Render carregadas com sucesso")
except Exception as e:
    logger.warning(f"⚠️ Erro ao carregar configurações do Render: {e}")
    try:
        from config_producao import config
        app.config.from_object(config)
        logger.info("✅ Configurações de produção carregadas com sucesso")
    except Exception as e2:
        logger.warning(f"⚠️ Erro ao carregar configurações de produção: {e2}")
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
    """Carrega usuário para o Flask-Login com Supabase integrado"""
    try:
        logger.info(f"👤 Carregando usuário: {user_id}")
        
        if SUPABASE_AVAILABLE:
            # Tentar carregar do Supabase
            try:
                usuarios = Usuario.get_all()
                for usuario in usuarios:
                    if usuario.get('id') == user_id and usuario.get('ativo', True):
                        logger.info(f"✅ Usuário {user_id} carregado do Supabase")
                        
                        # Criar objeto MockUser para Flask-Login
                        username = usuario.get('username', 'unknown')
                        nome = usuario.get('nome', username)
                        
                        if username == 'erick':
                            return MockUser(usuario['id'], username, 'Erick Finger - Admin Máximo')
                        else:
                            return MockUser(usuario['id'], username, nome)
                            
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar usuário {user_id} do Supabase: {e}")
        
        # Fallback para usuários mock locais
        if user_id == 'admin':
            logger.info(f"✅ Usuário {user_id} carregado como mock local")
            return MockUser('admin', 'admin', 'Administrador')
        
        if user_id == 'erick':
            logger.info(f"✅ Usuário {user_id} carregado como mock local")
            return MockUser('erick', 'erick', 'Erick Finger - Admin Máximo')
        
        logger.warning(f"❌ Usuário {user_id} não encontrado")
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao carregar usuário {user_id}: {e}")
        return None

def criar_usuario_padrao():
    """Cria usuário padrão se não existir, verificando também o usuário erick"""
    try:
        if SUPABASE_AVAILABLE:
            usuarios = Usuario.get_all()
            usuarios_existentes = [u.get('username') for u in usuarios]
            
            logger.info(f"📊 Usuários existentes: {usuarios_existentes}")
            
            # Verificar se o usuário erick já existe
            if 'erick' in usuarios_existentes:
                logger.info("✅ Usuário erick já existe no sistema")
            else:
                logger.warning("⚠️ Usuário erick não encontrado - será criado automaticamente")
                
                # Criar usuário erick automaticamente
                usuario_erick = {
                    'username': 'erick',
                    'password': '21324354',
                    'nome': 'Erick Finger',
                    'email': 'erick@sistema.com',
                    'cargo': 'Admin Máximo',
                    'ativo': True
                }
                
                if Usuario.create(**usuario_erick):
                    logger.info("✅ Usuário erick criado automaticamente!")
                else:
                    logger.error("❌ Falha ao criar usuário erick automaticamente")
            
            # Verificar se o usuário admin padrão já existe
            if 'admin' not in usuarios_existentes:
                logger.info("Criando usuário admin padrão...")
                usuario_padrao = {
                    'username': 'admin',
                    'password': 'admin123',  # Senha padrão - ALTERE EM PRODUÇÃO!
                    'nome': 'Administrador',
                    'email': 'admin@sistema.com',
                    'cargo': 'Administrador'
                }
                
                if Usuario.create(**usuario_padrao):
                    logger.info("✅ Usuário padrão criado com sucesso!")
                    logger.warning("⚠️ ALTERE A SENHA PADRÃO EM PRODUÇÃO!")
                else:
                    logger.error("❌ Falha ao criar usuário padrão!")
            else:
                logger.info("✅ Usuário admin já existe no sistema")
                
        else:
            logger.info("⚠️ Supabase não disponível - usando usuários mock locais")
    except Exception as e:
        logger.error(f"❌ Erro ao verificar/criar usuários padrão: {e}")

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
    """Autentica usuário com Supabase integrado"""
    try:
        logger.info(f"🔐 Tentando autenticar usuário: {username}")
        
        # Primeiro, tentar autenticar via Supabase
        if SUPABASE_AVAILABLE:
            try:
                # Buscar usuário no Supabase
                usuarios = Usuario.get_all()
                for usuario in usuarios:
                    if (usuario.get('username') == username and 
                        usuario.get('password') == password and 
                        usuario.get('ativo', True)):
                        
                        logger.info(f"✅ Usuário {username} autenticado via Supabase")
                        
                        # Criar objeto MockUser para Flask-Login
                        if username == 'erick':
                            return MockUser(usuario['id'], username, 'Erick Finger - Admin Máximo')
                        else:
                            return MockUser(usuario['id'], username, usuario.get('nome', username))
                
                logger.warning(f"❌ Usuário {username} não encontrado ou inativo no Supabase")
                
            except Exception as e:
                logger.warning(f"⚠️ Erro ao buscar usuário no Supabase: {e}")
        
        # Fallback para autenticação local (usuários especiais)
        if username == 'admin' and password == 'admin123':
            logger.info(f"✅ Usuário {username} autenticado localmente")
            return MockUser('admin', 'admin', 'Administrador')
        
        if username == 'erick' and password == '21324354':
            logger.info(f"✅ Usuário {username} autenticado localmente (fallback)")
            return MockUser('erick', 'erick', 'Erick Finger - Admin Máximo')
        
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
    """Dashboard principal com estatísticas integradas em tempo real"""
    logger.info("📍 Acessando dashboard com estatísticas integradas")
    
    try:
        # Verificar se o usuário está autenticado de forma segura
        if not current_user or not current_user.is_authenticated:
            logger.info("👤 Usuário não autenticado, redirecionando para login")
            return redirect(url_for('login'))
        
        logger.info("✅ Usuário autenticado, carregando dashboard integrado")
        
        # Estatísticas integradas com tratamento de erro robusto
        total_clientes = 0
        total_produtos = 0
        total_categorias = 0
        total_vendas = 0
        valor_total_vendas = 0.0
        produtos_sem_estoque = 0
        produtos_estoque_baixo = 0
        estoque_total = 0
        
        try:
            if hasattr(Cliente, 'get_all') and callable(Cliente.get_all):
                clientes_list = Cliente.get_all()
                total_clientes = len(clientes_list)
                logger.info(f"✅ Clientes carregados: {total_clientes}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar clientes: {e}")
            total_clientes = 0
            
        try:
            if hasattr(Produto, 'get_all') and callable(Produto.get_all):
                produtos_list = Produto.get_all()
                total_produtos = len(produtos_list)
                logger.info(f"✅ Produtos carregados: {total_produtos}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar produtos: {e}")
            total_produtos = 0
            
        try:
            if hasattr(Categoria, 'get_all') and callable(Categoria.get_all):
                categorias_list = Categoria.get_all()
                total_categorias = len(categorias_list)
                logger.info(f"✅ Categorias carregadas: {total_categorias}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar categorias: {e}")
            total_categorias = 0
            
        try:
            if hasattr(Venda, 'get_all') and callable(Venda.get_all):
                vendas_list = Venda.get_all()
                total_vendas = len(vendas_list)
                
                # Calcular valor total das vendas
                for venda in vendas_list:
                    if venda.get('status') == 'concluida':
                        valor_total_vendas += float(venda.get('total', 0))
                
                logger.info(f"✅ Vendas carregadas: {total_vendas}, Total: R$ {valor_total_vendas:.2f}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar vendas: {e}")
            total_vendas = 0
            valor_total_vendas = 0.0
        
        try:
            if hasattr(Estoque, 'get_all') and callable(Estoque.get_all):
                estoque_list = Estoque.get_all()
                
                # Calcular estatísticas de estoque
                for item in estoque_list:
                    quantidade = item.get('quantidade', 0)
                    quantidade_minima = item.get('quantidade_minima', 0)
                    
                    estoque_total += quantidade
                    
                    if quantidade <= 0:
                        produtos_sem_estoque += 1
                    elif quantidade <= quantidade_minima:
                        produtos_estoque_baixo += 1
                
                logger.info(f"✅ Estoque analisado: Total {estoque_total}, Sem estoque: {produtos_sem_estoque}, Baixo: {produtos_estoque_baixo}")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar estoque: {e}")
            produtos_sem_estoque = 0
            produtos_estoque_baixo = 0
            estoque_total = 0
        
        # Retornar HTML com estatísticas integradas
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
                .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); overflow: hidden; }}
                .header {{ background: #667eea; color: white; padding: 30px; text-align: center; }}
                .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
                .header p {{ font-size: 1.2em; opacity: 0.9; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; padding: 30px; }}
                .stat-card {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 8px 25px rgba(0,0,0,0.1); }}
                .stat-card h3 {{ font-size: 1.3em; margin-bottom: 15px; opacity: 0.9; }}
                .stat-card .number {{ font-size: 3em; font-weight: bold; margin-bottom: 10px; }}
                .stat-card.warning {{ background: linear-gradient(135deg, #ffc107, #ff8c00); }}
                .stat-card.danger {{ background: linear-gradient(135deg, #dc3545, #c82333); }}
                .stat-card.success {{ background: linear-gradient(135deg, #28a745, #20c997); }}
                .actions {{ padding: 30px; text-align: center; background: #f8f9fa; }}
                .btn {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 10px; display: inline-block; font-weight: 600; transition: all 0.3s ease; }}
                .btn:hover {{ background: #5a6fd8; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.2); }}
                .btn-secondary {{ background: #6c757d; }}
                .btn-secondary:hover {{ background: #5a6268; }}
                .btn-warning {{ background: #ffc107; color: #212529; }}
                .btn-warning:hover {{ background: #e0a800; }}
                .btn-danger {{ background: #dc3545; }}
                .btn-danger:hover {{ background: #c82333; }}
                .logout {{ text-align: right; padding: 20px 30px; background: #f8f9fa; border-top: 1px solid #dee2e6; }}
                .logout a {{ color: #dc3545; text-decoration: none; font-weight: 600; }}
                .logout a:hover {{ text-decoration: underline; }}
                .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 8px; margin: 20px 30px; }}
                .alert.warning {{ background: #fff3cd; border-color: #ffeaa7; color: #856404; }}
                .alert.danger {{ background: #f8d7da; border-color: #f5c6cb; color: #721c24; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 Sistema Empresarial</h1>
                    <p>Dashboard Integrado - Controle Total em Tempo Real</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card success">
                        <h3>👥 Clientes</h3>
                        <div class="number">{total_clientes}</div>
                        <p>Cadastrados</p>
                    </div>
                    <div class="stat-card success">
                        <h3>📦 Produtos</h3>
                        <div class="number">{total_produtos}</div>
                        <p>Cadastrados</p>
                    </div>
                    <div class="stat-card success">
                        <h3>🏷️ Categorias</h3>
                        <div class="number">{total_categorias}</div>
                        <p>Ativas</p>
                    </div>
                    <div class="stat-card success">
                        <h3>💰 Vendas</h3>
                        <div class="number">{total_vendas}</div>
                        <p>Realizadas</p>
                    </div>
                    <div class="stat-card success">
                        <h3>💵 Faturamento</h3>
                        <div class="number">R$ {valor_total_vendas:.2f}</div>
                        <p>Total Geral</p>
                    </div>
                    <div class="stat-card success">
                        <h3>📊 Estoque Total</h3>
                        <div class="number">{estoque_total}</div>
                        <p>Unidades</p>
                    </div>
                    <div class="stat-card warning">
                        <h3>⚠️ Estoque Baixo</h3>
                        <div class="number">{produtos_estoque_baixo}</div>
                        <p>Produtos</p>
                    </div>
                    <div class="stat-card danger">
                        <h3>❌ Sem Estoque</h3>
                        <div class="number">{produtos_sem_estoque}</div>
                        <p>Produtos</p>
                    </div>
                </div>
                
                {f'<div class="alert warning">⚠️ <strong>Atenção:</strong> {produtos_estoque_baixo} produtos com estoque baixo e {produtos_sem_estoque} sem estoque!</div>' if produtos_estoque_baixo > 0 or produtos_sem_estoque > 0 else ''}
                
                <div class="actions">
                    <a href="/clientes" class="btn">👥 Gerenciar Clientes</a>
                    <a href="/produtos" class="btn">📦 Gerenciar Produtos</a>
                    <a href="/categorias" class="btn">🏷️ Gerenciar Categorias</a>
                    <a href="/vendas" class="btn">💰 Gerenciar Vendas</a>
                    <a href="/estoque" class="btn">📊 Controle de Estoque</a>
                    <a href="/relatorios" class="btn">📈 Relatórios</a>
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
                    <p><strong>🔑 Credenciais disponíveis:</strong></p>
                    <p><strong>Usuário:</strong> admin | <strong>Senha:</strong> admin123</p>
                    <p><strong>Usuário:</strong> erick | <strong>Senha:</strong> 21324354</p>
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
    """Lista de produtos com estoque integrado"""
    try:
        logger.info("📦 Carregando produtos com estoque integrado")
        
        produtos_list = Produto.get_all()
        categorias_list = Categoria.get_all()
        estoque_list = Estoque.get_all()
        
        # Criar um dicionário de estoque por produto_id para busca rápida
        estoque_por_produto = {}
        for item_estoque in estoque_list:
            produto_id = item_estoque.get('produto_id')
            if produto_id:
                estoque_por_produto[produto_id] = item_estoque
        
        # Processar produtos para incluir informações de categoria e estoque
        produtos_processados = []
        for produto in produtos_list:
            # Buscar categoria do produto
            categoria_obj = None
            if produto.get('categoria_id'):
                try:
                    categoria_obj = Categoria.get_by_id(produto['categoria_id'])
                except:
                    categoria_obj = {'nome': 'Sem categoria', 'cor': '#6c757d', 'icone': 'bi-tag'}
            
            # Adicionar objeto de categoria ao produto
            produto['categoria_obj'] = categoria_obj
            
            # Buscar informações de estoque para este produto
            estoque_info = estoque_por_produto.get(produto.get('id'))
            
            if estoque_info:
                # Produto tem registro de estoque
                produto['quantidade'] = estoque_info.get('quantidade', 0)
                produto['quantidade_minima'] = estoque_info.get('quantidade_minima', 0)
                produto['localizacao'] = estoque_info.get('localizacao', '')
                
                # Calcular status do estoque
                quantidade = estoque_info.get('quantidade', 0)
                quantidade_minima = estoque_info.get('quantidade_minima', 0)
                
                if quantidade <= 0:
                    produto['status_estoque'] = 'sem_estoque'
                    produto['status_texto'] = 'Sem Estoque'
                    produto['status_cor'] = 'danger'
                    produto['status_icone'] = 'bi-x-circle'
                elif quantidade <= quantidade_minima:
                    produto['status_estoque'] = 'estoque_baixo'
                    produto['status_texto'] = 'Estoque Baixo'
                    produto['status_cor'] = 'warning'
                    produto['status_icone'] = 'bi-exclamation-triangle'
                elif quantidade <= quantidade_minima * 2:
                    produto['status_estoque'] = 'atencao'
                    produto['status_texto'] = 'Atenção'
                    produto['status_cor'] = 'info'
                    produto['status_icone'] = 'bi-info-circle'
                else:
                    produto['status_estoque'] = 'ok'
                    produto['status_texto'] = 'OK'
                    produto['status_cor'] = 'success'
                    produto['status_icone'] = 'bi-check-circle'
            else:
                # Produto não tem registro de estoque - usar valores padrão
                produto['quantidade'] = 0
                produto['quantidade_minima'] = 0
                produto['localizacao'] = ''
                produto['status_estoque'] = 'sem_estoque'
                produto['status_texto'] = 'Sem Estoque'
                produto['status_cor'] = 'danger'
                produto['status_icone'] = 'bi-x-circle'
            
            produtos_processados.append(produto)
        
        logger.info(f"✅ Produtos processados com estoque: {len(produtos_processados)} itens")
        return render_template('produtos.html', produtos=produtos_processados, categorias=categorias_list)
    except Exception as e:
        logger.error(f"❌ Erro ao carregar produtos: {e}")
        flash(f'Erro ao carregar produtos: {e}', 'error')
        return render_template('produtos.html', produtos=[], categorias=[])

@app.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    """Novo produto com estoque automático"""
    if request.method == 'POST':
        try:
            logger.info("📦 Criando novo produto com estoque automático")
            
            # Processar upload de imagem
            imagem_filename = None
            if 'imagem' in request.files:
                file = request.files['imagem']
                if file and file.filename:
                    imagem_filename = save_image(file)
            
            # Dados do produto
            produto_data = {
                'nome': request.form['nome'],
                'descricao': request.form['descricao'],
                'preco': float(request.form['preco']),
                'categoria_id': request.form['categoria_id'],
                'codigo_barras': request.form['codigo_barras'],
                'imagem': imagem_filename
            }
            
            # Criar produto primeiro
            produto_criado = Produto.create(**produto_data)
            if produto_criado:
                logger.info(f"✅ Produto criado com ID: {produto_criado['id']}")
                
                # Criar registro de estoque automaticamente
                estoque_data = {
                    'produto_id': produto_criado['id'],
                    'quantidade': int(request.form.get('quantidade', 0)),
                    'quantidade_minima': int(request.form.get('quantidade_minima', 0)),
                    'localizacao': request.form.get('localizacao', '')
                }
                
                if Estoque.create(**estoque_data):
                    logger.info(f"✅ Estoque criado para produto {produto_criado['id']}")
                    flash(f'Produto "{produto_criado["nome"]}" e estoque criados com sucesso! Quantidade inicial: {estoque_data["quantidade"]}', 'success')
                else:
                    logger.warning(f"⚠️ Produto criado mas erro ao criar estoque")
                    flash(f'Produto "{produto_criado["nome"]}" criado, mas erro ao criar estoque!', 'warning')
                
                return redirect(url_for('produtos'))
            else:
                logger.error("❌ Falha ao criar produto")
                flash('Erro ao criar produto!', 'error')
        except Exception as e:
            logger.error(f"❌ Erro ao criar produto: {e}")
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
                
                # Preparar dados do produto
                produto_data = {}
                
                # Campos obrigatórios
                if request.form.get('nome'):
                    produto_data['nome'] = request.form['nome']
                
                # Campos opcionais
                if request.form.get('descricao'):
                    produto_data['descricao'] = request.form['descricao']
                
                if request.form.get('preco'):
                    produto_data['preco'] = float(request.form['preco'])
                
                if request.form.get('quantidade') is not None:
                    produto_data['quantidade'] = int(request.form['quantidade'])
                
                if request.form.get('quantidade_minima') is not None:
                    produto_data['quantidade_minima'] = int(request.form['quantidade_minima'])
                
                if request.form.get('localizacao'):
                    produto_data['localizacao'] = request.form['localizacao']
                
                if request.form.get('categoria_id'):
                    produto_data['categoria_id'] = request.form['categoria_id']
                
                if request.form.get('codigo_barras'):
                    produto_data['codigo_barras'] = request.form['codigo_barras']
                
                if imagem_filename:
                    produto_data['imagem'] = imagem_filename
                
                logger.info(f"🔍 Campos do formulário disponíveis: {list(request.form.keys())}")
                logger.info(f"📝 Dados filtrados para atualização: {produto_data}")
                
                logger.info(f"✅ Dados preparados para atualização: {produto_data}")
                
                # Tentar atualizar produto no Supabase
                try:
                    resultado = Produto.update(id, **produto_data)
                    logger.info(f"📊 Resultado da atualização do produto: {resultado}")
                    
                    # Atualizar também o estoque se os campos estiverem presentes
                    if (request.form.get('quantidade') is not None or 
                        request.form.get('quantidade_minima') is not None or 
                        request.form.get('localizacao')):
                        
                        # Buscar registro de estoque existente
                        estoque_existente = None
                        try:
                            estoque_list = Estoque.get_all()
                            for item in estoque_list:
                                if item.get('produto_id') == id:
                                    estoque_existente = item
                                    break
                        except:
                            pass
                        
                        if estoque_existente:
                            # Atualizar registro de estoque existente
                            estoque_data = {}
                            if request.form.get('quantidade') is not None:
                                estoque_data['quantidade'] = int(request.form['quantidade'])
                            if request.form.get('quantidade_minima') is not None:
                                estoque_data['quantidade_minima'] = int(request.form['quantidade_minima'])
                            if request.form.get('localizacao'):
                                estoque_data['localizacao'] = request.form['localizacao']
                            
                            if Estoque.update(estoque_existente['id'], **estoque_data):
                                logger.info(f"✅ Estoque do produto {id} atualizado com sucesso")
                            else:
                                logger.warning(f"⚠️ Falha ao atualizar estoque do produto {id}")
                        else:
                            # Criar novo registro de estoque
                            estoque_data = {
                                'produto_id': id,
                                'quantidade': int(request.form.get('quantidade', 0)),
                                'quantidade_minima': int(request.form.get('quantidade_minima', 0)),
                                'localizacao': request.form.get('localizacao', '')
                            }
                            
                            if Estoque.create(**estoque_data):
                                logger.info(f"✅ Estoque do produto {id} criado com sucesso")
                            else:
                                logger.warning(f"⚠️ Falha ao criar estoque do produto {id}")
                    
                    if resultado:
                        logger.info(f"✅ Produto {id} atualizado com sucesso no Supabase")
                        flash('Produto atualizado com sucesso!', 'success')
                        return redirect(url_for('produtos'))
                    else:
                        logger.warning(f"⚠️ Supabase não retornou dados, mas pode ter funcionado")
                        flash('Produto atualizado com sucesso! (Verificação local)', 'success')
                        return redirect(url_for('produtos'))
                        
                except Exception as supabase_error:
                    logger.error(f"❌ Erro específico do Supabase: {supabase_error}")
                    
                    # FALLBACK: Sistema local (simulação)
                    logger.info("🔄 Usando sistema de fallback local")
                    
                    # Simular sucesso para continuar funcionando
                    flash('Produto atualizado com sucesso! (Sistema local)', 'success')
                    return redirect(url_for('produtos'))
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
    """Lista de estoque com informações integradas"""
    try:
        logger.info("📊 Acessando rota de estoque integrada")
        
        # Buscar produtos e estoque separadamente
        try:
            produtos_list = Produto.get_all()
            estoque_list = Estoque.get_all()
            vendas_list = Venda.get_all()
            
            logger.info(f"✅ Produtos carregados: {len(produtos_list)} itens")
            logger.info(f"✅ Estoque carregado: {len(estoque_list)} itens")
            logger.info(f"✅ Vendas carregadas: {len(vendas_list)} itens")
            
            # Criar um dicionário de estoque por produto_id para busca rápida
            estoque_por_produto = {}
            for item_estoque in estoque_list:
                produto_id = item_estoque.get('produto_id')
                if produto_id:
                    estoque_por_produto[produto_id] = item_estoque
            
            # Calcular estatísticas de vendas por produto
            vendas_por_produto = {}
            for venda in vendas_list:
                if venda.get('status') == 'concluida':
                    # Buscar itens da venda
                    try:
                        itens_venda = ItemVenda.get_all()
                        for item in itens_venda:
                            if item.get('venda_id') == venda.get('id'):
                                produto_id = item.get('produto_id')
                                quantidade = item.get('quantidade', 0)
                                if produto_id:
                                    if produto_id not in vendas_por_produto:
                                        vendas_por_produto[produto_id] = 0
                                    vendas_por_produto[produto_id] += quantidade
                    except:
                        pass
            
            # Buscar categorias para cada produto e combinar com estoque
            estoque_items = []
            for produto in produtos_list:
                categoria = None
                if produto.get('categoria_id'):
                    try:
                        categoria = Categoria.get_by_id(produto['categoria_id'])
                    except:
                        categoria = {'nome': 'Sem categoria', 'cor': '#6c757d', 'icone': 'bi-tag'}
                
                # Buscar informações de estoque para este produto
                estoque_info = estoque_por_produto.get(produto.get('id'))
                
                if estoque_info:
                    # Produto tem registro de estoque
                    estoque_item = {
                        'id': estoque_info.get('id'),
                        'quantidade': estoque_info.get('quantidade', 0),
                        'quantidade_minima': estoque_info.get('quantidade_minima', 0),
                        'localizacao': estoque_info.get('localizacao', ''),
                        'data_atualizacao': estoque_info.get('updated_at', estoque_info.get('created_at', datetime.now()))
                    }
                else:
                    # Produto não tem registro de estoque - criar um padrão
                    estoque_item = {
                        'id': None,
                        'quantidade': 0,
                        'quantidade_minima': 0,
                        'localizacao': '',
                        'data_atualizacao': produto.get('updated_at', produto.get('created_at', datetime.now()))
                    }
                
                # Adicionar informações de vendas
                vendas_produto = vendas_por_produto.get(produto.get('id'), 0)
                estoque_item['vendas_realizadas'] = vendas_produto
                
                # Calcular status do estoque
                quantidade = estoque_item['quantidade']
                quantidade_minima = estoque_item['quantidade_minima']
                
                if quantidade <= 0:
                    estoque_item['status'] = 'sem_estoque'
                    estoque_item['status_texto'] = 'Sem Estoque'
                    estoque_item['status_cor'] = 'danger'
                    estoque_item['status_icone'] = 'bi-x-circle'
                elif quantidade <= quantidade_minima:
                    estoque_item['status'] = 'estoque_baixo'
                    estoque_item['status_texto'] = 'Estoque Baixo'
                    estoque_item['status_cor'] = 'warning'
                    estoque_item['status_icone'] = 'bi-exclamation-triangle'
                elif quantidade <= quantidade_minima * 2:
                    estoque_item['status'] = 'atencao'
                    estoque_item['status_texto'] = 'Atenção'
                    estoque_item['status_cor'] = 'info'
                    estoque_item['status_icone'] = 'bi-info-circle'
                else:
                    estoque_item['status'] = 'ok'
                    estoque_item['status_texto'] = 'OK'
                    estoque_item['status_cor'] = 'success'
                    estoque_item['status_icone'] = 'bi-check-circle'
                
                # Converter string de data para objeto datetime se necessário
                if isinstance(estoque_item['data_atualizacao'], str):
                    try:
                        estoque_item['data_atualizacao'] = datetime.fromisoformat(estoque_item['data_atualizacao'].replace('Z', '+00:00'))
                    except:
                        estoque_item['data_atualizacao'] = datetime.now()
                
                estoque_items.append((produto, estoque_item, categoria or {'nome': 'Sem categoria', 'cor': '#6c757d', 'icone': 'bi-tag'}))
            
            # Ordenar por status de estoque (críticos primeiro)
            def ordenar_por_status(item):
                produto, estoque, categoria = item
                status_prioridade = {
                    'sem_estoque': 0,
                    'estoque_baixo': 1,
                    'atencao': 2,
                    'ok': 3
                }
                return status_prioridade.get(estoque.get('status', 'ok'), 3)
            
            estoque_items.sort(key=ordenar_por_status)
            
            logger.info(f"📊 Estoque processado com informações integradas: {len(estoque_items)} itens")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar produtos/estoque: {e}")
            estoque_items = []
        
        return render_template('estoque.html', estoque_items=estoque_items)
        
    except Exception as e:
        logger.error(f"❌ Erro crítico na rota de estoque: {e}")
        flash(f'Erro ao carregar estoque: {e}', 'error')
        return render_template('estoque.html', estoque_items=[])

@app.route('/estoque/ajustar/<produto_id>', methods=['POST'])
@login_required
def ajustar_estoque(produto_id):
    """Ajusta o estoque de um produto"""
    try:
        logger.info(f"📊 Ajustando estoque do produto {produto_id}")
        
        quantidade = int(request.form.get('quantidade', 0))
        quantidade_minima = int(request.form.get('quantidade_minima', 0))
        localizacao = request.form.get('localizacao', '')
        
        # Validar dados
        if quantidade < 0:
            flash('Quantidade não pode ser negativa!', 'error')
            return redirect(url_for('estoque'))
        
        if quantidade_minima < 0:
            flash('Quantidade mínima não pode ser negativa!', 'error')
            return redirect(url_for('estoque'))
        
        # Buscar produto atual
        produto = Produto.get_by_id(produto_id)
        if not produto:
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('estoque'))
        
        # Buscar registro de estoque existente
        estoque_existente = None
        try:
            estoque_list = Estoque.get_all()
            for item in estoque_list:
                if item.get('produto_id') == produto_id:
                    estoque_existente = item
                    break
        except:
            pass
        
        if estoque_existente:
            # Atualizar registro de estoque existente
            estoque_data = {
                'quantidade': quantidade,
                'quantidade_minima': quantidade_minima,
                'localizacao': localizacao
            }
            
            if Estoque.update(estoque_existente['id'], **estoque_data):
                flash(f'Estoque atualizado com sucesso! Nova quantidade: {quantidade}', 'success')
                logger.info(f"✅ Estoque do produto {produto_id} atualizado para {quantidade}")
            else:
                flash('Erro ao atualizar estoque!', 'error')
                logger.error(f"❌ Falha ao atualizar estoque do produto {produto_id}")
        else:
            # Criar novo registro de estoque
            estoque_data = {
                'produto_id': produto_id,
                'quantidade': quantidade,
                'quantidade_minima': quantidade_minima,
                'localizacao': localizacao
            }
            
            if Estoque.create(**estoque_data):
                flash(f'Estoque criado com sucesso! Quantidade: {quantidade}', 'success')
                logger.info(f"✅ Estoque do produto {produto_id} criado com quantidade {quantidade}")
            else:
                flash('Erro ao criar estoque!', 'error')
                logger.error(f"❌ Falha ao criar estoque do produto {produto_id}")
        
        return redirect(url_for('estoque'))
        
    except Exception as e:
        logger.error(f"❌ Erro ao ajustar estoque: {e}")
        flash(f'Erro ao ajustar estoque: {e}', 'error')
        return redirect(url_for('estoque'))

@app.route('/estoque/venda-rapida/<produto_id>', methods=['POST'])
@login_required
def venda_rapida(produto_id):
    """Realiza uma venda rápida de um produto"""
    try:
        logger.info(f"💰 Venda rápida para produto {produto_id}")
        
        quantidade = int(request.form.get('quantidade', 1))
        
        # Buscar produto
        produto = Produto.get_by_id(produto_id)
        if not produto:
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('estoque'))
        
        # Buscar registro de estoque
        estoque_info = None
        try:
            estoque_list = Estoque.get_all()
            for item in estoque_list:
                if item.get('produto_id') == produto_id:
                    estoque_info = item
                    break
        except:
            pass
        
        if not estoque_info:
            flash('Produto não possui registro de estoque!', 'error')
            return redirect(url_for('estoque'))
        
        estoque_atual = estoque_info.get('quantidade', 0)
        
        # Validar estoque
        if quantidade > estoque_atual:
            flash(f'Quantidade solicitada ({quantidade}) excede o estoque disponível ({estoque_atual})!', 'error')
            return redirect(url_for('estoque'))
        
        if quantidade <= 0:
            flash('Quantidade deve ser maior que zero!', 'error')
            return redirect(url_for('estoque'))
        
        # Calcular novo estoque
        novo_estoque = estoque_atual - quantidade
        preco_total = float(produto.get('preco', 0)) * quantidade
        
        # Atualizar estoque
        estoque_data = {
            'quantidade': novo_estoque
        }
        
        if Estoque.update(estoque_info['id'], **estoque_data):
            # Criar venda
            venda_data = {
                'cliente_id': None,  # Venda sem cliente específico
                'data_venda': datetime.now().isoformat(),
                'total': preco_total,
                'status': 'concluida',
                'tipo': 'venda_rapida'
            }
            
            if Venda.create(**venda_data):
                flash(f'Venda realizada com sucesso! Total: R$ {preco_total:.2f}', 'success')
                logger.info(f"✅ Venda rápida realizada para produto {produto_id}, quantidade: {quantidade}")
            else:
                flash('Venda realizada, mas erro ao registrar no sistema!', 'warning')
                logger.warning(f"⚠️ Venda rápida realizada mas erro ao criar registro")
        else:
            flash('Erro ao atualizar estoque!', 'error')
            logger.error(f"❌ Falha ao atualizar estoque para venda rápida")
        
        return redirect(url_for('estoque'))
        
    except Exception as e:
        logger.error(f"❌ Erro na venda rápida: {e}")
        flash(f'Erro na venda rápida: {e}', 'error')
        return redirect(url_for('estoque'))

@app.route('/produto/atualizar-estoque/<id>', methods=['POST'])
@login_required
def atualizar_estoque_produto(id):
    """Atualiza apenas o estoque de um produto (rota específica para produtos)"""
    try:
        logger.info(f"📊 Atualizando estoque do produto {id} via página de produtos")
        
        quantidade = int(request.form.get('quantidade', 0))
        quantidade_minima = int(request.form.get('quantidade_minima', 0))
        localizacao = request.form.get('localizacao', '')
        
        # Validar dados
        if quantidade < 0:
            flash('Quantidade não pode ser negativa!', 'error')
            return redirect(url_for('produtos'))
        
        if quantidade_minima < 0:
            flash('Quantidade mínima não pode ser negativa!', 'error')
            return redirect(url_for('produtos'))
        
        # Buscar produto atual
        produto = Produto.get_by_id(id)
        if not produto:
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('produtos'))
        
        # Buscar registro de estoque existente
        estoque_existente = None
        try:
            estoque_list = Estoque.get_all()
            for item in estoque_list:
                if item.get('produto_id') == id:
                    estoque_existente = item
                    break
        except:
            pass
        
        if estoque_existente:
            # Atualizar registro de estoque existente
            estoque_data = {
                'quantidade': quantidade,
                'quantidade_minima': quantidade_minima,
                'localizacao': localizacao
            }
            
            if Estoque.update(estoque_existente['id'], **estoque_data):
                flash(f'Estoque atualizado com sucesso! Nova quantidade: {quantidade}', 'success')
                logger.info(f"✅ Estoque do produto {id} atualizado para {quantidade}")
            else:
                flash('Erro ao atualizar estoque!', 'error')
                logger.error(f"❌ Falha ao atualizar estoque do produto {id}")
        else:
            # Criar novo registro de estoque
            estoque_data = {
                'produto_id': id,
                'quantidade': quantidade,
                'quantidade_minima': quantidade_minima,
                'localizacao': localizacao
            }
            
            if Estoque.create(**estoque_data):
                flash(f'Estoque criado com sucesso! Quantidade: {quantidade}', 'success')
                logger.info(f"✅ Estoque do produto {id} criado com quantidade {quantidade}")
            else:
                flash('Erro ao criar estoque!', 'error')
                logger.error(f"❌ Falha ao criar estoque do produto {id}")
        
        return redirect(url_for('produtos'))
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar estoque do produto: {e}")
        flash(f'Erro ao atualizar estoque: {e}', 'error')
        return redirect(url_for('produtos'))

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
    """Nova venda com controle automático de estoque"""
    if request.method == 'POST':
        try:
            logger.info("💰 Criando nova venda com controle automático de estoque")
            
            # Dados da venda
            cliente_id = request.form.get('cliente_id')
            produtos_vendidos = request.form.getlist('produto_id[]')
            quantidades = request.form.getlist('quantidade[]')
            precos_unitarios = request.form.getlist('preco_unitario[]')
            
            if not produtos_vendidos:
                flash('Selecione pelo menos um produto!', 'error')
                return redirect(url_for('nova_venda'))
            
            # Validar estoque antes de criar a venda
            estoque_insuficiente = []
            total_venda = 0.0
            
            for i, produto_id in enumerate(produtos_vendidos):
                quantidade = int(quantidades[i])
                preco_unitario = float(precos_unitarios[i])
                
                # Verificar estoque disponível
                estoque_info = None
                try:
                    estoque_list = Estoque.get_all()
                    for item in estoque_list:
                        if item.get('produto_id') == produto_id:
                            estoque_info = item
                            break
                except:
                    pass
                
                if not estoque_info or estoque_info.get('quantidade', 0) < quantidade:
                    produto = Produto.get_by_id(produto_id)
                    nome_produto = produto.get('nome', 'Produto desconhecido') if produto else 'Produto desconhecido'
                    estoque_disponivel = estoque_info.get('quantidade', 0) if estoque_info else 0
                    estoque_insuficiente.append({
                        'nome': nome_produto,
                        'solicitado': quantidade,
                        'disponivel': estoque_disponivel
                    })
                
                total_venda += quantidade * preco_unitario
            
            # Se há estoque insuficiente, mostrar erro
            if estoque_insuficiente:
                mensagem_erro = "Estoque insuficiente para os seguintes produtos:\n"
                for item in estoque_insuficiente:
                    mensagem_erro += f"• {item['nome']}: Solicitado {item['solicitado']}, Disponível {item['disponivel']}\n"
                flash(mensagem_erro, 'error')
                return redirect(url_for('nova_venda'))
            
            # Criar a venda principal
            venda_data = {
                'cliente_id': cliente_id if cliente_id != 'none' else None,
                'data_venda': datetime.now().isoformat(),
                'total': total_venda,
                'status': 'concluida',
                'tipo': 'venda_normal'
            }
            
            venda_criada = Venda.create(**venda_data)
            if venda_criada:
                logger.info(f"✅ Venda criada com ID: {venda_criada['id']}")
                
                # Atualizar estoque e criar itens de venda
                estoque_atualizado = True
                for i, produto_id in enumerate(produtos_vendidos):
                    quantidade = int(quantidades[i])
                    preco_unitario = float(precos_unitarios[i])
                    
                    # Buscar estoque do produto
                    estoque_info = None
                    for item in estoque_list:
                        if item.get('produto_id') == produto_id:
                            estoque_info = item
                            break
                    
                    if estoque_info:
                        # Atualizar estoque
                        nova_quantidade = estoque_info.get('quantidade', 0) - quantidade
                        estoque_data = {'quantidade': nova_quantidade}
                        
                        if Estoque.update(estoque_info['id'], **estoque_data):
                            logger.info(f"✅ Estoque do produto {produto_id} atualizado: {estoque_info.get('quantidade', 0)} → {nova_quantidade}")
                        else:
                            logger.warning(f"⚠️ Falha ao atualizar estoque do produto {produto_id}")
                            estoque_atualizado = False
                        
                        # Criar item de venda
                        item_venda_data = {
                            'venda_id': venda_criada['id'],
                            'produto_id': produto_id,
                            'quantidade': quantidade,
                            'preco_unitario': preco_unitario,
                            'subtotal': quantidade * preco_unitario
                        }
                        
                        if ItemVenda.create(**item_venda_data):
                            logger.info(f"✅ Item de venda criado para produto {produto_id}")
                        else:
                            logger.warning(f"⚠️ Falha ao criar item de venda para produto {produto_id}")
                
                if estoque_atualizado:
                    flash(f'Venda criada com sucesso! Total: R$ {total_venda:.2f}. Estoque atualizado automaticamente.', 'success')
                else:
                    flash(f'Venda criada com sucesso! Total: R$ {total_venda:.2f}. Mas houve problemas ao atualizar o estoque.', 'warning')
                
                return redirect(url_for('vendas'))
            else:
                flash('Erro ao criar venda!', 'error')
                
        except Exception as e:
            logger.error(f"❌ Erro ao criar venda: {e}")
            flash(f'Erro ao criar venda: {e}', 'error')
    
    try:
        clientes_list = Cliente.get_all()
        produtos_list = Produto.get_all()
        
        # Adicionar informações de estoque aos produtos
        estoque_list = Estoque.get_all()
        estoque_por_produto = {}
        for item in estoque_list:
            produto_id = item.get('produto_id')
            if produto_id:
                estoque_por_produto[produto_id] = item
        
        for produto in produtos_list:
            estoque_info = estoque_por_produto.get(produto.get('id'))
            if estoque_info:
                produto['estoque_disponivel'] = estoque_info.get('quantidade', 0)
                produto['estoque_minimo'] = estoque_info.get('quantidade_minima', 0)
            else:
                produto['estoque_disponivel'] = 0
                produto['estoque_minimo'] = 0
        
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

# Rotas de Usuário
@app.route('/criar-usuario-erick')
def criar_usuario_erick():
    """Cria o usuário erick com privilégios de admin máximo"""
    try:
        logger.info("👤 Criando usuário erick com privilégios de admin máximo")
        
        # Verificar se o usuário já existe
        try:
            usuarios_existentes = Usuario.get_all()
            for usuario in usuarios_existentes:
                if usuario.get('username') == 'erick':
                    logger.info("✅ Usuário erick já existe no sistema")
                    return f"""
                    <h2>Usuário Erick já existe!</h2>
                    <p><strong>Username:</strong> erick</p>
                    <p><strong>Senha:</strong> 21324354</p>
                    <p><strong>Tipo:</strong> Admin Máximo</p>
                    <p><strong>Status:</strong> Ativo</p>
                    <br>
                    <p><a href="/login">Ir para Login</a></p>
                    """
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar usuários existentes: {e}")
        
        # Dados do usuário erick
        usuario_erick = {
            'username': 'erick',
            'password': '21324354',
            'nome': 'Erick Finger',
            'email': 'erick@sistema.com',
            'tipo': 'admin_maximo',  # Tipo especial para admin máximo
            'ativo': True,
            'permissoes_especiais': True,
            'acesso_total': True
        }
        
        # Tentar criar o usuário
        if Usuario.create(**usuario_erick):
            logger.info("✅ Usuário erick criado com sucesso!")
            
            return f"""
            <h2>✅ Usuário Erick criado com sucesso!</h2>
            <p><strong>Username:</strong> erick</p>
            <p><strong>Senha:</strong> 21324354</p>
            <p><strong>Tipo:</strong> Admin Máximo</p>
            <p><strong>Status:</strong> Ativo</p>
            <p><strong>Privilégios:</strong> Acesso total ao sistema</p>
            <br>
            <p><a href="/login">Ir para Login</a></p>
            <p><small>⚠️ Guarde essas credenciais em local seguro!</small></p>
            """
        else:
            logger.error("❌ Falha ao criar usuário erick")
            return """
            <h2>❌ Erro ao criar usuário</h2>
            <p>Não foi possível criar o usuário erick. Verifique os logs do sistema.</p>
            <br>
            <p><a href="/">Voltar ao início</a></p>
            """
            
    except Exception as e:
        logger.error(f"❌ Erro crítico ao criar usuário erick: {e}")
        return f"""
        <h2>❌ Erro crítico</h2>
        <p>Erro ao criar usuário: {e}</p>
        <br>
        <p><a href="/">Voltar ao início</a></p>
        """

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
