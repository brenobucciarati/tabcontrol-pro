# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, flash
from flask_cors import CORS
from database import db, Tablet, Historico, FotosHistorico, Usuario, LogSistema
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid
import base64
from io import BytesIO
from PIL import Image
import secrets

# ==================== CONFIGURAÇÃO CLOUDINARY ====================
USE_CLOUDINARY = True  # ← Mude para True para usar Cloudinary

if USE_CLOUDINARY:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    cloudinary.config(
        cloud_name="SEU_CLOUD_NAME",      # ← SUBSTITUA PELO SEU
        api_key="SEU_API_KEY",            # ← SUBSTITUA PELO SEU
        api_secret="SEU_API_SECRET"       # ← SUBSTITUA PELO SEU
    )


# Importações para autenticação
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuração
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tabcontrol.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPLOAD_FOLDER_FOTOS'] = 'static/uploads/fotos'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.secret_key = secrets.token_hex(32)  # Chave secreta para sessão

# Criar pasta de uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER_FOTOS'], exist_ok=True)

db.init_app(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== FUNÇÕES DE AUTENTICAÇÃO ====================

def hash_senha(senha):
    """Gera hash da senha"""
    return generate_password_hash(senha, method='pbkdf2:sha256')

def verificar_senha(senha_hash, senha):
    """Verifica se a senha está correta"""
    return check_password_hash(senha_hash, senha)

def login_required(f):
    """Decorator para rotas que exigem login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Não autorizado', 'redirect': '/login'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para rotas que exigem permissão de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Não autorizado', 'redirect': '/login'}), 401
            return redirect(url_for('login_page'))
        
        if session.get('cargo') != 'admin':
            if request.is_json:
                return jsonify({'error': 'Permissão negada'}), 403
            flash('Acesso restrito a administradores', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def registrar_log(usuario_id, acao, descricao, tablet_id=None):
    """Registra uma ação no sistema"""
    try:
        log = LogSistema(
            usuario_id=usuario_id,
            acao=acao,
            descricao=descricao,
            tablet_id=tablet_id,
            ip=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def criar_usuario_admin():
    """Cria o usuário administrador padrão se não existir"""
    admin = Usuario.query.filter_by(email='admin@tabcontrol.com').first()
    if not admin:
        admin = Usuario(
            nome='Administrador',
            email='admin@tabcontrol.com',
            senha=hash_senha('admin123'),
            cargo='admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário administrador criado!")
        print("   Email: admin@tabcontrol.com")
        print("   Senha: admin123")


# NOVA FUNÇÃO: Salvar foto com estrutura organizada
def salvar_foto_organizada(file, tipo, tablet_numero=None):
    """
    Salva a foto na estrutura:
    uploads/fotos/tablet_XX/YYYY-MM-DD/tipo/foto_HHMMSS.jpg
    """
    agora = datetime.now()
    data_pasta = agora.strftime('%Y-%m-%d')
    hora_arquivo = agora.strftime('%H%M%S')
    
    # Formatar número do tablet (ex: 1 -> 01)
    if not tablet_numero:
        tablet_numero = 'geral'
    else:
        tablet_numero = str(tablet_numero).zfill(2)
    
    # Criar o caminho da pasta
    pasta_base = app.config['UPLOAD_FOLDER_FOTOS']
    pasta_tablet = os.path.join(pasta_base, f'tablet_{tablet_numero}')
    pasta_data = os.path.join(pasta_tablet, data_pasta)
    pasta_tipo = os.path.join(pasta_data, tipo)
    
    # Criar todas as pastas necessárias
    os.makedirs(pasta_tipo, exist_ok=True)
    
    # Gerar nome do arquivo
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    nome_arquivo = f"{tipo}_{hora_arquivo}.{ext}"
    caminho_completo = os.path.join(pasta_tipo, nome_arquivo)
    
    # Salvar e redimensionar imagem
    try:
        image = Image.open(file)
        max_size = (1024, 1024)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        if image.mode in ('RGBA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        
        image.save(caminho_completo, 'JPEG', quality=85)
    except Exception as e:
        print(f"Erro ao processar imagem: {e}")
        file.save(caminho_completo)
    
    # Retornar caminho relativo para o banco de dados
    caminho_relativo = f"fotos/tablet_{tablet_numero}/{data_pasta}/{tipo}/{nome_arquivo}"
    
    print(f"📁 Foto salva em: {caminho_relativo}")
    return caminho_relativo

# ==================== FUNÇÃO CLOUDINARY ====================

def salvar_foto_cloudinary(file, tipo, tablet_numero=None):
    """Faz upload da foto para o Cloudinary"""
    agora = datetime.now()
    data_pasta = agora.strftime('%Y-%m-%d')
    hora_arquivo = agora.strftime('%H%M%S')
    
    if not tablet_numero:
        tablet_numero = 'geral'
    else:
        tablet_numero = str(tablet_numero).zfill(2)
    
    folder_path = f"tabcontrol/tablet_{tablet_numero}/{data_pasta}/{tipo}"
    public_id = f"{tipo}_{hora_arquivo}"
    
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder_path,
            public_id=public_id,
            overwrite=False,
            resource_type="image"
        )
        print(f"📁 Foto enviada para Cloudinary: {result['secure_url']}")
        return result['secure_url']
    except Exception as e:
        print(f"❌ Erro no Cloudinary, salvando localmente: {e}")
        return salvar_foto_organizada(file, tipo, tablet_numero)


# ==================== INICIALIZAÇÃO ====================

with app.app_context():
    db.create_all()
    criar_usuario_admin()  # Cria admin padrão
    
    if Tablet.query.count() == 0:
        # Lista dos tablets conforme especificação
        tablets_iniciais = []
        
        # Tablets 01 ao 03 - Samsung Tab A9
        for i in range(1, 4):
            tablets_iniciais.append({
                'numero': f"{i:02d}",
                'modelo': 'Samsung Tab A9',
                'cor': '#4158D0',  # Azul
                'imagem': 'default.png'
            })
        
        # Tablets 04 ao 05 - Samsung Tab A9+
        for i in range(4, 6):
            tablets_iniciais.append({
                'numero': f"{i:02d}",
                'modelo': 'Samsung Tab A9+',
                'cor': '#C850C0',  # Roxo
                'imagem': 'default.png'
            })
        
        # Tablets 06 ao 40 - Lenovo Tab (35 tablets)
        for i in range(6, 41):
            tablets_iniciais.append({
                'numero': f"{i:02d}",
                'modelo': 'Lenovo Tab',
                'cor': '#00ff88',  # Verde Neon
                'imagem': 'default.png'
            })
        
        # Inserir todos no banco de dados
        for tablet_data in tablets_iniciais:
            tablet = Tablet(
                numero=tablet_data['numero'],
                modelo=tablet_data['modelo'],
                cor=tablet_data['cor'],
                imagem=tablet_data['imagem']
            )
            db.session.add(tablet)
        
        db.session.commit()
        print("✅ 40 tablets criados com sucesso!")
        print("   - Tablets 01-03: Samsung Tab A9")
        print("   - Tablets 04-05: Samsung Tab A9+")
        print("   - Tablets 06-40: Lenovo Tab")


# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/login')
def login_page():
    """Página de login"""
    if 'usuario_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    """API de autenticação"""
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    
    usuario = Usuario.query.filter_by(email=email, ativo=True).first()
    
    if not usuario or not verificar_senha(usuario.senha, senha):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
    
    # Atualizar último login
    usuario.ultimo_login = datetime.now()
    
    # Registrar na sessão
    session['usuario_id'] = usuario.id
    session['usuario_nome'] = usuario.nome
    session['usuario_email'] = usuario.email
    session['cargo'] = usuario.cargo
    
    db.session.commit()
    
    # Registrar log
    registrar_log(usuario.id, 'login', f'Login no sistema', None)
    
    return jsonify({
        'success': True,
        'usuario': usuario.to_dict(),
        'redirect': url_for('index')
    })

@app.route('/logout')
def logout():
    """Logout do sistema"""
    if 'usuario_id' in session:
        registrar_log(session['usuario_id'], 'logout', f'Logout do sistema', None)
        session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/usuario/atual', methods=['GET'])
@login_required
def usuario_atual():
    """Retorna o usuário logado"""
    usuario = Usuario.query.get(session['usuario_id'])
    if not usuario:
        session.clear()
        return jsonify({'error': 'Usuário não encontrado'}), 401
    return jsonify(usuario.to_dict())


# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/cadastro')
@login_required
def cadastro():
    return render_template('cadastro.html')

@app.route('/historico')
@login_required
def historico():
    return render_template('historico.html')


# ==================== ROTAS DE ADMIN ====================

@app.route('/admin')
@admin_required
def admin_panel():
    """Painel de administração"""
    return render_template('admin.html')

@app.route('/admin/logs')
@admin_required
def logs_page():
    """Página de logs do sistema"""
    return render_template('logs.html')

@app.route('/api/usuarios', methods=['GET'])
@admin_required
def listar_usuarios():
    """Lista todos os usuários (apenas admin)"""
    usuarios = Usuario.query.all()
    return jsonify([u.to_dict_admin() for u in usuarios])

@app.route('/api/usuarios', methods=['POST'])
@admin_required
def criar_usuario():
    """Cria um novo usuário (apenas admin)"""
    data = request.json
    
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 400
    
    usuario = Usuario(
        nome=data['nome'],
        email=data['email'],
        senha=hash_senha(data['senha']),
        cargo=data.get('cargo', 'operador'),
        ativo=data.get('ativo', True)
    )
    
    db.session.add(usuario)
    db.session.commit()
    
    registrar_log(
        session['usuario_id'],
        'cadastro_usuario',
        f'Cadastrou o usuário {usuario.nome} ({usuario.email})',
        None
    )
    
    return jsonify(usuario.to_dict()), 201

@app.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
@admin_required
def atualizar_usuario(usuario_id):
    """Atualiza um usuário (apenas admin)"""
    usuario = Usuario.query.get_or_404(usuario_id)
    data = request.json
    
    usuario.nome = data.get('nome', usuario.nome)
    usuario.email = data.get('email', usuario.email)
    usuario.cargo = data.get('cargo', usuario.cargo)
    usuario.ativo = data.get('ativo', usuario.ativo)
    
    if data.get('senha'):
        usuario.senha = hash_senha(data['senha'])
    
    db.session.commit()
    
    registrar_log(
        session['usuario_id'],
        'edicao_usuario',
        f'Editou o usuário {usuario.nome}',
        None
    )
    
    return jsonify(usuario.to_dict())

@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
@admin_required
def deletar_usuario(usuario_id):
    """Desativa um usuário (apenas admin)"""
    usuario = Usuario.query.get_or_404(usuario_id)
    
    # Não permitir deletar o próprio usuário
    if usuario.id == session['usuario_id']:
        return jsonify({'error': 'Não é possível excluir seu próprio usuário'}), 400
    
    usuario.ativo = False
    db.session.commit()
    
    registrar_log(
        session['usuario_id'],
        'exclusao_usuario',
        f'Desativou o usuário {usuario.nome}',
        None
    )
    
    return jsonify({'message': 'Usuário desativado'})

@app.route('/api/logs', methods=['GET'])
@admin_required
def listar_logs():
    """Lista todos os logs do sistema (apenas admin)"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    logs = LogSistema.query.order_by(LogSistema.data.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': logs.page
    })


