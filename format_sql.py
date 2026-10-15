'
' Formata scripts SQL dos dialetos MS SQL Server, Oracle, MySQL e SQLite3
'
' Criado por Danilo Almeida com auxílio de IA (Gemini)
'
' Licença: MIT
'

import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
import sqlglot
import sqlglot.expressions as exp
from sqlglot.errors import ParseError
import threading
import time
import re

def is_likely_sql(text):
    keywords = r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|WITH|MERGE)\b'
    return bool(re.search(keywords, text, re.IGNORECASE))

def annotate_insert_values(ast_node):
    """
    Navega pela estrutura do SQL e injeta o nome da coluna como 
    comentário no respectivo valor da cláusula VALUES.
    """
    # Procura todos os comandos de INSERT na árvore do código
    for insert_node in ast_node.find_all(exp.Insert):
        
        # 1. Extrai o esquema (Tabela e Colunas listadas)
        schema = insert_node.args.get("this")
        if not isinstance(schema, exp.Schema):
            continue # Se não especificou colunas (ex: INSERT INTO tab VALUES (...)), pula.
            
        columns = [col.name for col in schema.expressions]
        if not columns:
            continue
            
        # 2. Extrai a cláusula VALUES
        values_clause = insert_node.args.get("expression")
        if not isinstance(values_clause, exp.Values):
            continue
            
        # 3. Mapeia e injeta os comentários em cada tupla de valores
        for tuple_node in values_clause.expressions:
            if isinstance(tuple_node, exp.Tuple):
                for i, val_node in enumerate(tuple_node.expressions):
                    if i < len(columns):
                        col_name = columns[i]
                        # Inicializa a lista de comentários se não existir
                        if val_node.comments is None:
                            val_node.comments = []
                        # Adiciona o comentário se já não estiver lá
                        if col_name not in val_node.comments:
                            val_node.comments.append(col_name)
                            
    return ast_node

def detect_and_format_sql(text):
    dialects = ['tsql', 'oracle', 'mysql', 'sqlite']
    
    for dialect in dialects:
        try:
            # 1. Tenta realizar o parse do texto para a estrutura de dados (AST)
            ast_list = sqlglot.parse(text, read=dialect)
            
            # Rejeita se o parse não retornou nada válido
            if not ast_list or any(node is None for node in ast_list):
                continue
            
            formatted_statements = []
            
            # 2. Processa cada comando SQL (separados por ponto e vírgula)
            for ast in ast_list:
                # Aplica a nossa inteligência de injetar comentários
                ast = annotate_insert_values(ast)
                
                # Gera a string final formatada
                formatted_sql = ast.sql(dialect=dialect, pretty=True)
                formatted_statements.append(formatted_sql)
                
            # 3. Remonta o arquivo
            final_sql = ";\n\n".join(formatted_statements)
            
            if not final_sql.endswith(';'):
                final_sql += ";"
                
            return True, final_sql
            
        except ParseError:
            continue
            
    return False, None

def process_clipboard(root, progress_window):
    try:
        text = pyperclip.paste().strip()
        time.sleep(0.5) 

        if not text or not is_likely_sql(text):
            root.after(0, show_error, root, progress_window, "O conteúdo atual da área de transferência não parece ser um código SQL válido.")
            return
            
        success, formatted_sql = detect_and_format_sql(text)
        time.sleep(0.5) 
        
        if success:
            pyperclip.copy(formatted_sql)
            root.after(0, root.destroy)
        else:
            root.after(0, show_error, root, progress_window, "Erro de sintaxe. Não foi possível formatar o código SQL em nenhum dos dialetos suportados.")
            
    except Exception as e:
        root.after(0, show_error, root, progress_window, f"Ocorreu um erro inesperado: {str(e)}")

def show_error(root, progress_window, message):
    progress_window.destroy()
    messagebox.showinfo("Formatador SQL", message)
    root.destroy()

def main():
    root = tk.Tk()
    root.withdraw()
    
    progress_window = tk.Toplevel(root)
    progress_window.title("Formatando SQL...")
    progress_window.geometry("300x80")
    progress_window.resizable(False, False)
    
    progress_window.update_idletasks()
    width = progress_window.winfo_width()
    height = progress_window.winfo_height()
    x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
    y = (progress_window.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry(f'{width}x{height}+{x}+{y}')
    
    label = ttk.Label(progress_window, text="Analisando e formatando código...")
    label.pack(pady=(10, 5))
    
    progress = ttk.Progressbar(progress_window, mode='indeterminate', length=250)
    progress.pack(pady=(0, 10))
    progress.start(15) 
    
    threading.Thread(target=process_clipboard, args=(root, progress_window), daemon=True).start()
    
    root.mainloop()

if __name__ == "__main__":
    main()
