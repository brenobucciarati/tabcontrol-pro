// static/js/foto-upload.js
// Sistema de Upload de Fotos - Integrado ao TabControl Pro
// Versão com suporte a múltiplas fotos, categorias e organização por tablet/data

class FotoUploadManager {
    constructor(options = {}) {
        this.tipo = options.tipo || 'retirada'; // 'retirada' ou 'devolucao'
        this.onUploadComplete = options.onUploadComplete || (() => {});
        this.containerId = options.containerId || `foto-${this.tipo}-container`;
        this.fotoPath = null;
        this.modoMultiplo = options.modoMultiplo || false;
        this.maxFotos = options.maxFotos || 10;
        this.fotos = [];
        this.onFotosChange = options.onFotosChange || (() => {});
        this.tabletId = options.tabletId || null; // NOVO: ID do tablet
    }

    // NOVO: Método para definir o ID do tablet
    setTabletId(tabletId) {
        this.tabletId = tabletId;
    }

    render(container) {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (this.modoMultiplo) {
            this.renderMultiplo(container, isMobile);
        } else {
            this.renderUnico(container, isMobile);
        }
    }

    renderUnico(container, isMobile) {
        const html = `
            <div class="foto-upload-container">
                <h4>
                    <i class="fas fa-camera"></i> 
                    Foto na ${this.tipo === 'retirada' ? 'Retirada' : 'Devolução'}
                </h4>
                
                ${isMobile ? this.renderMobileUpload() : this.renderDesktopUpload()}
                
                <div id="foto-preview-${this.tipo}" class="foto-preview" style="display: none;">
                    <img id="foto-img-${this.tipo}" src="" alt="Preview" onclick="openFotoCarrossel([{caminho: this.src.split('/static/uploads/')[1], categoria: 'Geral'}], 0)">
                </div>
                
                <div class="foto-actions">
                    <button type="button" class="btn-camera" id="btn-foto-${this.tipo}">
                        <i class="fas fa-${isMobile ? 'camera' : 'cloud-upload-alt'}"></i>
                        ${isMobile ? 'Tirar Foto' : 'Selecionar Arquivo'}
                    </button>
                    <button type="button" class="btn-limpar-foto" id="btn-limpar-foto-${this.tipo}" style="display: none;">
                        <i class="fas fa-trash-alt"></i> Limpar
                    </button>
                </div>
                
                <div class="foto-info" id="foto-info-${this.tipo}">
                    <i class="fas fa-info-circle"></i>
                    <span>${isMobile ? 'Toque para abrir a câmera' : 'Arraste ou clique para selecionar'}</span>
                </div>
                
                <input type="hidden" id="foto-path-${this.tipo}" name="foto_${this.tipo}">
            </div>
        `;
        
        container.innerHTML = html;
        this.bindEventsUnico(isMobile);
    }

    renderMultiplo(container, isMobile) {
        const html = `
            <div class="multi-foto-container">
                <div class="fotos-header">
                    <h4>
                        <i class="fas fa-images"></i> 
                        Fotos da ${this.tipo === 'retirada' ? 'Retirada' : 'Devolução'}
                        <span class="foto-count" id="foto-count-${this.tipo}">0/${this.maxFotos}</span>
                    </h4>
                </div>
                
                <div id="fotos-grid-${this.tipo}" class="fotos-grid">
                    <div class="upload-zone-mini" id="upload-zone-mini-${this.tipo}">
                        <i class="fas fa-plus-circle"></i>
                        <span>Adicionar</span>
                    </div>
                </div>
                
                <div class="foto-actions">
                    <button type="button" class="btn-camera" id="btn-add-foto-${this.tipo}">
                        <i class="fas fa-${isMobile ? 'camera' : 'cloud-upload-alt'}"></i>
                        Adicionar Foto
                    </button>
                    
                    <select id="foto-categoria-${this.tipo}" class="foto-categoria-select">
                        <option value="geral">📸 Foto Geral</option>
                        <option value="tela">📱 Foto da Tela</option>
                        <option value="avaria">⚠️ Foto de Avaria</option>
                        <option value="outro">📌 Outro</option>
                    </select>
                </div>
                
                <div class="foto-info" id="foto-info-${this.tipo}">
                    <i class="fas fa-info-circle"></i>
                    <span>Adicione até ${this.maxFotos} fotos ${this.tipo === 'retirada' ? 'da retirada' : 'da devolução'}</span>
                </div>
                
                <input type="file" 
                       id="foto-input-${this.tipo}" 
                       accept="image/*" 
                       ${isMobile ? 'capture="environment"' : ''}
                       class="hidden-input"
                       ${this.modoMultiplo ? 'multiple' : ''}>
            </div>
        `;
        
        container.innerHTML = html;
        this.bindEventsMultiplo(isMobile);
    }

