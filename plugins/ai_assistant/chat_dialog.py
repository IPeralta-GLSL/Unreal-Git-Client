import os
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QProgressBar, 
                             QWidget, QScrollArea, QFrame, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QTextCursor
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import get_translation_manager

# Try to import llama_cpp
LLAMA_IMPORT_ERROR = None
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except Exception as e:
    LLAMA_AVAILABLE = False
    LLAMA_IMPORT_ERROR = str(e)

class ModelThread(QThread):
    response_ready = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, model_path, prompt, history):
        super().__init__()
        self.model_path = model_path
        self.prompt = prompt
        self.history = history
        self.llm = None
        
    def run(self):
        if not LLAMA_AVAILABLE:
            self.error.emit(f"llama-cpp-python failed to load. Details: {LLAMA_IMPORT_ERROR}")
            return

        if not os.path.exists(self.model_path):
            self.error.emit(f"Model not found at {self.model_path}. Please download TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf and place it in the 'models' folder.")
            return

        try:
            # Initialize model if not already initialized (in a real app, we might want to keep the model loaded)
            # For this example, we'll load it every time or we need a way to persist it. 
            # Better: The Dialog should hold the model instance.
            pass 
        except Exception as e:
            self.error.emit(str(e))

class Worker(QThread):
    text_received = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, llm, messages):
        super().__init__()
        self.llm = llm
        self.messages = messages
        
    def run(self):
        try:
            stream = self.llm.create_chat_completion(
                messages=self.messages,
                stream=True,
                max_tokens=1024,
                temperature=0.1
            )
            
            for output in stream:
                if "content" in output["choices"][0]["delta"]:
                    text = output["choices"][0]["delta"]["content"]
                    self.text_received.emit(text)
            
            self.finished.emit()
        except Exception as e:
            self.text_received.emit(f"\nError: {str(e)}")
            self.finished.emit()

