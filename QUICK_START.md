# 🚀 Início Rápido - Sistema Empresarial

## ⚡ Deploy em 5 minutos no Render

### 1. **Faça Upload para o GitHub**
- Crie um repositório chamado `sistema-empresarial`
- Faça upload de TODOS os arquivos desta pasta
- **NÃO** inclua a pasta `.venv` ou arquivos `.env`

### 2. **Configure o Render**
- Acesse [render.com](https://render.com)
- Faça login com GitHub
- Clique em "New +" → "Web Service"
- Selecione seu repositório

### 3. **Configure o Serviço**
- **Name**: `sistema-empresarial`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements_producao.txt`
- **Start Command**: `gunicorn app_producao:app`
- **Plan**: `Free`

### 4. **Configure as Variáveis de Ambiente**
Clique em "Environment" e adicione:

```
SUPABASE_URL=https://txylasunasazzcyvchfe.supabase.co
SUPABASE_KEY=sb_secret_-iHi5o-WP76kpTWev7bQYA_49UtmLdL
SUPABASE_SERVICE_KEY=COLE_SUA_CHAVE_SERVICE_ROLE_AQUI
SECRET_KEY=sua_chave_secreta_muito_segura_aqui_123456789
FLASK_ENV=production
```

### 5. **Deploy**
- Clique em "Create Web Service"
- Aguarde o build (2-5 minutos)
- Pronto! Seu sistema estará online

## 🔑 Acesso ao Sistema

- **URL**: `https://seu-servico.onrender.com`
- **Login**: `admin`
- **Senha**: `admin123`

## ⚠️ IMPORTANTE

1. **Altere a senha padrão** após o primeiro login
2. **Configure sua chave service role** do Supabase
3. **O sistema sincroniza automaticamente** com o Supabase

## 🆘 Problemas Comuns

**Build falha?**
- Verifique se todos os arquivos estão no GitHub
- Confirme as variáveis de ambiente

**Erro 500?**
- Verifique os logs no Render
- Confirme as credenciais do Supabase

**Não conecta ao Supabase?**
- Verifique `SUPABASE_URL` e `SUPABASE_KEY`
- Confirme se o projeto está ativo

---

**🎉 Seu sistema empresarial estará rodando na nuvem!**