    renderMobileUpload() {
        return `
            <div class="mobile-upload-area">
                <i class="fas fa-mobile-alt"></i>
                <p>Toque no botão abaixo para abrir a câmera</p>
                <small>A foto será tirada e enviada automaticamente</small>
            </div>
            <input type="file" 
                   id="foto-input-${this.tipo}" 
                   accept="image/*" 
                   capture="environment"
                   class="hidden-input">
        `;
    }

    renderDesktopUpload() {
        return `
            <div class="upload-zone" id="upload-zone-${this.tipo}">
                <i class="fas fa-cloud-upload-alt"></i>
                <p>Arraste uma foto ou clique para selecionar</p>
                <small>PNG, JPG, JPEG, GIF, WEBP (máx. 16MB)</small>
            </div>
            <input type="file" 
                   id="foto-input-${this.tipo}" 
                   accept="image/*"
                   class="hidden-input">
        `;
    }

    bindEventsUnico(isMobile) {
        const btnFoto = document.getElementById(`btn-foto-${this.tipo}`);
        const inputFoto = document.getElementById(`foto-input-${this.tipo}`);
        const btnLimpar = document.getElementById(`btn-limpar-foto-${this.tipo}`);
        const preview = document.getElementById(`foto-preview-${this.tipo}`);
        const previewImg = document.getElementById(`foto-img-${this.tipo}`);
        const pathInput = document.getElementById(`foto-path-${this.tipo}`);
        const fotoInfo = document.getElementById(`foto-info-${this.tipo}`);

        if (btnFoto) {
            btnFoto.addEventListener('click', () => {
                inputFoto.click();
            });
        }

        if (inputFoto) {
            inputFoto.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    await this.processarFotoUnica(file, preview, previewImg, pathInput, btnLimpar, fotoInfo);
                }
            });
        }

        if (!isMobile) {
            const uploadZone = document.getElementById(`upload-zone-${this.tipo}`);
            if (uploadZone) {
                uploadZone.addEventListener('click', () => {
                    inputFoto.click();
                });
                
                uploadZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    uploadZone.classList.add('drag-over');
                });
                
                uploadZone.addEventListener('dragleave', () => {
                    uploadZone.classList.remove('drag-over');
                });
                
                uploadZone.addEventListener('drop', async (e) => {
                    e.preventDefault();
                    uploadZone.classList.remove('drag-over');
                    
                    const file = e.dataTransfer.files[0];
                    if (file && file.type.startsWith('image/')) {
                        await this.processarFotoUnica(file, preview, previewImg, pathInput, btnLimpar, fotoInfo);
                    } else {
                        showNotification('Por favor, selecione uma imagem válida', 'error');
                    }
                });
            }
        }

        if (btnLimpar) {
            btnLimpar.addEventListener('click', () => {
                preview.style.display = 'none';
                previewImg.src = '';
                pathInput.value = '';
                inputFoto.value = '';
                btnLimpar.style.display = 'none';
                this.fotoPath = null;
                
                if (fotoInfo) {
                    fotoInfo.innerHTML = `
                        <i class="fas fa-info-circle"></i>
                        <span>${isMobile ? 'Toque para abrir a câmera' : 'Arraste ou clique para selecionar'}</span>
                    `;
                }
                
                this.onUploadComplete(null);
            });
        }
    }

    bindEventsMultiplo(isMobile) {
        const btnAddFoto = document.getElementById(`btn-add-foto-${this.tipo}`);
        const inputFoto = document.getElementById(`foto-input-${this.tipo}`);
        const categoriaSelect = document.getElementById(`foto-categoria-${this.tipo}`);
        const uploadZone = document.getElementById(`upload-zone-mini-${this.tipo}`);
        
        if (btnAddFoto) {
            btnAddFoto.addEventListener('click', () => {
                inputFoto.click();
            });
        }
        
        if (uploadZone) {
            uploadZone.addEventListener('click', () => {
                inputFoto.click();
            });
        }
        
        if (inputFoto) {
            inputFoto.addEventListener('change', async (e) => {
                const categoria = categoriaSelect ? categoriaSelect.value : 'geral';
                
                const files = Array.from(e.target.files);
                for (const file of files) {
                    await this.processarFotoMultipla(file, categoria);
                }
                
                inputFoto.value = '';
            });
        }
        
        if (!isMobile) {
            const grid = document.getElementById(`fotos-grid-${this.tipo}`);
            if (grid) {
                grid.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    grid.classList.add('drag-over');
                });
                
                grid.addEventListener('dragleave', () => {
                    grid.classList.remove('drag-over');
                });
                
                grid.addEventListener('drop', async (e) => {
                    e.preventDefault();
                    grid.classList.remove('drag-over');
                    
                    const files = Array.from(e.dataTransfer.files);
                    for (const file of files) {
                        if (file.type.startsWith('image/')) {
                            await this.processarFotoMultipla(file, 'geral');
                        }
                    }
                });
            }
        }
    }

    async processarFotoUnica(file, preview, previewImg, pathInput, btnLimpar, fotoInfo) {
        if (fotoInfo) {
            fotoInfo.innerHTML = `
                <span class="foto-loading"></span>
                <span>Enviando foto...</span>
            `;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            preview.style.display = 'block';
            preview.style.animation = 'cardEntrance 0.3s ease';
        };
        reader.readAsDataURL(file);

        try {
            const formData = new FormData();
            formData.append('foto', file);
            formData.append('tipo', this.tipo);
            
            if (this.tabletId || window.currentTabletId) {
                formData.append('tablet_id', this.tabletId || window.currentTabletId);
            }

            const response = await fetch('/api/upload-foto', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.success) {
                pathInput.value = data.path;
                this.fotoPath = data.path;
                btnLimpar.style.display = 'inline-flex';
                
                if (fotoInfo) {
                    fotoInfo.innerHTML = `
                        <i class="fas fa-check-circle" style="color: var(--neon-verde);"></i>
                        <span>Foto enviada com sucesso!</span>
                    `;
                }
                
                this.onUploadComplete(data.path);
                showNotification('Foto enviada com sucesso!', 'success');
            } else {
                throw new Error(data.error || 'Erro no upload');
            }
        } catch (error) {
            console.error('Erro no upload:', error);
            
            if (fotoInfo) {
                fotoInfo.innerHTML = `
                    <i class="fas fa-exclamation-circle" style="color: var(--neon-vermelho);"></i>
                    <span>Erro ao enviar foto</span>
                `;
            }
            
            preview.style.display = 'none';
            pathInput.value = '';
            
            showNotification('Erro ao enviar foto: ' + error.message, 'error');
        }
    }

    async processarFotoMultipla(file, categoria = 'geral') {
        if (this.fotos.length >= this.maxFotos) {
            showNotification(`Máximo de ${this.maxFotos} fotos atingido!`, 'error');
            return;
        }
        
        const fotoId = Date.now() + Math.random();
        this.adicionarFotoPreview(fotoId, file, categoria);
        
        try {
            const formData = new FormData();
            formData.append('foto', file);
            formData.append('tipo', this.tipo);
            formData.append('categoria', categoria);
            
            if (this.tabletId || window.currentTabletId) {
                formData.append('tablet_id', this.tabletId || window.currentTabletId);
            }

            const response = await fetch('/api/upload-foto', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.success) {
                const fotoInfo = {
                    id: fotoId,
                    caminho: data.path,
                    categoria: categoria,
                    file: file
                };
                
                this.fotos.push(fotoInfo);
                this.atualizarPreview(fotoId, data.path);
                this.atualizarContador();
                this.onFotosChange(this.fotos);
                this.onUploadComplete(data.path);
                
                showNotification('Foto adicionada com sucesso!', 'success');
            } else {
                throw new Error(data.error || 'Erro no upload');
            }
        } catch (error) {
            console.error('Erro no upload:', error);
            this.removerFoto(fotoId);
            showNotification('Erro ao enviar foto: ' + error.message, 'error');
        }
    }

    adicionarFotoPreview(fotoId, file, categoria) {
        const grid = document.getElementById(`fotos-grid-${this.tipo}`);
        if (!grid) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const fotoElement = document.createElement('div');
            fotoElement.className = 'foto-item uploading';
            fotoElement.id = `foto-${fotoId}`;
            fotoElement.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <div class="foto-overlay">
                    <span class="foto-categoria-badge">${this.getCategoriaNome(categoria)}</span>
                    <div class="foto-loading-spinner"></div>
                </div>
                <button class="foto-remove-btn" onclick="event.stopPropagation(); window.currentMultiFotoManager.removerFoto('${fotoId}')">
                    <i class="fas fa-times"></i>
                </button>
                <span class="foto-label">Enviando...</span>
            `;
            
            const uploadZone = document.getElementById(`upload-zone-mini-${this.tipo}`);
            if (uploadZone) {
                grid.insertBefore(fotoElement, uploadZone);
            } else {
                grid.appendChild(fotoElement);
            }
        };
        reader.readAsDataURL(file);
    }

    atualizarPreview(fotoId, caminho) {
        const fotoElement = document.getElementById(`foto-${fotoId}`);
        if (fotoElement) {
            fotoElement.classList.remove('uploading');
            const spinner = fotoElement.querySelector('.foto-loading-spinner');
            if (spinner) spinner.remove();
            
            const label = fotoElement.querySelector('.foto-label');
            if (label) label.textContent = 'Enviada';
            
            fotoElement.addEventListener('click', () => {
                openFotoCarrossel([{caminho: caminho, categoria: this.fotos.find(f => f.caminho === caminho)?.categoria || 'Geral'}], 0);
            });
        }
    }

    removerFoto(fotoId) {
        const fotoElement = document.getElementById(`foto-${fotoId}`);
        if (fotoElement) {
            fotoElement.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => fotoElement.remove(), 300);
        }
        
        this.fotos = this.fotos.filter(f => f.id != fotoId);
        this.atualizarContador();
        this.onFotosChange(this.fotos);
    }

    atualizarContador() {
        const counter = document.getElementById(`foto-count-${this.tipo}`);
        if (counter) {
            counter.textContent = `${this.fotos.length}/${this.maxFotos}`;
            
            if (this.fotos.length === 0) {
                counter.style.color = 'var(--neon-vermelho)';
            } else {
                counter.style.color = 'var(--neon-verde)';
            }
        }
    }

    getCategoriaNome(categoria) {
        const nomes = {
            'geral': '📸 Geral',
            'tela': '📱 Tela',
            'avaria': '⚠️ Avaria',
            'outro': '📌 Outro'
        };
        return nomes[categoria] || categoria;
    }

    async uploadBase64(imageData) {
        const preview = document.getElementById(`foto-preview-${this.tipo}`);
        const previewImg = document.getElementById(`foto-img-${this.tipo}`);
        const pathInput = document.getElementById(`foto-path-${this.tipo}`);
        const btnLimpar = document.getElementById(`btn-limpar-foto-${this.tipo}`);
        const fotoInfo = document.getElementById(`foto-info-${this.tipo}`);
        
        try {
            if (fotoInfo) {
                fotoInfo.innerHTML = `
                    <span class="foto-loading"></span>
                    <span>Enviando foto...</span>
                `;
            }
            
            const body = {
                image: imageData,
                tipo: this.tipo
            };
            
            if (this.tabletId || window.currentTabletId) {
                body.tablet_id = this.tabletId || window.currentTabletId;
            }
            
            const response = await fetch('/api/upload-foto-base64', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });

            const data = await response.json();
            
            if (data.success) {
                pathInput.value = data.path;
                this.fotoPath = data.path;
                previewImg.src = imageData;
                preview.style.display = 'block';
                preview.style.animation = 'cardEntrance 0.3s ease';
                btnLimpar.style.display = 'inline-flex';
                
                if (fotoInfo) {
                    fotoInfo.innerHTML = `
                        <i class="fas fa-check-circle" style="color: var(--neon-verde);"></i>
                        <span>Foto enviada com sucesso!</span>
                    `;
                }
                
                this.onUploadComplete(data.path);
                showNotification('Foto capturada com sucesso!', 'success');
                return true;
            } else {
                throw new Error(data.error || 'Erro no upload');
            }
        } catch (error) {
            console.error('Erro no upload:', error);
            
            if (fotoInfo) {
                fotoInfo.innerHTML = `
                    <i class="fas fa-exclamation-circle" style="color: var(--neon-vermelho);"></i>
                    <span>Erro ao enviar foto</span>
                `;
            }
            
            showNotification('Erro ao enviar foto: ' + error.message, 'error');
            return false;
        }
    }

    getFotoPath() {
        return this.fotoPath || document.getElementById(`foto-path-${this.tipo}`)?.value || null;
    }

    getFotos() {
        return this.fotos;
    }

    getFotosPaths() {
        return this.fotos.map(f => f.caminho);
    }

    temFotos() {
        return this.fotos.length > 0;
    }

    temFotoCategoria(categoria) {
        return this.fotos.some(f => f.categoria === categoria);
    }

    // ✅ NOVOS MÉTODOS - DENTRO DA CLASSE
    temUploadPendente() {
        const grid = document.getElementById(`fotos-grid-${this.tipo}`);
        if (grid) {
            const uploadingItems = grid.querySelectorAll('.foto-item.uploading');
            return uploadingItems.length > 0;
        }
        return false;
    }

    getFotosEnviadas() {
        return this.fotos.filter(f => {
            const fotoElement = document.getElementById(`foto-${f.id}`);
            return fotoElement && !fotoElement.classList.contains('uploading');
        });
    }

    setFotoExistente(path) {
        if (!path) return;
        
        this.fotoPath = path;
        const pathInput = document.getElementById(`foto-path-${this.tipo}`);
        const preview = document.getElementById(`foto-preview-${this.tipo}`);
        const previewImg = document.getElementById(`foto-img-${this.tipo}`);
        const btnLimpar = document.getElementById(`btn-limpar-foto-${this.tipo}`);
        const fotoInfo = document.getElementById(`foto-info-${this.tipo}`);
        
        if (pathInput) pathInput.value = path;
        if (preview && previewImg) {
            previewImg.src = `/static/uploads/${path}`;
            preview.style.display = 'block';
        }
        if (btnLimpar) btnLimpar.style.display = 'inline-flex';
        if (fotoInfo) {
            fotoInfo.innerHTML = `
                <i class="fas fa-image" style="color: var(--neon-azul);"></i>
                <span>Foto carregada</span>
            `;
        }
    }
}

// Classe para modo múltiplo (compatibilidade)
class MultiFotoUploadManager extends FotoUploadManager {
    constructor(options = {}) {
        super({
            ...options,
            modoMultiplo: true
        });
    }
}

// ========== FUNÇÕES DO CARROSSEL ==========

let carrosselState = {
    fotos: [],
    indexAtual: 0,
    touchStartX: 0,
    touchEndX: 0
};

function openFotoCarrossel(fotos, indexInicial = 0) {
    if (!fotos || fotos.length === 0) return;
    
    carrosselState.fotos = fotos;
    carrosselState.indexAtual = indexInicial;
    
    const modal = document.getElementById('foto-modal');
    const img = document.getElementById('foto-modal-img');
    const title = document.getElementById('foto-modal-title');
    const contador = document.getElementById('carrossel-contador');
    const indicadores = document.getElementById('carrossel-indicadores');
    const infoAtual = document.getElementById('foto-info-atual');
    
    if (!modal || !img) return;
    
    if (title) {
        title.innerHTML = `<i class="fas fa-images"></i> Visualizar Fotos (${fotos.length})`;
    }
    
    atualizarImagemCarrossel(img, infoAtual, contador, indicadores);
    
    if (indicadores) {
        indicadores.innerHTML = '';
        fotos.forEach((foto, i) => {
            const indicador = document.createElement('span');
            indicador.className = `carrossel-indicador ${i === carrosselState.indexAtual ? 'ativo' : ''}`;
            indicador.onclick = () => navegarParaFoto(i);
            indicadores.appendChild(indicador);
        });
    }
    
    atualizarBotoesNavegacao();
    
    const container = document.getElementById('carrossel-container');
    if (container) {
        container.addEventListener('touchstart', handleTouchStart);
        container.addEventListener('touchmove', handleTouchMove);
        container.addEventListener('touchend', handleTouchEnd);
    }
    
    document.addEventListener('keydown', handleKeyDown);
    
    modal.style.display = 'block';
    modal.style.animation = 'slideUp 0.3s ease';
}

function atualizarImagemCarrossel(img, infoAtual, contador, indicadores) {
    const foto = carrosselState.fotos[carrosselState.indexAtual];
    if (!foto) return;
    
    img.style.opacity = '0.5';
    
    const imgPath = foto.caminho || foto;
    img.src = `/static/uploads/${imgPath}`;
    img.alt = foto.categoria || 'Foto';
    
    img.onload = () => {
        img.style.opacity = '1';
    };
    
    if (infoAtual) {
        const categoria = foto.categoria || 'Geral';
        const icone = 
            categoria === 'avaria' ? '⚠️' :
            categoria === 'tela' ? '📱' :
            categoria === 'geral' ? '📸' : '📌';
        
        infoAtual.innerHTML = `
            <span class="foto-categoria-badge">${icone} ${categoria}</span>
            ${foto.data_upload ? `<span class="foto-data"><i class="far fa-calendar-alt"></i> ${foto.data_upload}</span>` : ''}
        `;
    }
    
    if (contador) {
        contador.textContent = `${carrosselState.indexAtual + 1} / ${carrosselState.fotos.length}`;
    }
    
    if (indicadores) {
        const indicadoresList = indicadores.children;
        for (let i = 0; i < indicadoresList.length; i++) {
            indicadoresList[i].classList.toggle('ativo', i === carrosselState.indexAtual);
        }
    }
}

function navegarParaFoto(index) {
    if (index < 0 || index >= carrosselState.fotos.length) return;
    
    const direction = index > carrosselState.indexAtual ? 'right' : 'left';
    carrosselState.indexAtual = index;
    
    const img = document.getElementById('foto-modal-img');
    const infoAtual = document.getElementById('foto-info-atual');
    const contador = document.getElementById('carrossel-contador');
    const indicadores = document.getElementById('carrossel-indicadores');
    
    img.classList.add(direction === 'right' ? 'foto-slide-right' : 'foto-slide-left');
    
    atualizarImagemCarrossel(img, infoAtual, contador, indicadores);
    atualizarBotoesNavegacao();
    
    setTimeout(() => {
        img.classList.remove('foto-slide-right', 'foto-slide-left');
    }, 300);
}

function navegarCarrossel(direcao) {
    const novoIndex = carrosselState.indexAtual + direcao;
    if (novoIndex >= 0 && novoIndex < carrosselState.fotos.length) {
        navegarParaFoto(novoIndex);
    }
}

function atualizarBotoesNavegacao() {
    const btnPrev = document.getElementById('carrossel-prev');
    const btnNext = document.getElementById('carrossel-next');
    
    if (btnPrev) btnPrev.disabled = carrosselState.indexAtual === 0;
    if (btnNext) btnNext.disabled = carrosselState.indexAtual === carrosselState.fotos.length - 1;
}

function handleTouchStart(e) {
    carrosselState.touchStartX = e.touches[0].clientX;
}

function handleTouchMove(e) {
    carrosselState.touchEndX = e.touches[0].clientX;
}

function handleTouchEnd() {
    const diff = carrosselState.touchStartX - carrosselState.touchEndX;
    const threshold = 50;
    
    if (Math.abs(diff) > threshold) {
        if (diff > 0) {
            navegarCarrossel(1);
        } else {
            navegarCarrossel(-1);
        }
    }
}

function handleKeyDown(e) {
    if (document.getElementById('foto-modal').style.display !== 'block') return;
    
    if (e.key === 'ArrowLeft') {
        navegarCarrossel(-1);
    } else if (e.key === 'ArrowRight') {
        navegarCarrossel(1);
    } else if (e.key === 'Escape') {
        closeFotoModal();
    }
}

function closeFotoModal() {
    const modal = document.getElementById('foto-modal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.2s ease';
        setTimeout(() => {
            modal.style.display = 'none';
            modal.style.animation = '';
            document.removeEventListener('keydown', handleKeyDown);
            carrosselState.fotos = [];
            carrosselState.indexAtual = 0;
        }, 200);
    }
}

function openFotoModal(imgSrc) {
    const foto = {
        caminho: imgSrc.replace('/static/uploads/', ''),
        categoria: 'Geral'
    };
    openFotoCarrossel([foto], 0);
}

function abrirCarrosselHistorico(fotos, indexInicial = 0) {
    openFotoCarrossel(fotos, indexInicial);
}

function showNotification(message, type = 'success') {
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        console.log(`[${type}] ${message}`);
    }
}

// Exportar para uso global
window.FotoUploadManager = FotoUploadManager;
window.MultiFotoUploadManager = MultiFotoUploadManager;
window.openFotoCarrossel = openFotoCarrossel;
window.openFotoModal = openFotoModal;
window.closeFotoModal = closeFotoModal;
window.navegarCarrossel = navegarCarrossel;
window.abrirCarrosselHistorico = abrirCarrosselHistorico;