#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações para Produção - Sistema Empresarial
"""

import os

class Config:
    """Configurações do sistema"""
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://txylasunasazzcyvchfe.supabase.co')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'sb_secret_-iHi5o-WP76kpTWev7bQYA_49UtmLdL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'COLE_SUA_CHAVE_SERVICE_ROLE_AQUI')
    
    # Configurações de segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua_chave_secreta_muito_segura_aqui_123456789')
    
    # Configurações do Flask
    FLASK_ENV = 'production'
    DEBUG = False
    
    # Configurações de upload
    UPLOAD_FOLDER = '/tmp/uploads'  # Render usa sistema temporário
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Configurações de sessão
    SESSION_COOKIE_SECURE = False  # Render pode não ter HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

# Configuração ativa
config = Config()
