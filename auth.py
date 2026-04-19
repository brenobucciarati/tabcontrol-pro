# auth.py
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, Usuario, LogSistema
from datetime import datetime
import hashlib
import secrets

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
                return jsonify({'error': 'Não autorizado'}), 401
            flash('Faça login para continuar', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para rotas que exigem permissão de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Não autorizado'}), 401
            flash('Faça login para continuar', 'warning')
            return redirect(url_for('login'))
        
        if session.get('cargo') != 'admin':
            if request.is_json:
                return jsonify({'error': 'Permissão negada'}), 403
            flash('Acesso restrito a administradores', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def registrar_log(usuario_id, acao, descricao, tablet_id=None):
    """Registra uma ação no sistema"""
    log = LogSistema(
        usuario_id=usuario_id,
        acao=acao,
        descricao=descricao,
        tablet_id=tablet_id,
        ip=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

def criar_usuario_admin():
    """Cria o usuário administrador padrão se não existir"""
    from app import app
    with app.app_context():
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