# ==================== API - UPLOAD DE FOTOS ====================

@app.route('/static/uploads/fotos/<path:filepath>')
def serve_foto_organizada(filepath):
    """Serve as fotos da nova estrutura de pastas"""
    return send_from_directory(app.config['UPLOAD_FOLDER_FOTOS'], filepath)

@app.route('/api/upload-foto-base64', methods=['POST'])
@login_required
def upload_foto_base64():
    """Recebe foto em base64 do app mobile com organização por tablet/data"""
    try:
        data = request.json
        image_data = data.get('image')
        tipo = data.get('tipo')
        tablet_id = data.get('tablet_id')
        
        if not image_data or not tipo:
            return jsonify({'error': 'Dados incompletos'}), 400
        
        tablet_numero = None
        if tablet_id:
            tablet = Tablet.query.get(tablet_id)
            if tablet:
                tablet_numero = tablet.numero
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        from werkzeug.datastructures import FileStorage
        file = FileStorage(
            stream=BytesIO(image_bytes),
            filename=f"mobile_upload.jpg"
        )
        
        if USE_CLOUDINARY:
            caminho = salvar_foto_cloudinary(file, tipo, tablet_numero)
        else:
            caminho = salvar_foto_organizada(file, tipo, tablet_numero)
        
        return jsonify({
            'success': True,
            'path': caminho
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-foto', methods=['POST'])
@login_required
def upload_foto():
    """Recebe arquivo de foto do desktop com organização por tablet/data"""
    try:
        if 'foto' not in request.files:
            return jsonify({'error': 'Nenhuma foto enviada'}), 400
        
        file = request.files['foto']
        tipo = request.form.get('tipo')
        tablet_id = request.form.get('tablet_id')
        
        if file.filename == '':
            return jsonify({'error': 'Nome de arquivo vazio'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Formato de arquivo não permitido'}), 400
        
        tablet_numero = None
        if tablet_id:
            tablet = Tablet.query.get(tablet_id)
            if tablet:
                tablet_numero = tablet.numero
        
        caminho_relativo = salvar_foto_organizada(file, tipo, tablet_numero)
        
        return jsonify({
            'success': True,
            'path': caminho_relativo
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== API - TABLETS ====================

@app.route('/api/tablets', methods=['GET'])
@login_required
def listar_tablets():
    tablets = Tablet.query.all()
    return jsonify([tablet.to_dict() for tablet in tablets])

@app.route('/api/tablets/<int:tablet_id>', methods=['GET'])
@login_required
def buscar_tablet(tablet_id):
    tablet = Tablet.query.get_or_404(tablet_id)
    return jsonify(tablet.to_dict())

@app.route('/api/tablets', methods=['POST'])
@login_required
def criar_tablet():
    data = request.form
    
    if Tablet.query.filter_by(numero=data['numero']).first():
        return jsonify({'error': 'Número já existe'}), 400
    
    imagem = 'default.png'
    if 'imagem' in request.files:
        file = request.files['imagem']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            novo_nome = f"tablet_{data['numero']}_{uuid.uuid4().hex[:8]}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], novo_nome))
            imagem = novo_nome
    
    tablet = Tablet(
        numero=data['numero'],
        modelo=data['modelo'],
        cor=data.get('cor', '#4158D0'),
        imagem=imagem
    )
    
    db.session.add(tablet)
    db.session.commit()
    
    registrar_log(
        session['usuario_id'],
        'cadastro_tablet',
        f'Cadastrou o tablet {tablet.numero}',
        tablet.id
    )
    
    return jsonify(tablet.to_dict()), 201

@app.route('/api/tablets/<int:tablet_id>', methods=['DELETE'])
@admin_required
def deletar_tablet(tablet_id):
    tablet = Tablet.query.get_or_404(tablet_id)
    
    if tablet.imagem and tablet.imagem != 'default.png':
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], tablet.imagem))
        except:
            pass
    
    registrar_log(
        session['usuario_id'],
        'exclusao_tablet',
        f'Excluiu o tablet {tablet.numero}',
        tablet.id
    )
    
    db.session.delete(tablet)
    db.session.commit()
    return jsonify({'message': 'Tablet removido'})


# ==================== API - RETIRADA E DEVOLUÇÃO ====================

@app.route('/api/tablets/<int:tablet_id>/retirar', methods=['POST'])
@login_required
def retirar_tablet(tablet_id):
    tablet = Tablet.query.get_or_404(tablet_id)
    data = request.json
    
    if tablet.status == 'em_uso':
        return jsonify({'error': 'Tablet já está em uso'}), 400
    
    historico = Historico(
        tablet_id=tablet.id,
        usuario_nome=data['usuario'],
        usuario_id=session['usuario_id'],
        liberado_por=session['usuario_nome'],
        checklist_retirada_estado=data.get('checklist_estado'),
        checklist_retirada_rede=data.get('checklist_rede'),
        checklist_retirada_carga=data.get('checklist_carga')
    )
    
    db.session.add(historico)
    db.session.flush()
    
    fotos = data.get('fotos', [])
    
    if fotos and len(fotos) > 0:
        if isinstance(fotos[0], dict):
            historico.foto_retirada = fotos[0].get('caminho')
        else:
            historico.foto_retirada = fotos[0]
        
        for foto_data in fotos:
            if isinstance(foto_data, dict):
                caminho = foto_data.get('caminho')
                categoria = foto_data.get('categoria', 'geral')
            else:
                caminho = foto_data
                categoria = 'geral'
            
            if caminho:
                foto = FotosHistorico(
                    historico_id=historico.id,
                    tipo='retirada',
                    categoria=categoria,
                    caminho=caminho
                )
                db.session.add(foto)
                print(f"📸 Foto de retirada salva: {caminho} - {categoria}")
    
    tablet.status = 'em_uso'
    db.session.commit()
    
    registrar_log(
        session['usuario_id'],
        'retirada',
        f'Retirou o tablet {tablet.numero} para {data["usuario"]}',
        tablet.id
    )
    
    return jsonify(tablet.to_dict())

@app.route('/api/tablets/<int:tablet_id>/devolver', methods=['POST'])
@login_required
def devolver_tablet(tablet_id):
    tablet = Tablet.query.get_or_404(tablet_id)
    data = request.json
    
    if tablet.status == 'disponivel':
        return jsonify({'error': 'Tablet já está disponível'}), 400
    
    historico = Historico.query.filter_by(
        tablet_id=tablet.id,
        data_devolucao=None
    ).first()
    
    if historico:
        historico.data_devolucao = datetime.now()
        historico.checklist_devolucao_estado = data.get('checklist_devolucao_estado')
        historico.recebido_por_id = session['usuario_id']
        
        fotos = data.get('fotos', [])
        
        if fotos and len(fotos) > 0:
            if isinstance(fotos[0], dict):
                historico.foto_devolucao = fotos[0].get('caminho')
            else:
                historico.foto_devolucao = fotos[0]
            
            for foto_data in fotos:
                if isinstance(foto_data, dict):
                    caminho = foto_data.get('caminho')
                    categoria = foto_data.get('categoria', 'geral')
                else:
                    caminho = foto_data
                    categoria = 'geral'
                
                if caminho:
                    foto = FotosHistorico(
                        historico_id=historico.id,
                        tipo='devolucao',
                        categoria=categoria,
                        caminho=caminho
                    )
                    db.session.add(foto)
                    print(f"📸 Foto de devolução salva: {caminho} - {categoria}")
    
    tablet.status = 'disponivel'
    db.session.commit()
    
    registrar_log(
        session['usuario_id'],
        'devolucao',
        f'Recebeu a devolução do tablet {tablet.numero}',
        tablet.id
    )
    
    return jsonify(tablet.to_dict())


# ==================== API - HISTÓRICOS ====================

@app.route('/api/historico/geral', methods=['GET'])
@login_required
def historico_geral():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    historicos = Historico.query.order_by(Historico.data_retirada.desc())\
                               .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [h.to_dict() for h in historicos.items],
        'total': historicos.total,
        'pages': historicos.pages,
        'current_page': historicos.page
    })

@app.route('/api/historico/completo', methods=['GET'])
@login_required
def historico_completo():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', 'todos')
    busca = request.args.get('busca', '')
    
    query = Historico.query
    
    if status == 'retirados':
        query = query.filter(Historico.data_devolucao == None)
    elif status == 'devolvidos':
        query = query.filter(Historico.data_devolucao != None)
    
    if busca:
        query = query.filter(
            db.or_(
                Historico.usuario_nome.ilike(f'%{busca}%'),
                Historico.tablet.has(Tablet.numero.ilike(f'%{busca}%'))
            )
        )
    
    historicos = query.order_by(Historico.data_retirada.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [{
            'id': h.id,
            'tablet_id': h.tablet_id,
            'tablet_numero': h.tablet.numero,
            'tablet_modelo': h.tablet.modelo,
            'usuario': h.usuario_nome,
            'entregue_por': h.entregue_por.nome if h.entregue_por else h.liberado_por,
            'liberado_por': h.liberado_por,
            'recebido_por': h.recebido_por.nome if h.recebido_por else None,
            'data_retirada': h.data_retirada.strftime('%d/%m/%Y %H:%M'),
            'data_devolucao': h.data_devolucao.strftime('%d/%m/%Y %H:%M') if h.data_devolucao else None,
            'tempo_uso': h.tempo_uso(),
            'checklist_retirada': {
                'estado': h.checklist_retirada_estado,
                'rede': h.checklist_retirada_rede,
                'carga': h.checklist_retirada_carga
            },
            'checklist_devolucao': {
                'estado': h.checklist_devolucao_estado
            },
            'foto_retirada': h.foto_retirada,
            'foto_devolucao': h.foto_devolucao,
            'fotos': [foto.to_dict() for foto in h.fotos]
        } for h in historicos.items],
        'total': historicos.total,
        'pages': historicos.pages,
        'current_page': historicos.page
    })

