#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações específicas para o Render
"""

import os

class Config:
    """Configurações para produção no Render"""
    
    # Configurações básicas
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sua_chave_secreta_muito_segura_aqui_123456789')
    DEBUG = False
    TESTING = False
    
    # Configurações do Supabase
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos
    SESSION_COOKIE_SECURE = False  # Render pode não ter HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Configurações de upload
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Configurações de logging
    LOG_LEVEL = 'INFO'
    
    # Usuários padrão para o Render
    DEFAULT_USERS = [
        {
            'username': 'admin',
            'password': 'admin123',
            'nome': 'Administrador',
            'email': 'admin@sistema.com',
            'cargo': 'Administrador',
            'ativo': True
        },
        {
            'username': 'erick',
            'password': '21324354',
            'nome': 'Erick Finger',
            'email': 'erick@sistema.com',
            'cargo': 'Admin Máximo',
            'ativo': True
        }
    ]
    
    # Configurações de segurança
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf_secret_key_123456789')
    
    # Configurações de banco de dados
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Configurações de email (se necessário)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configurações de rate limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'memory://'
    
    # Configurações de monitoramento
    ENABLE_MONITORING = True
    LOG_REQUESTS = True
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações específicas da aplicação"""
        pass

class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Configurações para produção"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    
    # Configurações de segurança para produção
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True

class TestingConfig(Config):
    """Configurações para testes"""
    TESTING = True
    WTF_CSRF_ENABLED = False

# Configuração padrão baseada no ambiente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Configuração ativa baseada na variável de ambiente
def get_config():
    """Retorna a configuração ativa baseada no ambiente"""
    env = os.environ.get('FLASK_ENV', 'production')
    return config.get(env, config['default'])
