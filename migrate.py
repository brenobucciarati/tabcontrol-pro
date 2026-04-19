# migrate_db.py
from app import app, db
import sqlite3

with app.app_context():
    conn = sqlite3.connect('instance/tabcontrol.db')
    cursor = conn.cursor()
    
    # 1. Adicionar colunas de foto na tabela historicos (se não existirem)
    cursor.execute("PRAGMA table_info(historicos)")
    colunas = [col[1] for col in cursor.fetchall()]
    
    if 'foto_retirada' not in colunas:
        print("📸 Adicionando coluna foto_retirada...")
        cursor.execute("ALTER TABLE historicos ADD COLUMN foto_retirada VARCHAR(500)")
    
    if 'foto_devolucao' not in colunas:
        print("📸 Adicionando coluna foto_devolucao...")
        cursor.execute("ALTER TABLE historicos ADD COLUMN foto_devolucao VARCHAR(500)")
    
    # 2. Verificar se a tabela fotos_historico já existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fotos_historico'")
    tabela_existe = cursor.fetchone()
    
    if not tabela_existe:
        print("📸 Criando tabela fotos_historico...")
        cursor.execute("""
            CREATE TABLE fotos_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                historico_id INTEGER NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                categoria VARCHAR(30) NOT NULL DEFAULT 'geral',
                caminho VARCHAR(500) NOT NULL,
                data_upload DATETIME DEFAULT CURRENT_TIMESTAMP,
                observacao VARCHAR(200),
                FOREIGN KEY(historico_id) REFERENCES historicos(id) ON DELETE CASCADE
            )
        """)
        print("✅ Tabela fotos_historico criada com sucesso!")
    else:
        print("ℹ️ Tabela fotos_historico já existe!")
    
    # 3. Verificar se a coluna tablet_modelo existe (para compatibilidade)
    cursor.execute("PRAGMA table_info(historicos)")
    colunas = [col[1] for col in cursor.fetchall()]
    
    conn.commit()
    conn.close()
    
    print("✅ Migração concluída com sucesso!")
    print("📋 Resumo:")
    print("   - Coluna foto_retirada: OK")
    print("   - Coluna foto_devolucao: OK")
    print("   - Tabela fotos_historico: OK")
    print("\n🚀 Agora você pode reiniciar o Flask com: python app.py")