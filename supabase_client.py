#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente Supabase para o Sistema Empresarial
"""

from supabase import create_client, Client
from config_producao import config
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseManager:
    """Gerenciador de conexão com Supabase"""
    
    def __init__(self):
        """Inicializa o cliente Supabase"""
        try:
            self.client: Client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_KEY
            )
            logger.info("✅ Cliente Supabase conectado com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com Supabase: {e}")
            self.client = None
    
    def test_connection(self):
        """Testa a conexão com o Supabase"""
        try:
            if self.client:
                # Tenta fazer uma consulta simples
                response = self.client.table('usuarios').select('*').limit(1).execute()
                logger.info("✅ Conexão com Supabase funcionando!")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erro no teste de conexão: {e}")
            return False
    
    def get_table(self, table_name: str):
        """Retorna uma referência para uma tabela"""
        try:
            if self.client:
                logger.info(f"🔍 Obtendo tabela: {table_name}")
                table = self.client.table(table_name)
                logger.info(f"✅ Tabela {table_name} obtida com sucesso")
                return table
            else:
                logger.error(f"❌ Cliente Supabase não disponível")
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao obter tabela {table_name}: {e}")
            return None

# Instância global
supabase = SupabaseManager()

def get_supabase_client():
    """Retorna o cliente Supabase"""
    return supabase.client

def get_table(table_name: str):
    """Retorna uma referência para uma tabela"""
    return supabase.get_table(table_name)
