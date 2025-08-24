// Sistema Empresarial - JavaScript Principal
console.log('🚀 Sistema Empresarial carregando...');

// Configurações
const CONFIG = {
    API_BASE: window.location.origin,
    VERSION: '1.0.0',
    DEBUG: true
};

// Classe principal do sistema
class SistemaEmpresarial {
    constructor() {
        this.init();
    }

    init() {
        console.log('✅ Inicializando Sistema Empresarial...');
        this.setupEventListeners();
        this.checkSystemStatus();
        this.loadMainContent();
    }

    setupEventListeners() {
        // Event listeners para navegação
        document.addEventListener('DOMContentLoaded', () => {
            this.setupNavigation();
            this.setupForms();
        });

        // Interceptar cliques em links
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'A') {
                e.preventDefault();
                this.navigateTo(e.target.href);
            }
        });
    }

    setupNavigation() {
        const nav = document.querySelector('nav');
        if (nav) {
            nav.innerHTML = `
                <div class="navbar">
                    <div class="navbar-brand">
                        <h1>🏢 Sistema Empresarial</h1>
                    </div>
                    <div class="navbar-menu">
                        <a href="/" class="nav-link">🏠 Dashboard</a>
                        <a href="/clientes" class="nav-link">👥 Clientes</a>
                        <a href="/produtos" class="nav-link">📦 Produtos</a>
                        <a href="/categorias" class="nav-link">🏷️ Categorias</a>
                        <a href="/estoque" class="nav-link">📊 Estoque</a>
                        <a href="/vendas" class="nav-link">💰 Vendas</a>
                        <a href="/relatorios" class="nav-link">📈 Relatórios</a>
                        <a href="/logout" class="nav-link">🚪 Sair</a>
                    </div>
                </div>
            `;
        }
    }

    setupForms() {
        // Setup do formulário de login
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleLogin();
            });
        }
    }

    async handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (username === 'admin' && password === 'admin123') {
            console.log('✅ Login bem-sucedido!');
            this.showDashboard();
        } else {
            this.showError('Usuário ou senha incorretos!');
        }
    }

    showDashboard() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="dashboard">
                    <h1>🏠 Dashboard - Sistema Empresarial</h1>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <h3>👥 Clientes</h3>
                            <p class="stat-number">0</p>
                        </div>
                        <div class="stat-card">
                            <h3>📦 Produtos</h3>
                            <p class="stat-number">0</p>
                        </div>
                        <div class="stat-card">
                            <h3>🏷️ Categorias</h3>
                            <p class="stat-number">0</p>
                        </div>
                        <div class="stat-card">
                            <h3>💰 Vendas</h3>
                            <p class="stat-number">0</p>
                        </div>
                    </div>
                    <div class="quick-actions">
                        <button onclick="sistema.navigateTo('/clientes')" class="btn btn-primary">➕ Novo Cliente</button>
                        <button onclick="sistema.navigateTo('/produtos')" class="btn btn-success">➕ Novo Produto</button>
                        <button onclick="sistema.navigateTo('/vendas')" class="btn btn-warning">💰 Nova Venda</button>
                    </div>
                </div>
            `;
        }
    }

    async navigateTo(path) {
        console.log(`🔄 Navegando para: ${path}`);
        
        try {
            // Tentar carregar via Flask primeiro
            const response = await fetch(path);
            if (response.ok) {
                window.location.href = path;
                return;
            }
        } catch (error) {
            console.log('⚠️ Flask não respondeu, usando JavaScript...');
        }

        // Fallback para JavaScript
        this.loadPageContent(path);
    }

    loadPageContent(path) {
        const mainContent = document.getElementById('main-content');
        
        switch (path) {
            case '/':
                this.showDashboard();
                break;
            case '/clientes':
                this.showClientes();
                break;
            case '/produtos':
                this.showProdutos();
                break;
            case '/categorias':
                this.showCategorias();
                break;
            case '/estoque':
                this.showEstoque();
                break;
            case '/vendas':
                this.showVendas();
                break;
            case '/relatorios':
                this.showRelatorios();
                break;
            default:
                this.showError('Página não encontrada');
        }
    }

    showClientes() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="page">
                    <h1>👥 Gestão de Clientes</h1>
                    <div class="actions">
                        <button onclick="sistema.showForm('cliente')" class="btn btn-primary">➕ Novo Cliente</button>
                    </div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Nome</th>
                                    <th>Email</th>
                                    <th>Telefone</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody id="clientes-table">
                                <tr><td colspan="4">Nenhum cliente cadastrado</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
    }

    showProdutos() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="page">
                    <h1>📦 Gestão de Produtos</h1>
                    <div class="actions">
                        <button onclick="sistema.showForm('produto')" class="btn btn-primary">➕ Novo Produto</button>
                    </div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Nome</th>
                                    <th>Preço</th>
                                    <th>Categoria</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody id="produtos-table">
                                <tr><td colspan="4">Nenhum produto cadastrado</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
    }

    showCategorias() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="page">
                    <h1>🏷️ Gestão de Categorias</h1>
                    <div class="actions">
                        <button onclick="sistema.showForm('categoria')" class="btn btn-primary">➕ Nova Categoria</button>
                    </div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Nome</th>
                                    <th>Descrição</th>
                                    <th>Cor</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody id="categorias-table">
                                <tr><td colspan="4">Nenhuma categoria cadastrada</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
    }

    showEstoque() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="page">
                    <h1>📊 Controle de Estoque</h1>
                    <div class="actions">
                        <button onclick="sistema.showForm('estoque')" class="btn btn-primary">➕ Ajustar Estoque</button>
                    </div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Produto</th>
                                    <th>Quantidade</th>
                                    <th>Mínimo</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="estoque-table">
                                <tr><td colspan="4">Nenhum produto em estoque</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
    }

    showVendas() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="page">
                    <h1>💰 Gestão de Vendas</h1>
                    <div class="actions">
                        <button onclick="sistema.showForm('venda')" class="btn btn-primary">➕ Nova Venda</button>
                    </div>
                    <div class="table-container">
                        <table class="data-table">
                            <thead>
                                <tr>
                                    <th>Data</th>
                                    <th>Cliente</th>
                                    <th>Total</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="vendas-table">
                                <tr><td colspan="4">Nenhuma venda registrada</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        }
    }

    showRelatorios() {
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.innerHTML = `
                <div class="page">
                    <h1>📈 Relatórios</h1>
                    <div class="reports-grid">
                        <div class="report-card">
                            <h3>📊 Vendas por Período</h3>
                            <p>Relatório de vendas mensais e anuais</p>
                            <button class="btn btn-primary">Gerar Relatório</button>
                        </div>
                        <div class="report-card">
                            <h3>📦 Estoque Baixo</h3>
                            <p>Produtos com estoque abaixo do mínimo</p>
                            <button class="btn btn-warning">Ver Produtos</button>
                        </div>
                        <div class="report-card">
                            <h3>👥 Clientes Ativos</h3>
                            <p>Lista de clientes com mais compras</p>
                            <button class="btn btn-success">Ver Ranking</button>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    showForm(type) {
        const mainContent = document.getElementById('main-content');
        let formHTML = '';

        switch (type) {
            case 'cliente':
                formHTML = `
                    <div class="form-page">
                        <h1>👥 Novo Cliente</h1>
                        <form onsubmit="sistema.saveCliente(event)">
                            <div class="form-group">
                                <label>Nome:</label>
                                <input type="text" id="nome" required>
                            </div>
                            <div class="form-group">
                                <label>Email:</label>
                                <input type="email" id="email" required>
                            </div>
                            <div class="form-group">
                                <label>Telefone:</label>
                                <input type="tel" id="telefone" required>
                            </div>
                            <div class="form-group">
                                <label>CPF/CNPJ:</label>
                                <input type="text" id="cpf_cnpj" required>
                            </div>
                            <div class="form-group">
                                <label>Endereço:</label>
                                <input type="text" id="endereco" required>
                            </div>
                            <div class="form-group">
                                <label>Cidade:</label>
                                <input type="text" id="cidade" required>
                            </div>
                            <div class="form-group">
                                <label>Estado:</label>
                                <input type="text" id="estado" required>
                            </div>
                            <div class="form-group">
                                <label>CEP:</label>
                                <input type="text" id="cep" required>
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">Salvar</button>
                                <button type="button" onclick="sistema.navigateTo('/clientes')" class="btn btn-secondary">Cancelar</button>
                            </div>
                        </form>
                    </div>
                `;
                break;
            case 'produto':
                formHTML = `
                    <div class="form-page">
                        <h1>📦 Novo Produto</h1>
                        <form onsubmit="sistema.saveProduto(event)">
                            <div class="form-group">
                                <label>Nome:</label>
                                <input type="text" id="produto_nome" required>
                            </div>
                            <div class="form-group">
                                <label>Descrição:</label>
                                <textarea id="produto_descricao" required></textarea>
                            </div>
                            <div class="form-group">
                                <label>Preço:</label>
                                <input type="number" id="produto_preco" step="0.01" required>
                            </div>
                            <div class="form-group">
                                <label>Categoria:</label>
                                <select id="produto_categoria" required>
                                    <option value="">Selecione uma categoria</option>
                                    <option value="1">Eletrônicos</option>
                                    <option value="2">Roupas</option>
                                    <option value="3">Livros</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Código de Barras:</label>
                                <input type="text" id="produto_codigo">
                            </div>
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">Salvar</button>
                                <button type="button" onclick="sistema.navigateTo('/produtos')" class="btn btn-secondary">Cancelar</button>
                            </div>
                        </form>
                    </div>
                `;
                break;
        }

        if (mainContent) {
            mainContent.innerHTML = formHTML;
        }
    }

    async saveCliente(event) {
        event.preventDefault();
        
        const cliente = {
            nome: document.getElementById('nome').value,
            email: document.getElementById('email').value,
            telefone: document.getElementById('telefone').value,
            cpf_cnpj: document.getElementById('cpf_cnpj').value,
            endereco: document.getElementById('endereco').value,
            cidade: document.getElementById('cidade').value,
            estado: document.getElementById('estado').value,
            cep: document.getElementById('cep').value
        };

        console.log('💾 Salvando cliente:', cliente);
        this.showSuccess('Cliente salvo com sucesso!');
        
        // Simular salvamento
        setTimeout(() => {
            this.navigateTo('/clientes');
        }, 1000);
    }

    async saveProduto(event) {
        event.preventDefault();
        
        const produto = {
            nome: document.getElementById('produto_nome').value,
            descricao: document.getElementById('produto_descricao').value,
            preco: parseFloat(document.getElementById('produto_preco').value),
            categoria_id: document.getElementById('produto_categoria').value,
            codigo_barras: document.getElementById('produto_codigo').value
        };

        console.log('💾 Salvando produto:', produto);
        this.showSuccess('Produto salvo com sucesso!');
        
        // Simular salvamento
        setTimeout(() => {
            this.navigateTo('/produtos');
        }, 1000);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    checkSystemStatus() {
        console.log('🔍 Verificando status do sistema...');
        
        // Verificar se o Flask está funcionando
        fetch('/')
            .then(response => {
                if (response.ok) {
                    console.log('✅ Flask funcionando!');
                } else {
                    console.log('⚠️ Flask retornou erro, usando JavaScript...');
                    this.loadMainContent();
                }
            })
            .catch(error => {
                console.log('❌ Flask não respondeu, usando JavaScript...');
                this.loadMainContent();
            });
    }

    loadMainContent() {
        console.log('📱 Carregando interface JavaScript...');
        
        // Verificar se já existe conteúdo
        if (document.getElementById('main-content')) {
            return;
        }

        // Criar estrutura principal
        const body = document.body;
        body.innerHTML = `
            <div id="app">
                <nav></nav>
                <main id="main-content">
                    <div class="loading">
                        <h1>🚀 Sistema Empresarial</h1>
                        <p>Carregando...</p>
                    </div>
                </main>
            </div>
        `;

        // Mostrar página inicial
        this.showDashboard();
    }
}

// Inicializar o sistema quando a página carregar
let sistema;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        sistema = new SistemaEmpresarial();
    });
} else {
    sistema = new SistemaEmpresarial();
}

// Expor globalmente para uso em HTML
window.sistema = sistema;