@app.route('/api/tablets/<int:tablet_id>/historico', methods=['GET'])
@login_required
def historico_tablet(tablet_id):
    historicos = Historico.query.filter_by(tablet_id=tablet_id)\
                               .order_by(Historico.data_retirada.desc())\
                               .limit(10).all()
    
    return jsonify([{
        'id': h.id,
        'usuario': h.usuario_nome,
        'entregue_por': h.entregue_por.nome if h.entregue_por else h.liberado_por,
        'liberado_por': h.liberado_por,
        'recebido_por': h.recebido_por.nome if h.recebido_por else None,
        'data_retirada': h.data_retirada.strftime('%d/%m/%Y %H:%M'),
        'data_devolucao': h.data_devolucao.strftime('%d/%m/%Y %H:%M') if h.data_devolucao else None,
        'tempo_uso': h.tempo_uso(),
        'checklist_retirada': {
            'estado': h.checklist_retirada_estado,
            'rede': h.checklist_retirada_rede,
            'carga': h.checklist_retirada_carga
        },
        'checklist_devolucao': {
            'estado': h.checklist_devolucao_estado
        },
        'foto_retirada': h.foto_retirada,
        'foto_devolucao': h.foto_devolucao,
        'fotos': [foto.to_dict() for foto in h.fotos]
    } for h in historicos])


