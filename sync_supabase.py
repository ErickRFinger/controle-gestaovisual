#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Sincronização Bidirecional entre Flask e Supabase
"""

import time
import threading
from datetime import datetime, timedelta
from supabase_client import supabase
from models_supabase import Cliente, Categoria, Produto, Estoque, Venda, ItemVenda
import logging

logger = logging.getLogger(__name__)

class SupabaseSync:
    """Sistema de sincronização bidirecional"""
    
    def __init__(self):
        self.last_sync = {}
        self.sync_interval = 30  # Sincronizar a cada 30 segundos
        self.running = False
        self.sync_thread = None
        
        # Inicializar timestamps de última sincronização
        self.last_sync = {
            'clientes': datetime.now() - timedelta(minutes=5),
            'categorias': datetime.now() - timedelta(minutes=5),
            'produtos': datetime.now() - timedelta(minutes=5),
            'estoque': datetime.now() - timedelta(minutes=5),
            'vendas': datetime.now() - timedelta(minutes=5)
        }
    
    def start_sync(self):
        """Inicia a sincronização automática"""
        if not self.running:
            self.running = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            logger.info("🔄 Sincronização automática iniciada!")
    
    def stop_sync(self):
        """Para a sincronização automática"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join()
        logger.info("⏹️ Sincronização automática parada!")
    
    def _sync_loop(self):
        """Loop principal de sincronização"""
        while self.running:
            try:
                self.sync_all()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Erro no loop de sincronização: {e}")
                time.sleep(10)  # Espera 10 segundos em caso de erro
    
    def sync_all(self):
        """Sincroniza todas as tabelas"""
        logger.debug("🔄 Iniciando sincronização completa...")
        
        try:
            # Sincronizar cada tabela
            self.sync_clientes()
            self.sync_categorias()
            self.sync_produtos()
            self.sync_estoque()
            self.sync_vendas()
            
            logger.debug("✅ Sincronização completa concluída!")
            
        except Exception as e:
            logger.error(f"❌ Erro na sincronização: {e}")
    
    def sync_clientes(self):
        """Sincroniza tabela de clientes"""
        try:
            # Buscar clientes do Supabase com timestamp mais recente
            last_sync_str = self.last_sync['clientes'].isoformat()
            
            response = supabase.client.table('clientes').select('*').gte('updated_at', last_sync_str).execute()
            
            if response.data:
                logger.info(f"🔄 Sincronizando {len(response.data)} clientes...")
                
                for cliente_data in response.data:
                    # Verificar se o cliente já existe no sistema
                    existing = Cliente.get_by_id(cliente_data['id'])
                    
                    if existing:
                        # Atualizar se foi modificado no Supabase
                        if existing.get('updated_at') != cliente_data.get('updated_at'):
                            Cliente.update(cliente_data['id'], **cliente_data)
                            logger.debug(f"✅ Cliente {cliente_data['nome']} atualizado via sincronização")
                    else:
                        # Criar novo cliente
                        Cliente.create(**cliente_data)
                        logger.debug(f"✅ Cliente {cliente_data['nome']} criado via sincronização")
                
                # Atualizar timestamp de última sincronização
                self.last_sync['clientes'] = datetime.now()
                
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar clientes: {e}")
    
    def sync_categorias(self):
        """Sincroniza tabela de categorias"""
        try:
            last_sync_str = self.last_sync['categorias'].isoformat()
            
            response = supabase.client.table('categorias').select('*').gte('updated_at', last_sync_str).execute()
            
            if response.data:
                logger.info(f"🔄 Sincronizando {len(response.data)} categorias...")
                
                for categoria_data in response.data:
                    existing = Categoria.get_by_id(categoria_data['id'])
                    
                    if existing:
                        if existing.get('updated_at') != categoria_data.get('updated_at'):
                            Categoria.update(categoria_data['id'], **categoria_data)
                            logger.debug(f"✅ Categoria {categoria_data['nome']} atualizada via sincronização")
                    else:
                        Categoria.create(**categoria_data)
                        logger.debug(f"✅ Categoria {categoria_data['nome']} criada via sincronização")
                
                self.last_sync['categorias'] = datetime.now()
                
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar categorias: {e}")
    
    def sync_produtos(self):
        """Sincroniza tabela de produtos"""
        try:
            last_sync_str = self.last_sync['produtos'].isoformat()
            
            response = supabase.client.table('produtos').select('*').gte('updated_at', last_sync_str).execute()
            
            if response.data:
                logger.info(f"🔄 Sincronizando {len(response.data)} produtos...")
                
                for produto_data in response.data:
                    existing = Produto.get_by_id(produto_data['id'])
                    
                    if existing:
                        if existing.get('updated_at') != produto_data.get('updated_at'):
                            Produto.update(produto_data['id'], **produto_data)
                            logger.debug(f"✅ Produto {produto_data['nome']} atualizado via sincronização")
                    else:
                        Produto.create(**produto_data)
                        logger.debug(f"✅ Produto {produto_data['nome']} criado via sincronização")
                
                self.last_sync['produtos'] = datetime.now()
                
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar produtos: {e}")
    
    def sync_estoque(self):
        """Sincroniza tabela de estoque"""
        try:
            last_sync_str = self.last_sync['estoque'].isoformat()
            
            response = supabase.client.table('estoque').select('*').gte('updated_at', last_sync_str).execute()
            
            if response.data:
                logger.info(f"🔄 Sincronizando {len(response.data)} itens de estoque...")
                
                for estoque_data in response.data:
                    existing = Estoque.get_by_id(estoque_data['id'])
                    
                    if existing:
                        if existing.get('updated_at') != estoque_data.get('updated_at'):
                            Estoque.update(estoque_data['id'], **estoque_data)
                            logger.debug(f"✅ Estoque do produto {estoque_data['produto_id']} atualizado via sincronização")
                    else:
                        Estoque.create(**estoque_data)
                        logger.debug(f"✅ Estoque do produto {estoque_data['produto_id']} criado via sincronização")
                
                self.last_sync['estoque'] = datetime.now()
                
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar estoque: {e}")
    
    def sync_vendas(self):
        """Sincroniza tabela de vendas"""
        try:
            last_sync_str = self.last_sync['vendas'].isoformat()
            
            response = supabase.client.table('vendas').select('*').gte('updated_at', last_sync_str).execute()
            
            if response.data:
                logger.info(f"🔄 Sincronizando {len(response.data)} vendas...")
                
                for venda_data in response.data:
                    existing = Venda.get_by_id(venda_data['id'])
                    
                    if existing:
                        if existing.get('updated_at') != venda_data.get('updated_at'):
                            Venda.update(venda_data['id'], **venda_data)
                            logger.debug(f"✅ Venda {venda_data['id']} atualizada via sincronização")
                    else:
                        Venda.create(**venda_data)
                        logger.debug(f"✅ Venda {venda_data['id']} criada via sincronização")
                
                self.last_sync['vendas'] = datetime.now()
                
        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar vendas: {e}")
    
    def force_sync(self):
        """Força uma sincronização imediata"""
        logger.info("🔄 Forçando sincronização imediata...")
        self.sync_all()
        logger.info("✅ Sincronização forçada concluída!")
    
    def get_sync_status(self):
        """Retorna o status da sincronização"""
        return {
            'running': self.running,
            'last_sync': self.last_sync,
            'sync_interval': self.sync_interval
        }

# Instância global do sincronizador
sync_manager = SupabaseSync()

def start_sync():
    """Inicia a sincronização"""
    sync_manager.start_sync()

def stop_sync():
    """Para a sincronização"""
    sync_manager.stop_sync()

def force_sync():
    """Força uma sincronização"""
    sync_manager.force_sync()

def get_sync_status():
    """Retorna o status da sincronização"""
    return sync_manager.get_sync_status()