class ChatWidget(QWidget):
    def __init__(self, repo_path, parent=None):
        super().__init__(parent)
        self.repo_path = repo_path
        self.icon_manager = IconManager()
        self.llm = None
        
        # Load documentation from application root
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        docs_path = os.path.join(app_root, "INSTRUCTIONS.md")
        
        doc_context = ""
        if os.path.exists(docs_path):
            try:
                with open(docs_path, "r", encoding="utf-8") as f:
                    doc_context += f.read() + "\n\n"
            except:
                pass

        # Simplified Prompting for stability
        self.messages = [
            {"role": "system", "content": f"""You are the AI Assistant for the 'Git Client' application.
Use the following documentation to answer user questions:

{doc_context}

Instructions:
- Answer concisely.
- If the user speaks Spanish, answer in Spanish.
- If the user speaks English, answer in English.
- Do not invent information.
"""},
            {"role": "user", "content": "Who are you?"},
            {"role": "assistant", "content": "I am the Git Client AI assistant. I help with Git operations and Unreal Engine workflows."}
        ]
        
        self.setup_ui()
        self.init_model()
        
    def setup_ui(self):
        theme = get_current_theme()
        self.setStyleSheet(f"background-color: {theme.colors['background']}; color: {theme.colors['text']};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QFrame()
        header.setStyleSheet(f"background-color: {theme.colors['surface']}; border-bottom: 1px solid {theme.colors['border']};")
        header_layout = QHBoxLayout(header)
        
        title = QLabel("AI Assistant")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        layout.addWidget(header)
        
        # Chat Area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.colors['background']};
                border: none;
                padding: 10px;
                font-size: 14px;
            }}
        """)
        layout.addWidget(self.chat_area, 1)
        
        # Status bar for model loading (Moved above input)
        self.status_bar = QLabel("Initializing...")
        self.status_bar.setStyleSheet(f"padding: 2px 10px; color: {theme.colors['text_secondary']}; font-size: 11px; background-color: {theme.colors['surface']};")
        layout.addWidget(self.status_bar)

        # Input Area
        input_container = QFrame()
        input_container.setStyleSheet(f"background-color: {theme.colors['surface']}; border-top: 1px solid {theme.colors['border']};")
        input_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Ask something...")
        self.input_field.setFixedHeight(50)
        self.input_field.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.colors['background_elevated']};
                border: 1px solid {theme.colors['border']};
                border-radius: 5px;
                padding: 8px;
                color: {theme.colors['text']};
            }}
            QTextEdit:focus {{
                border-color: {theme.colors['primary']};
            }}
        """)
        input_layout.addWidget(self.input_field)
        
        self.send_btn = QPushButton()
        self.send_btn.setIcon(self.icon_manager.get_icon("send", size=20))
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors['primary']};
                border-radius: 20px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {theme.colors['primary_hover']};
            }}
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        layout.addWidget(input_container)

    def init_model(self):
        if not LLAMA_AVAILABLE:
            self.append_message("System", f"Error: llama-cpp-python failed to load.\nDetails: {LLAMA_IMPORT_ERROR}\nPlease run: pip install llama-cpp-python")
            self.status_bar.setText("Missing dependencies")
            self.input_field.setEnabled(False)
            self.send_btn.setEnabled(False)
            return

        # Recommended model: Qwen 1.5 4B (or Phi-3)
        model_name = "qwen1_5-4b-chat-q3_k_m.gguf"
        
        # Check common locations
        possible_paths = [
            os.path.join(os.getcwd(), "models", model_name),
            os.path.join(os.getcwd(), "models", "Phi-3-mini-4k-instruct.Q4_K_M.gguf"),
            os.path.join(os.getcwd(), "models", "phi-3-mini-4k-instruct.Q4_K_M.gguf"),
            os.path.join(os.path.dirname(__file__), "models", model_name),
        ]
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path:
            self.append_message("System", f"Model not found.\nPlease download '{model_name}' (or Phi-3) and place it in the 'models' folder.")
            self.append_message("System", "You can find it on HuggingFace (TheBloke or Microsoft).")
            self.status_bar.setText("Model not found")
            self.input_field.setEnabled(False)
            self.send_btn.setEnabled(False)
            return

        self.status_bar.setText(f"Loading model: {os.path.basename(model_path)}...")
        
        # Load model in a separate thread to not freeze UI? 
        # Llama initialization can take a few seconds.
        # For simplicity in this snippet, I'll do it here but ideally it should be threaded.
        # Since QThread cannot easily return the object, we'll just do it and hope it's fast enough for 1.1B model.
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
            self.status_bar.setText("Ready")
            
            # Initial greeting based on app language
            tm = get_translation_manager()
            lang = tm.get_current_language()
            
            greeting = "Hello! I am the Git Client AI. How can I help you?"
            if lang == 'es':
                greeting = "¡Hola! Soy la IA de Git Client. ¿En qué puedo ayudarte?"
                
            self.append_message("Assistant", greeting)
        except Exception as e:
            self.status_bar.setText("Error loading model")
            self.append_message("System", f"Error loading model: {str(e)}")

    def send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        
        self.append_message("You", text)
        self.input_field.clear()
        self.messages.append({"role": "user", "content": text})
        
        self.status_bar.setText("Thinking...")
        
        self.worker = Worker(self.llm, self.messages)
        self.worker.text_received.connect(self.on_text_received)
        self.worker.finished.connect(self.on_generation_finished)
        
        # Prepare UI for streaming response
        self.current_response = ""
        self.chat_area.append(f"<b>Assistant:</b> ")
        self.worker.start()
        
    def on_text_received(self, text):
        self.current_response += text
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.chat_area.setTextCursor(cursor)
        self.chat_area.ensureCursorVisible()
        
    def on_generation_finished(self):
        self.messages.append({"role": "assistant", "content": self.current_response})
        self.status_bar.setText("Ready")
        self.chat_area.append("") # New line
        
    def append_message(self, sender, text):
        color = "#4ade80" if sender == "You" else "#60a5fa"
        if sender == "System": color = "#ef4444"
        
        self.chat_area.append(f"<b style='color:{color}'>{sender}:</b> {text}")
        self.chat_area.append("")