# ==================== API - ESTATÍSTICAS ====================

@app.route('/api/estatisticas', methods=['GET'])
@login_required
def estatisticas():
    total = Tablet.query.count()
    disponiveis = Tablet.query.filter_by(status='disponivel').count()
    em_uso = Tablet.query.filter_by(status='em_uso').count()
    
    ultimas = Historico.query.order_by(Historico.data_retirada.desc()).limit(5).all()
    
    return jsonify({
        'total': total,
        'disponiveis': disponiveis,
        'em_uso': em_uso,
        'ultimas_movimentacoes': [{
            'tablet': h.tablet.numero,
            'usuario': h.usuario_nome,
            'acao': 'Retirada' if not h.data_devolucao else 'Devolução',
            'data': h.data_retirada.strftime('%H:%M') if not h.data_devolucao 
                    else h.data_devolucao.strftime('%H:%M')
        } for h in ultimas]
    })

@app.route('/api/estatisticas/detalhadas', methods=['GET'])
@login_required
def estatisticas_detalhadas():
    total = Tablet.query.count()
    disponiveis = Tablet.query.filter_by(status='disponivel').count()
    em_uso = Tablet.query.filter_by(status='em_uso').count()
    
    retiradas_ok_estado = Historico.query.filter(
        Historico.checklist_retirada_estado == 'sim'
    ).count()
    
    retiradas_ok_rede = Historico.query.filter(
        Historico.checklist_retirada_rede == 'sim'
    ).count()
    
    retiradas_ok_carga = Historico.query.filter(
        Historico.checklist_retirada_carga == 'sim'
    ).count()
    
    devolucoes_ok_estado = Historico.query.filter(
        Historico.checklist_devolucao_estado == 'sim'
    ).count()
    
    devolucoes_com_avaria = Historico.query.filter(
        Historico.checklist_devolucao_estado == 'nao'
    ).count()
    
    total_fotos_retirada = Historico.query.filter(
        Historico.foto_retirada.isnot(None)
    ).count()
    
    total_fotos_devolucao = Historico.query.filter(
        Historico.foto_devolucao.isnot(None)
    ).count()
    
    return jsonify({
        'total': total,
        'disponiveis': disponiveis,
        'em_uso': em_uso,
        'checklist': {
            'retiradas_estado_ok': retiradas_ok_estado,
            'retiradas_rede_ok': retiradas_ok_rede,
            'retiradas_carga_ok': retiradas_ok_carga,
            'devolucoes_ok': devolucoes_ok_estado,
            'devolucoes_com_avaria': devolucoes_com_avaria
        },
        'fotos': {
            'total_retirada': total_fotos_retirada,
            'total_devolucao': total_fotos_devolucao
        }
    })

# ==================== sSUPORTE PARA PWA====================

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)