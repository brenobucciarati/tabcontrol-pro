# reset_db.py
import os
from flask import Flask
from database1 import db, Tablet

# Caminho do banco de dados
db_path = 'instance/tabcontrol.db'

# Remove o banco antigo
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"✅ Banco de dados antigo removido: {db_path}")

# Cria aplicação Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tabcontrol.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    print("✅ Novas tabelas criadas!")
    
    # Criar tablets conforme especificação
    tablets_data = []
    
    # Tablets 01-03: Samsung Tab A9
    for i in range(1, 4):
        tablets_data.append({
            'numero': f"{i:02d}",
            'modelo': 'Samsung Tab A9',
            'cor': '#4158D0',
            'imagem': 'default.png'
        })
        print(f"   Criado: Tablet {i:02d} - Samsung Tab A9")
    
    # Tablets 04-05: Samsung Tab A9+
    for i in range(4, 6):
        tablets_data.append({
            'numero': f"{i:02d}",
            'modelo': 'Samsung Tab A9+',
            'cor': '#C850C0',
            'imagem': 'default.png'
        })
        print(f"   Criado: Tablet {i:02d} - Samsung Tab A9+")
    
    # Tablets 06-26: Lenovo Tab (21 tablets)
    for i in range(6, 41):
        tablets_data.append({
            'numero': f"{i:02d}",
            'modelo': 'Lenovo Tab',
            'cor': '#00ff88',
            'imagem': 'default.png'
        })
        print(f"   Criado: Tablet {i:02d} - Lenovo Tab")
    
    # Inserir no banco
    for data in tablets_data:
        tablet = Tablet(**data)
        db.session.add(tablet)
    
    db.session.commit()
    
    # Verificação
    total = Tablet.query.count()
    print(f"\n📊 Total de tablets criados: {total}")
    
    # Estatísticas por modelo
    samsung_a9 = Tablet.query.filter_by(modelo='Samsung Tab A9').count()
    samsung_a9_plus = Tablet.query.filter_by(modelo='Samsung Tab A9+').count()
    lenovo = Tablet.query.filter_by(modelo='Lenovo Tab').count()
    
    print(f"\n📈 Distribuição:")
    print(f"   Samsung Tab A9: {samsung_a9}")
    print(f"   Samsung Tab A9+: {samsung_a9_plus}")
    print(f"   Lenovo Tab: {lenovo}")
    
print("\n✨ Banco de dados recriado com sucesso!")
print("🚀 Execute: python app.py")