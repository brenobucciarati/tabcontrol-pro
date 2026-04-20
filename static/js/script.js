

// static/js/script.js - VERSÃO COMPLETA E CORRIGIDA (SEM IMAGENS NOS MODAIS)
let tablets = [];
let estatisticas = {
    total: 0,
    disponiveis: 0,
    em_uso: 0
};
let isLoading = false;
let currentMultiFotoManagerRetirada = null;
let currentMultiFotoManagerDevolucao = null;
let usuarioAtual = null;

// Elementos DOM
const tabletsGrid = document.getElementById('tablets-grid');
const totalTablets = document.getElementById('total-tablets');
const disponiveisTablets = document.getElementById('disponiveis-tablets');
const emUsoTablets = document.getElementById('em-uso-tablets');
const filtroStatus = document.getElementById('filtro-status');
const busca = document.getElementById('busca');

// Modal
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
let currentTabletId = null;

// Funções de utilidade
function showNotification(message, type = 'success') {
    const flash = document.createElement('div');
    flash.className = `flash ${type === 'error' ? 'erro' : ''}`;
    flash.innerHTML = `
        <span><i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i> ${message}</span>
    `;
    
    const flashWrap = document.querySelector('.flash-wrap') || document.createElement('div');
    if (!flashWrap.className) {
        flashWrap.className = 'flash-wrap';
        document.querySelector('.container').insertBefore(flashWrap, document.querySelector('.filtros'));
    }
    flashWrap.innerHTML = '';
    flashWrap.appendChild(flash);
    
    flash.style.animation = 'cardEntrance 0.3s ease';
    
    setTimeout(() => {
        flash.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => flash.remove(), 300);
    }, 3000);
}

function filtrarPorStatus(status) {
    filtroStatus.value = status;
    aplicarFiltros();
    
    const statusTexto = {
        'todos': 'Todos os tablets',
        'disponivel': 'Tablets disponíveis',
        'em_uso': 'Tablets em uso'
    };
    
    showNotification(`<i class="fas fa-filter"></i> Mostrando: ${statusTexto[status]}`, 'success');
}

