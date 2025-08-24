# 🏢 Sistema Empresarial - Controle de Loja

## 📋 Descrição

Sistema completo de gestão empresarial desenvolvido em Flask com integração ao Supabase. Permite controle total de clientes, produtos, categorias, estoque e vendas com sincronização automática em tempo real.

## ✨ Funcionalidades

- 🔐 **Sistema de Login Seguro** - Autenticação de usuários
- 👥 **Gestão de Clientes** - CRUD completo de clientes
- 📦 **Controle de Produtos** - Cadastro e gestão de produtos
- 🏷️ **Categorias** - Organização por categorias
- 📊 **Controle de Estoque** - Acompanhamento de quantidade
- 💰 **Gestão de Vendas** - Registro e controle de vendas
- 📈 **Relatórios** - Relatórios de vendas e estoque
- 🔄 **Sincronização Automática** - Integração bidirecional com Supabase
- 📱 **Interface Responsiva** - Funciona em qualquer dispositivo
- 🌐 **PWA** - Instalável como aplicativo

## 🚀 Deploy Rápido no Render

### 1. Clone este repositório
```bash
git clone https://github.com/SEU_USUARIO/sistema-empresarial.git
cd sistema-empresarial
```

### 2. Configure as variáveis de ambiente no Render
```
SUPABASE_URL=https://txylasunasazzcyvchfe.supabase.co
SUPABASE_KEY=sua_chave_anon_public_aqui
SUPABASE_SERVICE_KEY=sua_chave_service_role_aqui
SECRET_KEY=sua_chave_secreta_muito_segura_aqui_123456789
FLASK_ENV=production
```

### 3. Deploy no Render
- Crie conta em [render.com](https://render.com)
- Conecte ao GitHub
- Selecione este repositório
- Use as configurações do `render.yaml`
- Deploy automático!

## 📱 Como Usar

1. **Acesse o sistema** via URL do Render
2. **Login**: admin / admin123
3. **Configure suas categorias** primeiro
4. **Adicione produtos** e clientes
5. **Gerencie vendas** e estoque

## 🔒 Segurança

- ✅ Autenticação obrigatória
- ✅ Sessões seguras
- ✅ Validação de dados
- ✅ Proteção contra SQL Injection

## 📊 Estrutura do Projeto

```
sistema-empresarial/
├── app_producao.py          # Aplicação principal
├── config_producao.py       # Configurações
├── models_supabase.py       # Modelos do banco
├── sync_supabase.py         # Sistema de sincronização
├── templates/               # Templates HTML
├── static/                  # Arquivos estáticos
├── requirements_producao.txt # Dependências
├── render.yaml              # Configuração Render
└── README.md               # Este arquivo
```

## 🎯 Tecnologias

- **Backend**: Flask (Python)
- **Banco de Dados**: Supabase (PostgreSQL)
- **Autenticação**: Flask-Login
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Hospedagem**: Render (Gratuito)

---

**Desenvolvido com ❤️ para facilitar a gestão empresarial**

> **⚠️ IMPORTANTE**: Altere a senha padrão em produção!
