#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos para Supabase - Sistema Empresarial
"""

from supabase_client import get_table
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class BaseModel:
    """Classe base para todos os modelos"""
    
    @classmethod
    def get_table(cls):
        """Retorna a tabela do Supabase"""
        return get_table(cls.__tablename__)
    
    @classmethod
    def create(cls, **data):
        """Cria um novo registro"""
        try:
            table = cls.get_table()
            if table:
                # Adiciona timestamps se não existirem
                if 'created_at' not in data:
                    data['created_at'] = datetime.utcnow().isoformat()
                if 'updated_at' not in data:
                    data['updated_at'] = datetime.utcnow().isoformat()
                
                response = table.insert(data).execute()
                logger.info(f"✅ {cls.__name__} criado com sucesso")
                return response.data[0] if response.data else None
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao criar {cls.__name__}: {e}")
            return None
    
    @classmethod
    def get_by_id(cls, id):
        """Busca um registro por ID"""
        try:
            table = cls.get_table()
            if table:
                response = table.select('*').eq('id', id).execute()
                return response.data[0] if response.data else None
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar {cls.__name__} por ID: {e}")
            return None
    
    @classmethod
    def get_all(cls, active_only=True):
        """Busca todos os registros"""
        try:
            table = cls.get_table()
            if table:
                query = table.select('*')
                if active_only and hasattr(cls, 'ativo'):
                    query = query.eq('ativo', True)
                response = query.execute()
                return response.data if response.data else []
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar todos {cls.__name__}: {e}")
            return []
    
    @classmethod
    def update(cls, id, **data):
        """Atualiza um registro"""
        try:
            table = cls.get_table()
            if table:
                # Adiciona timestamp de atualização
                data['updated_at'] = datetime.utcnow().isoformat()
                
                response = table.update(data).eq('id', id).execute()
                logger.info(f"✅ {cls.__name__} atualizado com sucesso")
                return response.data[0] if response.data else None
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar {cls.__name__}: {e}")
            return None
    
    @classmethod
    def delete(cls, id, soft_delete=True):
        """Remove um registro (soft delete por padrão)"""
        try:
            table = cls.get_table()
            if table:
                if soft_delete and hasattr(cls, 'ativo'):
                    # Soft delete
                    response = table.update({'ativo': False, 'updated_at': datetime.utcnow().isoformat()}).eq('id', id).execute()
                else:
                    # Hard delete
                    response = table.delete().eq('id', id).execute()
                
                logger.info(f"✅ {cls.__name__} removido com sucesso")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao remover {cls.__name__}: {e}")
            return False

class Usuario(BaseModel):
    """Modelo de Usuário"""
    __tablename__ = 'usuarios'
    
    @classmethod
    def authenticate(cls, username, password):
        """Autentica um usuário"""
        try:
            table = cls.get_table()
            if table:
                response = table.select('*').eq('username', username).eq('ativo', True).execute()
                user = response.data[0] if response.data else None
                
                if user and user.get('password') == password:  # Em produção, use hash
                    return user
                return None
            return None
        except Exception as e:
            logger.error(f"❌ Erro na autenticação: {e}")
            return None

class Cliente(BaseModel):
    """Modelo de Cliente"""
    __tablename__ = 'clientes'
    
    @classmethod
    def search_by_name(cls, name):
        """Busca clientes por nome"""
        try:
            table = cls.get_table()
            if table:
                response = table.select('*').ilike('nome', f'%{name}%').eq('ativo', True).execute()
                return response.data if response.data else []
            return []
        except Exception as e:
            logger.error(f"❌ Erro na busca de clientes: {e}")
            return []

class Categoria(BaseModel):
    """Modelo de Categoria"""
    __tablename__ = 'categorias'

class Produto(BaseModel):
    """Modelo de Produto"""
    __tablename__ = 'produtos'
    
    @classmethod
    def get_by_category(cls, categoria_id):
        """Busca produtos por categoria"""
        try:
            table = cls.get_table()
            if table:
                response = table.select('*').eq('categoria_id', categoria_id).eq('ativo', True).execute()
                return response.data if response.data else []
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar produtos por categoria: {e}")
            return []

class Estoque(BaseModel):
    """Modelo de Estoque"""
    __tablename__ = 'estoque'
    
    @classmethod
    def get_low_stock(cls, limit=10):
        """Busca produtos com estoque baixo"""
        try:
            table = cls.get_table()
            if table:
                response = table.select('*, produtos(*)').lte('quantidade', 'quantidade_minima').limit(limit).execute()
                return response.data if response.data else []
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar estoque baixo: {e}")
            return []

class Venda(BaseModel):
    """Modelo de Venda"""
    __tablename__ = 'vendas'
    
    @classmethod
    def get_sales_summary(cls, days=30):
        """Busca resumo de vendas dos últimos dias"""
        try:
            table = cls.get_table()
            if table:
                from datetime import datetime, timedelta
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                response = table.select('*').gte('data_venda', start_date).execute()
                return response.data if response.data else []
            return []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar resumo de vendas: {e}")
            return []

class ItemVenda(BaseModel):
    """Modelo de Item de Venda"""
    __tablename__ = 'itens_venda'