function formatTime(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

function setLoading(loading) {
    const refreshBtn = document.querySelector('a[href="#"][onclick="fetchTablets()"]');
    if (refreshBtn) {
        if (loading) {
            refreshBtn.classList.add('loading', 'btn-refresh');
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Atualizando...';
        } else {
            refreshBtn.classList.remove('loading');
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar';
        }
    }
    
    if (loading) {
        tabletsGrid.classList.add('loading');
    } else {
        tabletsGrid.classList.remove('loading');
    }
}

async function fetchUsuarioAtual() {
    try {
        const response = await fetch('/api/usuario/atual');
        if (response.ok) {
            usuarioAtual = await response.json();
            console.log('👤 Usuário logado:', usuarioAtual.nome);
        }
    } catch (error) {
        console.error('Erro ao buscar usuário:', error);
    }
}

async function verificarAdmin() {
    try {
        const response = await fetch('/api/usuario/atual');
        if (response.ok) {
            const usuario = await response.json();
            const adminLink = document.getElementById('admin-link');
            if (adminLink && usuario.cargo === 'admin') {
                adminLink.style.display = 'inline-flex';
            }
        }
    } catch (error) {
        console.log('Erro ao verificar admin:', error);
    }
}

async function fetchTablets() {
    if (isLoading) return;
    
    isLoading = true;
    setLoading(true);
    
    try {
        const response = await fetch('/api/tablets');
        
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        if (!response.ok) {
            throw new Error('Erro ao carregar tablets');
        }
        
        tablets = await response.json();
        console.log('📱 Tablets carregados:', tablets.length);
        
        setTimeout(() => {
            aplicarFiltros();
            fetchEstatisticas();
            isLoading = false;
            setLoading(false);
            showNotification(`${tablets.length} tablets carregados`);
        }, 300);
        
    } catch (error) {
        console.error('Erro ao buscar tablets:', error);
        showNotification('Erro ao carregar tablets', 'error');
        isLoading = false;
        setLoading(false);
    }
}

async function fetchEstatisticas() {
    try {
        const response = await fetch('/api/estatisticas');
        estatisticas = await response.json();
        atualizarEstatisticas();
    } catch (error) {
        console.error('Erro ao buscar estatísticas:', error);
    }
}

async function fetchTabletHistorico(tabletId) {
    try {
        const response = await fetch(`/api/tablets/${tabletId}/historico`);
        return await response.json();
    } catch (error) {
        console.error('Erro ao buscar histórico:', error);
        return [];
    }
}

async function retirarTabletComChecklistMultiFotos(tabletId, usuario, liberadoPor, checklist, fotos) {
    try {
        const body = { 
            usuario, 
            liberado_por: liberadoPor,
            checklist_estado: checklist.estado,
            checklist_rede: checklist.rede,
            checklist_carga: checklist.carga,
            fotos: fotos
        };
        
        if (fotos.length > 0) {
            body.foto_retirada = fotos[0].caminho;
        }
        
        const response = await fetch(`/api/tablets/${tabletId}/retirar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (response.ok) {
            showNotification(`<i class="fas fa-user-check"></i> Tablet retirado por ${usuario} com ${fotos.length} foto(s)`);
            fetchTablets();
            closeModal();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Erro ao retirar tablet', 'error');
        }
    } catch (error) {
        console.error('Erro ao retirar tablet:', error);
        showNotification('Erro ao retirar tablet', 'error');
    }
}

async function devolverTabletComChecklistMultiFotos(tabletId, checklistEstado, fotos) {
    try {
        const body = { 
            checklist_devolucao_estado: checklistEstado,
            fotos: fotos
        };
        
        if (fotos.length > 0) {
            body.foto_devolucao = fotos[0].caminho;
        }
        
        const response = await fetch(`/api/tablets/${tabletId}/devolver`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (response.ok) {
            showNotification(`<i class="fas fa-undo-alt"></i> Tablet devolvido com sucesso com ${fotos.length} foto(s)`);
            fetchTablets();
            closeModal();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Erro ao devolver tablet', 'error');
        }
    } catch (error) {
        console.error('Erro ao devolver tablet:', error);
        showNotification('Erro ao devolver tablet', 'error');
    }
}

function criarCardTablet(tablet, index) {
    const card = document.createElement('div');
    card.className = `card ${tablet.status === 'disponivel' ? 'livre' : 'ocupada'}`;
    card.dataset.id = tablet.id;
    card.dataset.status = tablet.status;
    card.dataset.numero = tablet.numero;
    card.dataset.modelo = tablet.modelo;
    
    card.style.setProperty('--card-index', index);
    
    const led = document.createElement('div');
    led.className = `led-pulse ${tablet.status === 'disponivel' ? 'livre' : 'ocupada'}`;
    card.appendChild(led);
    
    const imageDiv = document.createElement('div');
    imageDiv.className = 'tablet-image';
    
    const img = document.createElement('img');
    img.src = tablet.imagem ? `/static/uploads/${tablet.imagem}` : '/static/uploads/default.png';
    img.alt = `Tablet ${tablet.numero}`;
    img.onerror = () => {
        imageDiv.classList.add('no-image');
        imageDiv.innerHTML = '<i class="fas fa-tablet-alt"></i>';
        img.style.display = 'none';
    };
    
    if (tablet.imagem) {
        imageDiv.appendChild(img);
    } else {
        imageDiv.classList.add('no-image');
        imageDiv.innerHTML = '<i class="fas fa-tablet-alt"></i>';
    }
    card.appendChild(imageDiv);
    
    const cardHead = document.createElement('div');
    cardHead.className = 'card-head';
    cardHead.innerHTML = `
        <div>
            <div class="card-title"><i class="fas fa-hashtag"></i> Tablet ${tablet.numero}</div>
            <div class="tipo"><i class="fas fa-microchip"></i> ${tablet.modelo}</div>
        </div>
        <span class="badge ${tablet.status === 'disponivel' ? 'green' : 'red'}">
            <i class="fas ${tablet.status === 'disponivel' ? 'fa-check' : 'fa-hourglass-half'}"></i>
            ${tablet.status === 'disponivel' ? 'LIVRE' : 'EM USO'}
        </span>
    `;
    card.appendChild(cardHead);
    
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    if (tablet.status === 'em_uso') {
        cardBody.innerHTML = `
            <div class="linha">
                <span><i class="fas fa-user"></i> Usuário</span>
                <span class="valor">${tablet.usuario_atual || '—'}</span>
            </div>
            <div class="linha">
                <span><i class="fas fa-clock"></i> Desde</span>
                <span class="valor">${tablet.hora_retirada || '—'}</span>
            </div>
        `;
    } else if (tablet.ultimo_usuario) {
        cardBody.innerHTML = `
            <div class="linha">
                <span><i class="fas fa-history"></i> Último uso</span>
                <span class="valor">${tablet.ultimo_usuario}</span>
            </div>
        `;
    } else {
        cardBody.innerHTML = `
            <div class="linha">
                <span><i class="fas fa-history"></i> Último uso</span>
                <span class="valor">—</span>
            </div>
        `;
    }
    card.appendChild(cardBody);
    
    const actions = document.createElement('div');
    actions.className = 'actions';
    
    if (tablet.status === 'disponivel') {
        actions.innerHTML = `
            <button class="btn btn-start" onclick="event.stopPropagation(); abrirModalRetirada(${tablet.id})">
                <i class="fas fa-hand-paper"></i> Pegar
            </button>
        `;
    } else {
        actions.innerHTML = `
            <button class="btn btn-stop" onclick="event.stopPropagation(); abrirModalDevolucao(${tablet.id})">
                <i class="fas fa-undo-alt"></i> Devolver
            </button>
        `;
    }
    
    actions.innerHTML += `
        <button class="btn btn-roxo ghost" onclick="event.stopPropagation(); abrirModalDetalhes(${tablet.id})">
            <i class="fas fa-info-circle"></i> Detalhes
        </button>
    `;
    
    card.appendChild(actions);
    card.addEventListener('click', () => abrirModalDetalhes(tablet.id));
    
    return card;
}

function aplicarFiltros() {
    const statusFiltro = filtroStatus.value;
    const buscaTexto = busca.value.toLowerCase();
    
    let tabletsFiltrados = tablets.filter(tablet => {
        if (statusFiltro !== 'todos' && tablet.status !== statusFiltro) return false;
        if (buscaTexto) {
            return tablet.numero.includes(buscaTexto) || 
                   tablet.modelo.toLowerCase().includes(buscaTexto);
        }
        return true;
    });
    
    tabletsGrid.innerHTML = '';
    tabletsFiltrados.sort((a, b) => a.numero.localeCompare(b.numero));
    
    tabletsFiltrados.forEach((tablet, index) => {
        const card = criarCardTablet(tablet, index);
        tabletsGrid.appendChild(card);
    });
}

function atualizarEstatisticas() {
    animateNumber(totalTablets, estatisticas.total);
    animateNumber(disponiveisTablets, estatisticas.disponiveis);
    animateNumber(emUsoTablets, estatisticas.em_uso);
}

function animateNumber(element, newValue) {
    const oldValue = parseInt(element.textContent) || 0;
    if (oldValue === newValue) return;
    
    element.style.transform = 'scale(1.2)';
    element.style.transition = 'transform 0.3s ease';
    
    setTimeout(() => {
        element.textContent = newValue;
        element.style.transform = 'scale(1)';
    }, 150);
}

async function abrirModalDetalhes(tabletId) {
    currentTabletId = tabletId;
    const tablet = tablets.find(t => t.id === tabletId);
    const historico = await fetchTabletHistorico(tabletId);
    
    modalTitle.innerHTML = `<i class="fas fa-info-circle"></i> Tablet ${tablet.numero}`;
    
    let html = `
    <div class="info-grid">
        <div class="info-item">
            <span class="label"><i class="fas fa-hashtag"></i> Número</span>
            <span class="value">Tablet ${tablet.numero}</span>
        </div>
        <div class="info-item">
            <span class="label"><i class="fas fa-microchip"></i> Modelo</span>
            <span class="value">${tablet.modelo}</span>
        </div>
        <div class="info-item">
            <span class="label"><i class="fas fa-circle"></i> Status</span>
            <span class="value" style="color: ${tablet.status === 'disponivel' ? 'var(--neon-verde)' : 'var(--neon-vermelho)'}">
                <i class="fas ${tablet.status === 'disponivel' ? 'fa-check-circle' : 'fa-hourglass-half'}"></i>
                ${tablet.status === 'disponivel' ? 'Disponível' : 'Em Uso'}
            </span>
        </div>
    `;
    
    if (tablet.status === 'em_uso') {
        html += `
            <div class="info-item">
                <span class="label"><i class="fas fa-user"></i> Usuário</span>
                <span class="value">${tablet.usuario_atual || '—'}</span>
            </div>
            <div class="info-item">
                <span class="label"><i class="fas fa-clock"></i> Desde</span>
                <span class="value">${tablet.hora_retirada || '—'}</span>
            </div>
        `;
    }
    
    html += `</div>`;
    
    if (historico.length > 0) {
        html += `<h3 style="margin: 20px 0 10px;"><i class="fas fa-history"></i> Últimas movimentações</h3>`;
        historico.forEach(h => {
            const estadoIcon = h.checklist_retirada?.estado === 'sim' ? 'fa-check-circle' : 'fa-times-circle';
            const redeIcon = h.checklist_retirada?.rede === 'sim' ? 'fa-wifi' : 'fa-wifi-slash';
            const cargaIcon = h.checklist_retirada?.carga === 'sim' ? 'fa-battery-full' : 'fa-battery-quarter';
            const estadoColor = h.checklist_retirada?.estado === 'sim' ? 'var(--neon-verde)' : 'var(--neon-vermelho)';
            
            const temFotos = h.fotos && h.fotos.length > 0;
            const fotoPrincipal = h.foto_retirada || h.foto_devolucao;
            
            html += `
                <div class="linha" style="background: rgba(0,0,0,0.2); border-radius: 12px; padding: 10px; margin-bottom: 8px;">
                    <div style="flex: 1;">
                        <strong><i class="fas fa-user"></i> ${h.usuario}</strong><br>
                        <small style="color: var(--muted);"><i class="fas fa-key"></i> Liberado por: ${h.liberado_por}</small>
                        <div style="margin-top: 5px; font-size: 11px;">
                            <span style="color: ${estadoColor}"><i class="fas ${estadoIcon}"></i> Estado: ${h.checklist_retirada?.estado === 'sim' ? 'OK' : 'Com avaria'}</span><br>
                            <span><i class="fas ${redeIcon}"></i> Rede: ${h.checklist_retirada?.rede === 'sim' ? 'Conectado' : 'Desconectado'}</span><br>
                            <span><i class="fas ${cargaIcon}"></i> Carga: ${h.checklist_retirada?.carga === 'sim' ? 'Carregado' : 'Descarregado'}</span>
                        </div>
                        
                        ${(temFotos || fotoPrincipal) ? `
                            <div style="margin-top: 10px;">
                                <strong style="font-size: 11px; color: var(--muted);">
                                    <i class="fas fa-images"></i> Fotos (${temFotos ? h.fotos.length : 1})
                                </strong>
                                <div style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 5px;">
                                    ${temFotos ? 
                                        h.fotos.map(foto => `
                                            <div class="foto-item" onclick="event.stopPropagation(); abrirCarrosselHistorico(${JSON.stringify(h.fotos).replace(/"/g, '&quot;')}, ${h.fotos.indexOf(foto)})" title="${foto.categoria || 'Foto'}">
                                              <img src="${foto.caminho && foto.caminho.startsWith('http') ? foto.caminho : '/static/uploads/' + foto.caminho}" alt="Foto" class="foto-thumbnail">
                                                <span class="foto-label">${foto.categoria || 'Geral'}</span>
                                            </div>
                                        `).join('') 
                                        : 
                                        (fotoPrincipal ? `
                                            <div class="foto-item" onclick="openFotoModal('/static/uploads/${fotoPrincipal}')" title="Foto">
                                                <img src="/static/uploads/${fotoPrincipal}" alt="Foto" class="foto-thumbnail">
                                                <span class="foto-label">Principal</span>
                                            </div>
                                        ` : '')
                                    }
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div style="text-align: right;">
                        <span class="badge ${h.data_devolucao ? 'green' : 'red'}" style="display: inline-block;">
                            <i class="fas ${h.data_devolucao ? 'fa-check' : 'fa-hourglass-half'}"></i>
                            ${h.data_devolucao ? 'Devolvido' : 'Em uso'}
                        </span><br>
                        <small><i class="far fa-calendar-alt"></i> ${h.data_retirada}</small>
                        ${h.checklist_devolucao?.estado ? `<br><small><i class="fas ${h.checklist_devolucao.estado === 'sim' ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i> Devolução: ${h.checklist_devolucao.estado === 'sim' ? 'OK' : 'Com avaria'}</small>` : ''}
                    </div>
                </div>
            `;
        });
    }
    
    modalBody.innerHTML = html;
    modal.style.display = 'block';
    modal.style.animation = 'slideUp 0.3s ease';
}

function abrirModalRetirada(tabletId) {
    currentTabletId = tabletId;
    const tablet = tablets.find(t => t.id === tabletId);
    const nomeLiberadoPor = usuarioAtual ? usuarioAtual.nome : '';
    
    modalTitle.innerHTML = `<i class="fas fa-hand-paper"></i> Retirar Tablet ${tablet.numero}`;
    modalBody.innerHTML = `
        <div class="form-col">
            <div class="info-item" style="margin-bottom: 15px;">
                <span class="label"><i class="fas fa-hashtag"></i> Tablet</span>
                <span class="value">${tablet.numero} - ${tablet.modelo}</span>
            </div>
            
            <div>
                <label><i class="fas fa-user"></i> Colaborador <span style="color: var(--neon-vermelho);">*</span></label>
                <input type="text" id="modal-usuario" placeholder="Nome do colaborador..." style="width: 100%;">
            </div>
            <div>
                <label><i class="fas fa-key"></i> Liberado por <span style="color: var(--neon-vermelho);">*</span></label>
                <input type="text" id="modal-liberado" style="width: 100%; background: rgba(0,217,255,0.1); color: var(--neon-azul); font-weight: 500;" readonly value="${nomeLiberadoPor}">
            </div>
            
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                <h4 style="margin-bottom: 12px;"><i class="fas fa-clipboard-list"></i> Checklist de Retirada</h4>
                
                <div class="checklist-item" style="margin-bottom: 12px;">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <i class="fas fa-check-circle" style="color: var(--neon-verde);"></i>
                        <span>O tablet está em perfeito estado (sem avarias)?</span>
                        <select id="checklist-estado" style="margin-left: auto; width: 80px; padding: 4px; border-radius: 8px; background: #0f0f1f; color: var(--text); border: 1px solid rgba(255,255,255,0.2);">
                            <option value="sim">✅ Sim</option>
                            <option value="nao">❌ Não</option>
                        </select>
                    </label>
                </div>
                
                <div class="checklist-item" style="margin-bottom: 12px;">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <i class="fas fa-wifi"></i>
                        <span>O tablet está conectado na rede?</span>
                        <select id="checklist-rede" style="margin-left: auto; width: 80px; padding: 4px; border-radius: 8px; background: #0f0f1f; color: var(--text); border: 1px solid rgba(255,255,255,0.2);">
                            <option value="sim">✅ Sim</option>
                            <option value="nao">❌ Não</option>
                        </select>
                    </label>
                </div>
                
                <div class="checklist-item" style="margin-bottom: 12px;">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <i class="fas fa-battery-full"></i>
                        <span>O tablet está carregado?</span>
                        <select id="checklist-carga" style="margin-left: auto; width: 80px; padding: 4px; border-radius: 8px; background: #0f0f1f; color: var(--text); border: 1px solid rgba(255,255,255,0.2);">
                            <option value="sim">✅ Sim</option>
                            <option value="nao">❌ Não</option>
                        </select>
                    </label>
                </div>
            </div>
            
            <div style="margin-top: 10px; padding: 10px; background: rgba(255,59,88,0.1); border-radius: 8px; border: 1px dashed var(--neon-vermelho);">
                <p style="margin: 0 0 10px 0; color: var(--neon-vermelho); font-size: 13px;">
                    <i class="fas fa-exclamation-triangle"></i> 
                    <strong>FOTOS OBRIGATÓRIAS:</strong> Tire pelo menos uma foto do tablet!
                </p>
                <div id="fotos-retirada-container"></div>
            </div>
            
            <div id="aviso-avaria-retirada" class="avaria-aviso" style="display: none;">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>ATENÇÃO:</strong> Como o tablet não está em perfeito estado, 
                é <u>obrigatório</u> tirar pelo menos uma foto da AVARIA!
            </div>
            
            <button class="btn btn-start" onclick="confirmarRetiradaMultiFotos()" style="width: 100%; margin-top: 10px;">
                <i class="fas fa-check-circle"></i> Confirmar Retirada
            </button>
        </div>
    `;
    
    modal.style.display = 'block';
    modal.style.animation = 'slideUp 0.3s ease';
    
    setTimeout(() => {
        if (typeof MultiFotoUploadManager !== 'undefined') {
            currentMultiFotoManagerRetirada = new MultiFotoUploadManager({
                tipo: 'retirada',
                maxFotos: 10
            });
            currentMultiFotoManagerRetirada.setTabletId(tabletId);  // ✅ ADICIONADO
            
            const container = document.getElementById('fotos-retirada-container');
            if (container) {
                currentMultiFotoManagerRetirada.render(container);
                window.currentMultiFotoManager = currentMultiFotoManagerRetirada;
            }
        }
        
        const selectEstado = document.getElementById('checklist-estado');
        const avisoAvaria = document.getElementById('aviso-avaria-retirada');
        if (selectEstado && avisoAvaria) {
            selectEstado.addEventListener('change', (e) => {
                avisoAvaria.style.display = e.target.value === 'nao' ? 'block' : 'none';
            });
        }
    }, 100);
}

function confirmarRetiradaMultiFotos() {
    const usuario = document.getElementById('modal-usuario')?.value;
    const liberadoPor = usuarioAtual ? usuarioAtual.nome : document.getElementById('modal-liberado')?.value;
    const checklistEstado = document.getElementById('checklist-estado')?.value;
    const checklistRede = document.getElementById('checklist-rede')?.value;
    const checklistCarga = document.getElementById('checklist-carga')?.value;
    
    if (!usuario) {
        showNotification('Preencha o nome do colaborador!', 'error');
        return;
    }
    
    if (currentMultiFotoManagerRetirada && currentMultiFotoManagerRetirada.temUploadPendente()) {
        showNotification('⚠️ Aguarde o envio das fotos antes de confirmar!', 'error');
        return;
    }
    
    if (!currentMultiFotoManagerRetirada || !currentMultiFotoManagerRetirada.temFotos()) {
        showNotification('⚠️ É OBRIGATÓRIO tirar pelo menos uma foto do tablet!', 'error');
        return;
    }
    
    const fotosEnviadas = currentMultiFotoManagerRetirada.getFotosEnviadas();
    if (fotosEnviadas.length === 0) {
        showNotification('⚠️ Nenhuma foto foi enviada completamente!', 'error');
        return;
    }
    
    if (checklistEstado === 'nao' && !currentMultiFotoManagerRetirada.temFotoCategoria('avaria')) {
        showNotification('⚠️ Como o tablet NÃO está em perfeito estado, é obrigatório tirar uma foto da AVARIA!', 'error');
        return;
    }
    
    const fotos = fotosEnviadas.map(f => ({
        caminho: f.caminho,
        categoria: f.categoria
    }));
    
    retirarTabletComChecklistMultiFotos(currentTabletId, usuario, liberadoPor, {
        estado: checklistEstado,
        rede: checklistRede,
        carga: checklistCarga
    }, fotos);
}

function abrirModalDevolucao(tabletId) {
    currentTabletId = tabletId;
    const tablet = tablets.find(t => t.id === tabletId);
    
    modalTitle.innerHTML = `<i class="fas fa-undo-alt"></i> Devolver Tablet ${tablet.numero}`;
    modalBody.innerHTML = `
        <div class="form-col">
            <div class="info-item" style="margin-bottom: 15px;">
                <span class="label"><i class="fas fa-hashtag"></i> Tablet</span>
                <span class="value">${tablet.numero} - ${tablet.modelo}</span>
            </div>
            <div class="info-item" style="margin-bottom: 15px;">
                <span class="label"><i class="fas fa-user"></i> Usuário atual</span>
                <span class="value">${tablet.usuario_atual || '—'}</span>
            </div>
            <div class="info-item" style="margin-bottom: 15px;">
                <span class="label"><i class="fas fa-clock"></i> Retirado em</span>
                <span class="value">${tablet.data_retirada || '—'}</span>
            </div>
            
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                <h4 style="margin-bottom: 12px;"><i class="fas fa-clipboard-list"></i> Checklist de Devolução</h4>
                
                <div class="checklist-item" style="margin-bottom: 12px;">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer;">
                        <i class="fas fa-check-circle" style="color: var(--neon-verde);"></i>
                        <span>O tablet voltou em perfeito estado (sem avarias)?</span>
                        <select id="checklist-devolucao-estado" style="margin-left: auto; width: 80px; padding: 4px; border-radius: 8px; background: #0f0f1f; color: var(--text); border: 1px solid rgba(255,255,255,0.2);">
                            <option value="sim">✅ Sim</option>
                            <option value="nao">❌ Não</option>
                        </select>
                    </label>
                </div>
            </div>
            
            <div style="margin-top: 10px; padding: 10px; background: rgba(255,59,88,0.1); border-radius: 8px; border: 1px dashed var(--neon-vermelho);">
                <p style="margin: 0 0 10px 0; color: var(--neon-vermelho); font-size: 13px;">
                    <i class="fas fa-exclamation-triangle"></i> 
                    <strong>FOTOS OBRIGATÓRIAS:</strong> Tire pelo menos uma foto do tablet!
                </p>
                <div id="fotos-devolucao-container"></div>
            </div>
            
            <button class="btn btn-stop" onclick="confirmarDevolucaoMultiFotos()" style="width: 100%; margin-top: 10px;">
                <i class="fas fa-check-circle"></i> Confirmar Devolução
            </button>
        </div>
    `;
    
    modal.style.display = 'block';
    modal.style.animation = 'slideUp 0.3s ease';
    
    setTimeout(() => {
        if (typeof MultiFotoUploadManager !== 'undefined') {
            currentMultiFotoManagerDevolucao = new MultiFotoUploadManager({
                tipo: 'devolucao',
                maxFotos: 10
            });
            currentMultiFotoManagerDevolucao.setTabletId(tabletId);  // ✅ ADICIONADO
            
            const container = document.getElementById('fotos-devolucao-container');
            if (container) {
                currentMultiFotoManagerDevolucao.render(container);
                window.currentMultiFotoManager = currentMultiFotoManagerDevolucao;
            }
        }
    }, 100);
}

function confirmarDevolucaoMultiFotos() {
    const checklistEstado = document.getElementById('checklist-devolucao-estado')?.value;
    
    if (!checklistEstado) {
        showNotification('Selecione o estado do tablet!', 'error');
        return;
    }
    
    if (currentMultiFotoManagerDevolucao && currentMultiFotoManagerDevolucao.temUploadPendente()) {
        showNotification('⚠️ Aguarde o envio das fotos antes de confirmar!', 'error');
        return;
    }
    
    if (!currentMultiFotoManagerDevolucao || !currentMultiFotoManagerDevolucao.temFotos()) {
        showNotification('⚠️ É OBRIGATÓRIO tirar pelo menos uma foto do tablet!', 'error');
        return;
    }
    
    const fotosEnviadas = currentMultiFotoManagerDevolucao.getFotosEnviadas();
    if (fotosEnviadas.length === 0) {
        showNotification('⚠️ Nenhuma foto foi enviada completamente!', 'error');
        return;
    }
    
    const fotos = fotosEnviadas.map(f => ({
        caminho: f.caminho,
        categoria: f.categoria
    }));
    
    devolverTabletComChecklistMultiFotos(currentTabletId, checklistEstado, fotos);
}

function closeModal() {
    modal.style.animation = 'fadeOut 0.2s ease';
    setTimeout(() => {
        modal.style.display = 'none';
        modalBody.innerHTML = '';
        modal.style.animation = '';
        currentMultiFotoManagerRetirada = null;
        currentMultiFotoManagerDevolucao = null;
    }, 200);
}

// Event listeners
filtroStatus.addEventListener('change', aplicarFiltros);
busca.addEventListener('input', aplicarFiltros);

// Atualização automática
setInterval(() => {
    if (!isLoading) {
        fetchTablets();
    }
}, 120000);

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    fetchUsuarioAtual();
    fetchTablets();
    verificarAdmin();
    
    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length >= 3) {
        statCards[0].addEventListener('click', () => filtrarPorStatus('todos'));
        statCards[1].addEventListener('click', () => filtrarPorStatus('disponivel'));
        statCards[2].addEventListener('click', () => filtrarPorStatus('em_uso'));
        
        statCards.forEach(card => {
            card.style.cursor = 'pointer';
            card.setAttribute('title', 'Clique para filtrar');
        });
    }
    
    window.onclick = (event) => {
        if (event.target === modal) closeModal();
        
        const fotoModal = document.getElementById('foto-modal');
        if (fotoModal && event.target === fotoModal) {
            closeFotoModal();
        }
    };
});

// Funções globais
window.abrirModalDetalhes = abrirModalDetalhes;
window.abrirModalRetirada = abrirModalRetirada;
window.abrirModalDevolucao = abrirModalDevolucao;
window.confirmarRetiradaMultiFotos = confirmarRetiradaMultiFotos;
window.confirmarDevolucaoMultiFotos = confirmarDevolucaoMultiFotos;
window.closeModal = closeModal;
window.fetchTablets = fetchTablets;
window.filtrarPorStatus = filtrarPorStatus;
document.addEventListener('DOMContentLoaded', () => {
    const fotoModal = document.getElementById('foto-modal');
    if (fotoModal) {
        window.onclick = (event) => {
            if (event.target === fotoModal) {
                closeFotoModal();
            }
        };
    }
});
