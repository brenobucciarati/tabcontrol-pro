# main.py
import customtkinter as ctk
from PIL import Image
import json
import os
from datetime import datetime
from tkinter import messagebox
import threading
import time

# Configuração do tema moderno
ctk.set_appearance_mode("dark")  # Modo escuro moderno
ctk.set_default_color_theme("blue")

class TabletControlSystem:
    def __init__(self):
        self.janela = ctk.CTk()
        self.janela.title("TabControl - Sistema de Gerenciamento de Tablets")
        self.janela.geometry("1400x800")
        
        # Arquivo de dados
        self.arquivo_dados = "tablets.json"
        self.tablets = []
        self.cores_led = {
            "disponivel": "#2ecc71",  # Verde
            "em_uso": "#e74c3c",       # Vermelho
            "off": "#7f8c8d"           # Cinza
        }
        
        # Inicializa o sistema
        self.inicializar_sistema()
        self.criar_interface()
        
    def inicializar_sistema(self):
        """Inicializa o sistema com dados padrão se necessário"""
        try:
            self.carregar_dados()
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            # Se houver erro, cria dados iniciais
            self.criar_dados_iniciais()
            self.salvar_dados()
    
    def criar_dados_iniciais(self):
        """Cria dados iniciais para 40 tablets"""
        self.tablets = []
        modelos = ["iPad Pro", "Samsung Tab S9", "Lenovo Tab P12", "Xiaomi Pad 6", "Amazon Fire HD"]
        
        for i in range(1, 27):
            # Escolhe um modelo baseado no índice
            modelo_index = (i - 1) % len(modelos)
            
            self.tablets.append({
                "id": i,
                "numero": f"{i:02d}",
                "status": "disponivel",
                "usuario": "",
                "hora_retirada": "",
                "modelo": modelos[modelo_index],
                "cor": self.gerar_cor_modelo(i)
            })
    
    def gerar_cor_modelo(self, i):
        """Gera cores diferentes para os modelos"""
        cores_modelo = ["#3498db", "#9b59b6", "#e67e22", "#1abc9c", "#e84342", "#f1c40f", "#2c3e50", "#d35400"]
        return cores_modelo[i % len(cores_modelo)]
    
    def carregar_dados(self):
        """Carrega os tablets do arquivo JSON"""
        if os.path.exists(self.arquivo_dados):
            # Verifica se o arquivo não está vazio
            if os.path.getsize(self.arquivo_dados) > 0:
                with open(self.arquivo_dados, 'r', encoding='utf-8') as f:
                    self.tablets = json.load(f)
            else:
                # Arquivo vazio, cria dados iniciais
                self.criar_dados_iniciais()
        else:
            # Arquivo não existe, cria dados iniciais
            self.criar_dados_iniciais()
    
    def salvar_dados(self):
        """Salva os dados no arquivo JSON"""
        try:
            with open(self.arquivo_dados, 'w', encoding='utf-8') as f:
                json.dump(self.tablets, f, indent=4, ensure_ascii=False, default=str)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar dados: {e}")
    
    def criar_interface(self):
        """Cria a interface principal"""
        
        # Frame superior com título e estatísticas
        frame_topo = ctk.CTkFrame(self.janela, height=100, corner_radius=0)
        frame_topo.pack(fill="x", padx=10, pady=(10, 5))
        
        titulo = ctk.CTkLabel(frame_topo, text="📱 TabControl - Painel de Tablets", 
                              font=ctk.CTkFont(size=28, weight="bold"))
        titulo.pack(side="left", padx=20, pady=20)
        
        # Frame de estatísticas
        self.frame_stats = ctk.CTkFrame(frame_topo)
        self.frame_stats.pack(side="right", padx=20, pady=10)
        
        # Frame de botões de ação
        frame_acoes = ctk.CTkFrame(self.janela, height=60)
        frame_acoes.pack(fill="x", padx=10, pady=5)
        
        btn_novo = ctk.CTkButton(frame_acoes, text="➕ Adicionar Novo Tablet", 
                                  command=self.janela_cadastro_tablet,
                                  font=ctk.CTkFont(size=14, weight="bold"),
                                  height=40, width=200)
        btn_novo.pack(side="left", padx=10, pady=10)
        
        btn_atualizar = ctk.CTkButton(frame_acoes, text="🔄 Atualizar", 
                                       command=self.atualizar_grid,
                                       font=ctk.CTkFont(size=14),
                                       height=40, width=150,
                                       fg_color="#2c3e50", hover_color="#34495e")
        btn_atualizar.pack(side="left", padx=5, pady=10)
        
        btn_limpar = ctk.CTkButton(frame_acoes, text="🗑️ Limpar Todos", 
                                    command=self.limpar_todos_tablets,
                                    font=ctk.CTkFont(size=14),
                                    height=40, width=150,
                                    fg_color="#c0392b", hover_color="#e74c3c")
        btn_limpar.pack(side="left", padx=5, pady=10)
        
        # Frame principal com scroll (grid de tablets)
        self.frame_grid = ctk.CTkScrollableFrame(self.janela, label_text="📋 Tablets Disponíveis/Em Uso")
        self.frame_grid.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Atualiza estatísticas
        self.atualizar_estatisticas()
        
        # Inicia a atualização automática
        self.atualizar_grid()
        self.iniciar_atualizacao_automatica()
    
    def atualizar_estatisticas(self):
        """Atualiza o contador de estatísticas"""
        # Limpa frame
        for widget in self.frame_stats.winfo_children():
            widget.destroy()
        
        disponiveis = sum(1 for t in self.tablets if t["status"] == "disponivel")
        em_uso = sum(1 for t in self.tablets if t["status"] == "em_uso")
        
        label_disponiveis = ctk.CTkLabel(self.frame_stats, 
                                         text=f"✅ Disponíveis: {disponiveis}", 
                                         font=ctk.CTkFont(size=14, weight="bold"),
                                         text_color="#2ecc71")
        label_disponiveis.pack(side="left", padx=15)
        
        label_em_uso = ctk.CTkLabel(self.frame_stats, 
                                    text=f"🔴 Em Uso: {em_uso}", 
                                    font=ctk.CTkFont(size=14, weight="bold"),
                                    text_color="#e74c3c")
        label_em_uso.pack(side="left", padx=15)
        
        label_total = ctk.CTkLabel(self.frame_stats, 
                                   text=f"📊 Total: {len(self.tablets)}", 
                                   font=ctk.CTkFont(size=14, weight="bold"))
        label_total.pack(side="left", padx=15)
    
    def atualizar_grid(self):
        """Atualiza a grade de tablets"""
        try:
            # Limpa o grid atual
            for widget in self.frame_grid.winfo_children():
                widget.destroy()
            
            # Ordena tablets por número
            self.tablets.sort(key=lambda x: int(x["numero"]))
            
            # Configura grid com 5 colunas
            colunas = 5
            for i, tablet in enumerate(self.tablets):
                linha = i // colunas
                coluna = i % colunas
                
                self.criar_card_tablet(tablet, linha, coluna)
            
            # Atualiza estatísticas
            self.atualizar_estatisticas()
            
        except Exception as e:
            print(f"Erro ao atualizar grid: {e}")
    
    def criar_card_tablet(self, tablet, linha, coluna):
        """Cria um card para cada tablet"""
        try:
            # Frame do card
            card = ctk.CTkFrame(self.frame_grid, width=220, height=300, corner_radius=15)
            card.grid(row=linha, column=coluna, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)
            
            # Indicador LED (círculo colorido)
            led_color = self.cores_led[tablet["status"]]
            
            # Círculo LED
            canvas_led = ctk.CTkCanvas(card, width=20, height=20, bg=card.cget("fg_color"), highlightthickness=0)
            canvas_led.place(relx=0.85, rely=0.05)
            canvas_led.create_oval(2, 2, 18, 18, fill=led_color, outline="white", width=1)
            
            # Número do tablet em destaque
            label_numero = ctk.CTkLabel(card, text=tablet["numero"], 
                                        font=ctk.CTkFont(size=36, weight="bold"),
                                        text_color="white")
            label_numero.place(relx=0.5, rely=0.15, anchor="center")
            
            # Ícone do tablet (representação visual)
            frame_tablet = ctk.CTkFrame(card, width=140, height=100, 
                                        fg_color=tablet["cor"], corner_radius=10)
            frame_tablet.place(relx=0.5, rely=0.4, anchor="center")
            
            # "Tela" do tablet (efeito visual)
            tela = ctk.CTkFrame(frame_tablet, width=120, height=70, 
                               fg_color="#ecf0f1", corner_radius=5)
            tela.place(relx=0.5, rely=0.5, anchor="center")
            
            # Informações do tablet
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.place(relx=0.5, rely=0.7, anchor="center", width=200)
            
            # Modelo
            label_modelo = ctk.CTkLabel(info_frame, text=f"📱 {tablet['modelo']}", 
                                        font=ctk.CTkFont(size=11))
            label_modelo.pack(pady=2)
            
            if tablet["status"] == "em_uso":
                # Mostra informações de uso
                label_usuario = ctk.CTkLabel(info_frame, 
                                            text=f"👤 {tablet['usuario'][:15]}...",  # Limita tamanho
                                            font=ctk.CTkFont(size=11, weight="bold"))
                label_usuario.pack(pady=2)
                
                label_hora = ctk.CTkLabel(info_frame, 
                                         text=f"⏰ {tablet['hora_retirada']}",
                                         font=ctk.CTkFont(size=10))
                label_hora.pack(pady=2)
                
                # Calcula tempo de uso
                try:
                    hora_retirada = datetime.strptime(tablet['hora_retirada'], "%H:%M")
                    agora = datetime.now()
                    
                    # Ajusta para o mesmo dia
                    hora_retirada = hora_retirada.replace(
                        year=agora.year, 
                        month=agora.month, 
                        day=agora.day
                    )
                    
                    # Se a hora de retirada for maior que agora, assume que foi no dia anterior
                    if hora_retirada > agora:
                        hora_retirada = hora_retirada.replace(day=agora.day - 1)
                    
                    diff = agora - hora_retirada
                    horas = diff.seconds // 3600
                    minutos = (diff.seconds % 3600) // 60
                    
                    label_tempo = ctk.CTkLabel(info_frame, 
                                              text=f"⏱️ {horas:02d}:{minutos:02d} h",
                                              font=ctk.CTkFont(size=10),
                                              text_color="#f39c12")
                    label_tempo.pack(pady=2)
                except Exception as e:
                    label_tempo = ctk.CTkLabel(info_frame, 
                                              text="⏱️ 00:00 h",
                                              font=ctk.CTkFont(size=10),
                                              text_color="#f39c12")
                    label_tempo.pack(pady=2)
                
                # Botão de devolução
                btn_devolver = ctk.CTkButton(info_frame, text="Devolver", 
                                             command=lambda t=tablet: self.devolver_tablet(t),
                                             fg_color="#e74c3c", hover_color="#c0392b",
                                             height=28, width=100)
                btn_devolver.pack(pady=5)
                
            else:
                # Mostra disponível
                label_disponivel = ctk.CTkLabel(info_frame, text="✅ Disponível", 
                                               font=ctk.CTkFont(size=11, weight="bold"),
                                               text_color="#2ecc71")
                label_disponivel.pack(pady=2)
                
                # Campo para nome do usuário
                entry_usuario = ctk.CTkEntry(info_frame, placeholder_text="Nome ou Matrícula",
                                             height=28, width=150)
                entry_usuario.pack(pady=2)
                
                # Botão de retirada
                btn_pegar = ctk.CTkButton(info_frame, text="Pegar Tablet", 
                                          command=lambda t=tablet, e=entry_usuario: self.pegar_tablet(t, e),
                                          fg_color="#27ae60", hover_color="#229954",
                                          height=28, width=120)
                btn_pegar.pack(pady=5)
            
            # Indicador de status (texto no topo)
            status_text = "EM USO" if tablet["status"] == "em_uso" else "DISPONÍVEL"
            label_status = ctk.CTkLabel(card, text=status_text,
                                        font=ctk.CTkFont(size=9, weight="bold"),
                                        text_color=led_color)
            label_status.place(relx=0.5, rely=0.02, anchor="n")
            
        except Exception as e:
            print(f"Erro ao criar card: {e}")
    
    def pegar_tablet(self, tablet, entry_usuario):
        """Registra a retirada de um tablet"""
        try:
            usuario = entry_usuario.get().strip()
            
            if not usuario:
                messagebox.showwarning("Atenção", "Digite o nome ou matrícula do colaborador!")
                return
            
            # Atualiza dados do tablet
            tablet["status"] = "em_uso"
            tablet["usuario"] = usuario
            tablet["hora_retirada"] = datetime.now().strftime("%H:%M")
            
            self.salvar_dados()
            self.atualizar_grid()
            messagebox.showinfo("Sucesso", f"Tablet {tablet['numero']} retirado por {usuario}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao pegar tablet: {e}")
    
    def devolver_tablet(self, tablet):
        """Registra a devolução de um tablet"""
        try:
            if messagebox.askyesno("Confirmar", f"Confirmar devolução do Tablet {tablet['numero']}?"):
                # Registra tempo de uso
                try:
                    hora_retirada = datetime.strptime(tablet['hora_retirada'], "%H:%M")
                    agora = datetime.now()
                    
                    # Ajusta para o mesmo dia
                    hora_retirada = hora_retirada.replace(
                        year=agora.year, 
                        month=agora.month, 
                        day=agora.day
                    )
                    
                    if hora_retirada > agora:
                        hora_retirada = hora_retirada.replace(day=agora.day - 1)
                    
                    diff = agora - hora_retirada
                    horas = diff.seconds // 3600
                    minutos = (diff.seconds % 3600) // 60
                    
                    messagebox.showinfo("Tempo de Uso", 
                                       f"Tablet {tablet['numero']} usado por {horas}h{minutos}min")
                except Exception as e:
                    print(f"Erro ao calcular tempo: {e}")
                
                # Atualiza dados
                tablet["status"] = "disponivel"
                tablet["usuario"] = ""
                tablet["hora_retirada"] = ""
                
                self.salvar_dados()
                self.atualizar_grid()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao devolver tablet: {e}")
    
    def limpar_todos_tablets(self):
        """Limpa todos os tablets (devolve todos)"""
        if messagebox.askyesno("Confirmar", "Deseja realmente devolver TODOS os tablets?", icon="warning"):
            try:
                for tablet in self.tablets:
                    tablet["status"] = "disponivel"
                    tablet["usuario"] = ""
                    tablet["hora_retirada"] = ""
                
                self.salvar_dados()
                self.atualizar_grid()
                messagebox.showinfo("Sucesso", "Todos os tablets foram devolvidos!")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao limpar tablets: {e}")
    
    def janela_cadastro_tablet(self):
        """Abre janela para cadastrar novo tablet"""
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Cadastrar Novo Tablet")
        janela.geometry("400x350")
        janela.grab_set()  # Modal
        
        # Centraliza a janela
        janela.transient(self.janela)
        
        # Frame principal
        frame = ctk.CTkFrame(janela)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(frame, text="➕ Adicionar Novo Tablet", 
                              font=ctk.CTkFont(size=20, weight="bold"))
        titulo.pack(pady=10)
        
        # Campo número
        label_num = ctk.CTkLabel(frame, text="Número do Tablet:")
        label_num.pack(pady=(10, 0))
        
        # Próximo número disponível
        numeros_existentes = [int(t["numero"]) for t in self.tablets]
        proximo_num = max(numeros_existentes) + 1 if numeros_existentes else 1
        
        entry_num = ctk.CTkEntry(frame, placeholder_text="Ex: 27")
        entry_num.insert(0, str(proximo_num))
        entry_num.pack(pady=5)
        
        # Campo modelo
        label_modelo = ctk.CTkLabel(frame, text="Modelo:")
        label_modelo.pack(pady=(10, 0))
        
        modelos = ["iPad Pro", "Samsung Tab S9", "Lenovo Tab P12", "Xiaomi Pad 6", "Amazon Fire HD", "Outro"]
        combo_modelo = ctk.CTkComboBox(frame, values=modelos, width=200)
        combo_modelo.set("iPad Pro")
        combo_modelo.pack(pady=5)
        
        # Campo para modelo personalizado (aparece se selecionar "Outro")
        entry_modelo_personalizado = ctk.CTkEntry(frame, placeholder_text="Digite o modelo", width=200)
        
        def on_modelo_change(choice):
            if choice == "Outro":
                entry_modelo_personalizado.pack(pady=5)
            else:
                entry_modelo_personalizado.pack_forget()
        
        combo_modelo.configure(command=on_modelo_change)
        
        # Botão salvar
        btn_salvar = ctk.CTkButton(frame, text="Salvar Tablet", 
                                   command=lambda: self.salvar_novo_tablet(
                                       entry_num.get(), 
                                       combo_modelo.get() if combo_modelo.get() != "Outro" else entry_modelo_personalizado.get(),
                                       janela
                                   ),
                                   height=40, width=150)
        btn_salvar.pack(pady=20)
    
    def salvar_novo_tablet(self, numero, modelo, janela):
        """Salva um novo tablet no sistema"""
        if not numero or not modelo:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return
        
        try:
            # Verifica se número já existe
            for t in self.tablets:
                if t["numero"] == numero.zfill(2):
                    messagebox.showerror("Erro", f"Tablet {numero} já existe!")
                    return
            
            # Cria novo tablet
            novo_id = len(self.tablets) + 1
            novo_tablet = {
                "id": novo_id,
                "numero": numero.zfill(2),
                "status": "disponivel",
                "usuario": "",
                "hora_retirada": "",
                "modelo": modelo,
                "cor": self.gerar_cor_modelo(novo_id)
            }
            
            self.tablets.append(novo_tablet)
            self.salvar_dados()
            self.atualizar_grid()
            
            janela.destroy()
            messagebox.showinfo("Sucesso", f"Tablet {numero} cadastrado com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao cadastrar tablet: {e}")
    
    def iniciar_atualizacao_automatica(self):
        """Inicia thread para atualização automática (tempo real)"""
        def atualizar():
            while True:
                try:
                    time.sleep(5)  # Atualiza a cada 5 segundos
                    self.janela.after(0, self.atualizar_grid)
                except:
                    break
        
        thread = threading.Thread(target=atualizar, daemon=True)
        thread.start()
    
    def executar(self):
        """Inicia o programa"""
        try:
            self.janela.mainloop()
        except KeyboardInterrupt:
            print("Programa encerrado pelo usuário")
        except Exception as e:
            print(f"Erro na execução: {e}")
            messagebox.showerror("Erro", f"Erro na execução: {e}")

# Ponto de entrada
if __name__ == "__main__":
    # Verifica e instala dependências
    try:
        import customtkinter
        from PIL import Image
    except ImportError as e:
        print("Instalando dependências necessárias...")
        os.system("pip install customtkinter pillow")
        import customtkinter
        from PIL import Image
    
    # Executa o programa
    try:
        app = TabletControlSystem()
        app.executar()
    except Exception as e:
        print(f"Erro fatal: {e}")
        messagebox.showerror("Erro Fatal", f"Ocorreu um erro: {e}\n\nO programa será fechado.")