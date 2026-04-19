# database.py - Adicione a nova tabela FotosHistorico

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
            'usuario_atual': ultimo_uso.usuario if ultimo_uso else '',
            'hora_retirada': ultimo_uso.data_retirada.strftime('%H:%M') if ultimo_uso else '',
            'data_retirada': ultimo_uso.data_retirada.strftime('%d/%m/%Y %H:%M') if ultimo_uso else '',
            'ultimo_usuario': ultimo_registro.usuario if ultimo_registro and ultimo_registro.data_devolucao else '',
            'ultima_devolucao': ultimo_registro.data_devolucao.strftime('%d/%m/%Y %H:%M') if ultimo_registro and ultimo_registro.data_devolucao else ''
        }

class Historico(db.Model):
    __tablename__ = 'historicos'
    
    id = db.Column(db.Integer, primary_key=True)
    tablet_id = db.Column(db.Integer, db.ForeignKey('tablets.id'), nullable=False)
    usuario = db.Column(db.String(100), nullable=False)
    liberado_por = db.Column(db.String(100), nullable=False)
    data_retirada = db.Column(db.DateTime, default=datetime.now)
    data_devolucao = db.Column(db.DateTime, nullable=True)
    
    # Campos do questionário na retirada
    checklist_retirada_estado = db.Column(db.String(10), nullable=True)
    checklist_retirada_rede = db.Column(db.String(10), nullable=True)
    checklist_retirada_carga = db.Column(db.String(10), nullable=True)
    
    # Campos do questionário na devolução
    checklist_devolucao_estado = db.Column(db.String(10), nullable=True)
    
    # Campos antigos de foto única (manter para compatibilidade)
    foto_retirada = db.Column(db.String(500), nullable=True)
    foto_devolucao = db.Column(db.String(500), nullable=True)
    
    # Relacionamento com múltiplas fotos
    fotos = db.relationship('FotosHistorico', backref='historico', lazy=True, cascade='all, delete-orphan')
    
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
            'usuario': self.usuario,
            'liberado_por': self.liberado_por,
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
    tipo = db.Column(db.String(20), nullable=False)  # 'retirada' ou 'devolucao'
    categoria = db.Column(db.String(30), nullable=False, default='geral')  # 'geral', 'tela', 'avaria', etc.
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