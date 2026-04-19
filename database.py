# database.py - Versão final completa com autenticação
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==================== TABELAS EXISTENTES ====================

class Tablet(db.Model):
    __tablename__ = 'tablets'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(10), unique=True, nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='disponivel')
    cor = db.Column(db.String(20), default='#3498db')
    imagem = db.Column(db.String(200), default='default.png')
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    
    historicos = db.relationship('Historico', backref='tablet', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('LogSistema', backref='tablet', lazy=True)
    
    def to_dict(self):
        ultimo_uso = Historico.query.filter_by(
            tablet_id=self.id, 
            data_devolucao=None
        ).first()
        
        ultimo_registro = Historico.query.filter_by(
            tablet_id=self.id
        ).order_by(Historico.data_retirada.desc()).first()
        
        return {
            'id': self.id,
            'numero': self.numero,
            'modelo': self.modelo,
            'status': self.status,
            'cor': self.cor,
            'imagem': self.imagem,
            'usuario_atual': ultimo_uso.usuario_nome if ultimo_uso else '',
            'hora_retirada': ultimo_uso.data_retirada.strftime('%H:%M') if ultimo_uso else '',
            'data_retirada': ultimo_uso.data_retirada.strftime('%d/%m/%Y %H:%M') if ultimo_uso else '',
            'ultimo_usuario': ultimo_registro.usuario_nome if ultimo_registro and ultimo_registro.data_devolucao else '',
            'ultima_devolucao': ultimo_registro.data_devolucao.strftime('%d/%m/%Y %H:%M') if ultimo_registro and ultimo_registro.data_devolucao else ''
        }


class Historico(db.Model):
    __tablename__ = 'historicos'
    
    id = db.Column(db.Integer, primary_key=True)
    tablet_id = db.Column(db.Integer, db.ForeignKey('tablets.id'), nullable=False)
    
    # NOVOS CAMPOS - Relacionamento com usuários
    usuario_nome = db.Column(db.String(100), nullable=False)  # Nome do colaborador que pegou
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)  # Usuário que entregou
    liberado_por = db.Column(db.String(100), nullable=False)  # Nome de quem liberou (compatibilidade)
    recebido_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)  # Usuário que recebeu na devolução
    
    data_retirada = db.Column(db.DateTime, default=datetime.now)
    data_devolucao = db.Column(db.DateTime, nullable=True)
    
    checklist_retirada_estado = db.Column(db.String(10), nullable=True)
    checklist_retirada_rede = db.Column(db.String(10), nullable=True)
    checklist_retirada_carga = db.Column(db.String(10), nullable=True)
    checklist_devolucao_estado = db.Column(db.String(10), nullable=True)
    
    foto_retirada = db.Column(db.String(500), nullable=True)
    foto_devolucao = db.Column(db.String(500), nullable=True)
    
    fotos = db.relationship('FotosHistorico', backref='historico', lazy=True, cascade='all, delete-orphan')
    
    # Relacionamentos com usuários
    entregue_por = db.relationship('Usuario', foreign_keys=[usuario_id], backref='retiradas_entregues')
    recebido_por = db.relationship('Usuario', foreign_keys=[recebido_por_id], backref='devolucoes_recebidas')
    
    def tempo_uso(self):
        if self.data_devolucao:
            delta = self.data_devolucao - self.data_retirada
            horas = delta.seconds // 3600
            minutos = (delta.seconds % 3600) // 60
            return f"{horas:02d}:{minutos:02d}"
        return "Em uso"
    
    def to_dict(self):
        return {
            'id': self.id,
            'tablet_id': self.tablet_id,
            'tablet_numero': self.tablet.numero,
            'tablet_modelo': self.tablet.modelo,
            'usuario': self.usuario_nome,  # Para compatibilidade com front-end
            'usuario_nome': self.usuario_nome,
            'entregue_por': self.entregue_por.nome if self.entregue_por else self.liberado_por,
            'liberado_por': self.liberado_por,
            'recebido_por': self.recebido_por.nome if self.recebido_por else None,
            'data_retirada': self.data_retirada.strftime('%d/%m/%Y %H:%M'),
            'data_devolucao': self.data_devolucao.strftime('%d/%m/%Y %H:%M') if self.data_devolucao else None,
            'tempo_uso': self.tempo_uso(),
            'checklist_retirada': {
                'estado': self.checklist_retirada_estado,
                'rede': self.checklist_retirada_rede,
                'carga': self.checklist_retirada_carga
            },
            'checklist_devolucao': {
                'estado': self.checklist_devolucao_estado
            },
            'foto_retirada': self.foto_retirada,
            'foto_devolucao': self.foto_devolucao,
            'fotos': [foto.to_dict() for foto in self.fotos]
        }


class FotosHistorico(db.Model):
    __tablename__ = 'fotos_historico'
    
    id = db.Column(db.Integer, primary_key=True)
    historico_id = db.Column(db.Integer, db.ForeignKey('historicos.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    categoria = db.Column(db.String(30), nullable=False, default='geral')
    caminho = db.Column(db.String(500), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.now)
    observacao = db.Column(db.String(200), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'caminho': self.caminho,
            'data_upload': self.data_upload.strftime('%d/%m/%Y %H:%M'),
            'observacao': self.observacao
        }


# ==================== NOVAS TABELAS - AUTENTICAÇÃO ====================

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)  # Será hashada
    cargo = db.Column(db.String(50), default='operador')  # 'admin' ou 'operador'
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    ultimo_login = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos (definidos nas outras classes)
    logs = db.relationship('LogSistema', backref='usuario', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'cargo': self.cargo,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.strftime('%d/%m/%Y %H:%M'),
            'ultimo_login': self.ultimo_login.strftime('%d/%m/%Y %H:%M') if self.ultimo_login else None
        }
    
    def to_dict_admin(self):
        """Retorna mais informações para o admin"""
        data = self.to_dict()
        data.update({
            'total_retiradas': len(self.retiradas_entregues),
            'total_devolucoes': len(self.devolucoes_recebidas)
        })
        return data


class LogSistema(db.Model):
    __tablename__ = 'logs_sistema'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    acao = db.Column(db.String(100), nullable=False)  # 'retirada', 'devolucao', 'login', 'logout', 'cadastro_tablet', etc.
    descricao = db.Column(db.Text, nullable=False)
    tablet_id = db.Column(db.Integer, db.ForeignKey('tablets.id'), nullable=True)
    data = db.Column(db.DateTime, default=datetime.now)
    ip = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario': self.usuario.nome if self.usuario else 'Sistema',
            'usuario_email': self.usuario.email if self.usuario else None,
            'acao': self.acao,
            'descricao': self.descricao,
            'tablet': self.tablet.numero if self.tablet else None,
            'data': self.data.strftime('%d/%m/%Y %H:%M:%S'),
            'ip': self.ip
        }