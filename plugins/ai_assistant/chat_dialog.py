import os
import sys
import json
import re
import subprocess
import time
from pathlib import Path
import requests
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QProgressBar, 
                             QWidget, QScrollArea, QFrame, QMessageBox, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QEvent
from PyQt6.QtGui import QFont, QIcon, QTextCursor
from ui.theme import get_current_theme
from ui.icon_manager import IconManager
from core.translations import get_translation_manager
from PyQt6.QtWidgets import QApplication
from llama_cpp import llama_cpp

# Try to import llama_cpp
LLAMA_IMPORT_ERROR = None
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except Exception as e:
    LLAMA_AVAILABLE = False
    LLAMA_IMPORT_ERROR = str(e)

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0

            os.makedirs(os.path.dirname(self.dest_path), exist_ok=True)

            with open(self.dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            self.progress.emit(percent)
            
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))

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

        self._repo_context_index = None
        self._repo_context_cache = None
        self._repo_context_cache_time = 0.0
        
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

        repo_context = self._build_repo_context(include_size=False)

        app_name = self._get_application_name()
        repo_name, repo_remote = self._get_repo_info(repo_path)

        instructions = (
            "Use the following documentation to answer user questions:\n\n"
            f"{doc_context}\n\n"
            "Instructions:\n"
            "- Answer concisely.\n"
            "- If the user speaks Spanish, answer in Spanish.\n"
            "- If the user speaks English, answer in English.\n"
            "- Do not invent information.\n"
            "- If the question is about the currently opened repository, use the repository context provided.\n"
        )

        self._instructions = instructions

        system_intro = f"You are the AI Assistant for the '{app_name}' application. Current repository: {repo_name} ({repo_remote or 'no remote'})"

        self.messages = [
            {"role": "system", "content": system_intro + "\n\n" + instructions},
            {"role": "system", "content": repo_context},
            {"role": "user", "content": "Who are you?"},
            {"role": "assistant", "content": f"I am the {app_name} AI assistant. I help with Git operations and Unreal Engine workflows. Working on repository: {repo_name}."}
        ]

        self._repo_context_index = 1
        
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
        self.input_field.installEventFilter(self)
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

        model_name = "qwen1_5-4b-chat-q3_k_m.gguf"
        
        config_dir = Path.home() / '.unreal-git-client'
        models_dir = config_dir / 'models'

        possible_paths = [
            str(models_dir / model_name),
            os.path.join(os.getcwd(), "models", model_name),
            os.path.join(os.path.dirname(__file__), "models", model_name),
        ]
        
        model_path = None
        for path in possible_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path:
            self.append_message("System", f"Model '{model_name}' not found.")
            self.status_bar.setText("Model not found")
            self.input_field.setEnabled(False)
            self.send_btn.setEnabled(False)
            
            self.download_btn = QPushButton("Download Model (2.6 GB)")
            self.download_btn.clicked.connect(lambda: self.download_model(model_name))
            self.layout().addWidget(self.download_btn)
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            self.layout().addWidget(self.progress_bar)
            return

        self.load_model(model_path)

    def download_model(self, model_name):
        url = "https://huggingface.co/Qwen/Qwen1.5-4B-Chat-GGUF/resolve/main/qwen1_5-4b-chat-q3_k_m.gguf?download=true"
        config_dir = Path.home() / '.unreal-git-client'
        models_dir = config_dir / 'models'
        dest_path = str(models_dir / model_name)
        
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.download_thread = DownloadThread(url, dest_path)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_progress(self, percent):
        self.progress_bar.setValue(percent)

    def on_download_finished(self, path):
        self.progress_bar.setVisible(False)
        self.download_btn.setVisible(False)
        self.append_message("System", "Download complete. Loading model...")
        self.load_model(path)

    def on_download_error(self, error):
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Retry Download")
        self.append_message("System", f"Download error: {error}")

    def load_model(self, model_path):
        self.status_bar.setText(f"Loading model: {os.path.basename(model_path)}...")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        try:
            def _supports_gpu_offload():
                try:
                    fn = getattr(llama_cpp, "llama_supports_gpu_offload", None)
                    if callable(fn):
                        return bool(fn())
                except Exception:
                    pass
                return False

            def _get_gpu_layers(llm_obj):
                for attr in ("context_params", "_context_params", "_params"):
                    obj = getattr(llm_obj, attr, None)
                    if obj is not None and hasattr(obj, "n_gpu_layers"):
                        try:
                            return int(getattr(obj, "n_gpu_layers"))
                        except Exception:
                            continue
                return None

            tried_gpu = False
            if _supports_gpu_offload():
                try_gpu = {
                    "model_path": model_path,
                    "n_ctx": 2048,
                    "n_threads": 4,
                    "verbose": False,
                    "n_gpu_layers": -1,
                    "main_gpu": 0,
                    "n_batch": 512,
                }
                try:
                    self.llm = Llama(**try_gpu)
                    tried_gpu = True
                except Exception:
                    tried_gpu = False

            if not tried_gpu:
                self.llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,
                    n_threads=4,
                    verbose=False
                )

            layers = _get_gpu_layers(self.llm)
            if layers and layers > 0:
                self.status_bar.setText(f"Ready (GPU layers: {layers})")
            else:
                self.status_bar.setText("Ready (CPU)")
            
            tm = get_translation_manager()
            lang = tm.get_current_language()
            app_name = self._get_application_name()
            greeting = f"Hello! I am the {app_name} AI. How can I help you?"
            if lang == 'es':
                greeting = f"¡Hola! Soy la IA de {app_name}. ¿En qué puedo ayudarte?"
            self.append_message("Assistant", greeting)
        except Exception as e:
            self.status_bar.setText("Error loading model")
            self.append_message("System", f"Error loading model: {str(e)}")

    def eventFilter(self, obj, event):
        if obj == self.input_field and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return
        lower = text.lower()

        # Handle a few direct repo queries by asking the LLM with repo metadata when available
        def try_llm_with_metadata(user_question: str) -> bool:
            meta = None
            try:
                meta = self._get_repo_metadata(self.repo_path)
            except Exception:
                meta = None

            if not LLAMA_AVAILABLE or not self.llm:
                return False

            system_msg = {
                "role": "system",
                "content": (
                    "You are an assistant that answers user questions using only the provided repository metadata. "
                    "Use the metadata to give a concise, factual answer. Do not invent information. "
                    "If the user speaks Spanish, answer in Spanish; otherwise answer in English.\n\n"
                    f"Repository metadata:\n{json.dumps(meta, ensure_ascii=False, indent=2)}"
                )
            }
            messages = [system_msg, {"role": "user", "content": user_question}]

            self._start_worker_with_messages(messages)
            return True

        if any(k in lower for k in ["como se llama", "cómo se llama", "nombre del repo", "como se llama este repo", "cómo se llama este repo"]):
            if try_llm_with_metadata(text):
                self.append_message("You", text)
                self.input_field.clear()
                return
            self.append_message("You", text)
            self.input_field.clear()
            self.append_message("Assistant", "No puedo responder: el modelo local no está cargado.")
            return

        if any(k in lower for k in ["pesa", "peso", "cuanto pesa", "cuánto pesa", "tamaño", "tamano"]):
            if try_llm_with_metadata(text):
                self.append_message("You", text)
                self.input_field.clear()
                return
            self.append_message("You", text)
            self.input_field.clear()
            self.append_message("Assistant", "No puedo responder: el modelo local no está cargado.")
            return

        if any(k in lower for k in ["version de unreal", "versión de unreal", "que version de unreal", "qué versión de unreal", "unreal version", "ue version"]):
            if try_llm_with_metadata(text):
                self.append_message("You", text)
                self.input_field.clear()
                return
            self.append_message("You", text)
            self.input_field.clear()
            self.append_message("Assistant", "No puedo responder: el modelo local no está cargado.")
            return

        if any(k in lower for k in ["es un repo de un proyecto de unreal", "es repo de unreal", "es un proyecto de unreal", "proyecto de unreal"]):
            if try_llm_with_metadata(text):
                self.append_message("You", text)
                self.input_field.clear()
                return
            self.append_message("You", text)
            self.input_field.clear()
            self.append_message("Assistant", "No puedo responder: el modelo local no está cargado.")
            return

        # Fallback to LLM
        self._maybe_refresh_repo_context_for_query(text)
        self.append_message("You", text)
        self.input_field.clear()
        self.messages.append({"role": "user", "content": text})

        self.status_bar.setText("Thinking...")

        self.worker = Worker(self.llm, self.messages)
        self.worker.text_received.connect(self.on_text_received)
        self.worker.finished.connect(self.on_generation_finished)

        self.current_response = ""
        self.worker.start()
        
    def on_text_received(self, text):
        self.current_response += text
        
    def on_generation_finished(self):
        self.messages.append({"role": "assistant", "content": self.current_response})
        self.status_bar.setText("Ready")
        if self.current_response:
            self.append_message("Assistant", self.current_response)
        self.current_response = ""
        
    def append_message(self, sender, text):
        theme = get_current_theme()
        bg = theme.colors['surface'] if sender == "You" else theme.colors['surface_hover']
        label_color = "#4ade80" if sender == "You" else "#60a5fa"
        if sender == "System":
            bg = theme.colors['danger'] + "20"
            label_color = theme.colors['danger']

        body = self._escape_html(text)
        html = (
            f"<div style='margin:10px 0; padding:10px 12px; border-radius:12px; "
            f"background:{bg}; color:{theme.colors['text']}; border:none;'>"
            f"<div style='font-weight:700; margin-bottom:6px; color:{label_color}; text-transform:uppercase; font-size:11px;'>{sender}</div>"
            f"<div style='white-space:pre-wrap; line-height:1.5; font-size:13px;'>{body}</div>"
            "</div>"
        )
        self.chat_area.append(html)
        self.chat_area.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_area.ensureCursorVisible()

    def _escape_html(self, text: str) -> str:
        if text is None:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

    def _get_application_name(self) -> str:
        try:
            app = QApplication.instance()
            if app:
                name = app.applicationName()
                if name:
                    return name
        except Exception:
            pass
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.basename(root) or "Git Client"

    def _get_repo_info(self, repo_path: str) -> tuple[str, str | None]:
        if not repo_path:
            return ("unknown", None)
        name = os.path.basename(repo_path.rstrip(os.sep))
        remote = None
        try:
            result = subprocess.run([
                "git", "-C", repo_path, "remote", "get-url", "origin"
            ], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                remote = result.stdout.strip()
        except Exception:
            pass
        return (name, remote)

    def _get_repo_metadata(self, repo_path: str) -> dict:
        repo_name, repo_remote = self._get_repo_info(repo_path)
        uproject = self._find_uproject(repo_path)
        engine_assoc = None
        engine_ver = None
        plugins = []
        if uproject:
            try:
                with open(uproject, 'r', encoding='utf-8') as f:
                    j = json.load(f)
                engine_assoc = j.get('EngineAssociation')
                engine_ver = j.get('EngineVersion')
                for p in (j.get('Plugins') or []):
                    if p.get('Name'):
                        plugins.append({'name': p.get('Name'), 'enabled': bool(p.get('Enabled'))})
            except Exception:
                pass

        ray = self._detect_raytracing(repo_path)
        size = None
        try:
            size = self._get_repo_size_summary(repo_path)
        except Exception:
            size = None

        return {
            'path': repo_path,
            'name': repo_name,
            'remote': repo_remote,
            'uproject': uproject,
            'engine_association': engine_assoc,
            'engine_version': engine_ver,
            'plugins': plugins,
            'raytracing': ray,
            'size': size,
        }

    def _start_worker_with_messages(self, messages: list):
        if not LLAMA_AVAILABLE or not self.llm:
            return
        try:
            self.status_bar.setText("Thinking...")
            self.worker = Worker(self.llm, messages)
            self.worker.text_received.connect(self.on_text_received)
            self.worker.finished.connect(self.on_generation_finished)
            self.current_response = ""
            self.chat_area.append(f"<b>Assistant:</b> ")
            self.worker.start()
        except Exception:
            pass

    def _write_repo_metadata(self, repo_path: str, include_size: bool = False):
        if not repo_path or not os.path.isdir(repo_path):
            return
        uproject = self._find_uproject(repo_path)
        is_unreal = bool(uproject)
        engine_assoc = None
        engine_ver = None
        plugins = []
        try:
            if uproject:
                with open(uproject, 'r', encoding='utf-8') as f:
                    j = json.load(f)
                engine_assoc = j.get('EngineAssociation')
                engine_ver = j.get('EngineVersion')
                p = j.get('Plugins') or []
                for it in p:
                    name = it.get('Name')
                    if name:
                        plugins.append({'name': name, 'enabled': bool(it.get('Enabled'))})
        except Exception:
            pass

        repo_name, repo_remote = self._get_repo_info(repo_path)
        ray = self._detect_raytracing(repo_path)
        size = None
        if include_size:
            try:
                size = self._get_repo_size_summary(repo_path)
            except Exception:
                size = None

        config_dir = Path.home() / '.unreal-git-client'
        try:
            os.makedirs(config_dir, exist_ok=True)
            out = {
                'path': repo_path,
                'name': repo_name,
                'remote': repo_remote,
                'is_unreal': is_unreal,
                'uproject': uproject,
                'engine_association': engine_assoc,
                'engine_version': engine_ver,
                'plugins': plugins,
                'raytracing': ray,
                'size': size,
            }
            dest = config_dir / 'current_repo.json'
            with open(dest, 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_repo_path(self, repo_path: str):
        self.repo_path = repo_path
        repo_context = self._build_repo_context(include_size=False)
        repo_name, repo_remote = self._get_repo_info(repo_path)
        system_intro = f"You are the AI Assistant for the '{self._get_application_name()}' application. Current repository: {repo_name} ({repo_remote or 'no remote'})"
        if self._repo_context_index is None:
            self.messages.insert(1, {"role": "system", "content": repo_context})
            self._repo_context_index = 1
        else:
            if 0 <= self._repo_context_index < len(self.messages):
                self.messages[self._repo_context_index]["content"] = repo_context
            else:
                self.messages.insert(1, {"role": "system", "content": repo_context})
                self._repo_context_index = 1

        if self.messages and len(self.messages) > 0:
            self.messages[0]["content"] = system_intro + "\n\n" + (getattr(self, "_instructions", ""))
        try:
            self._write_repo_metadata(repo_path, include_size=False)
        except Exception:
            pass

    def _maybe_refresh_repo_context_for_query(self, user_text: str):
        if not self.repo_path or not os.path.isdir(self.repo_path):
            return

        text = (user_text or "").lower()

        wants_unreal_info = any(k in text for k in [
            "unreal", "uproject", "ue", "engine", "version", "versión", "raytracing", "ray tracing",
            "plugins", "plug-ins", "plugin", "rtx"
        ])
        wants_size = any(k in text for k in [
            "pesa", "peso", "tamaño", "tamano", "size", "meg", "gb", "gigas"
        ]) and any(k in text for k in ["repo", "repositorio", "project", "proyecto", "carpeta", "folder"])

        if not (wants_unreal_info or wants_size):
            return

        include_size = bool(wants_size)

        now = time.monotonic()
        cache_ttl = 30.0
        if self._repo_context_cache and (now - self._repo_context_cache_time) < cache_ttl and (not include_size):
            self._set_repo_context_message(self._repo_context_cache)
            return

        context = self._build_repo_context(include_size=include_size)
        if not include_size:
            self._repo_context_cache = context
            self._repo_context_cache_time = now
        self._set_repo_context_message(context)
        try:
            self._write_repo_metadata(self.repo_path, include_size=include_size)
        except Exception:
            pass

    def _set_repo_context_message(self, content: str):
        if self._repo_context_index is None:
            self.messages.insert(1, {"role": "system", "content": content})
            self._repo_context_index = 1
            return

        if 0 <= self._repo_context_index < len(self.messages):
            self.messages[self._repo_context_index]["content"] = content
        else:
            self.messages.insert(1, {"role": "system", "content": content})
            self._repo_context_index = 1

    def _build_repo_context(self, include_size: bool) -> str:
        repo_path = self.repo_path
        if not repo_path or not os.path.isdir(repo_path):
            return "Repository context: (no repository opened)"

        uproject_path = self._find_uproject(repo_path)
        is_unreal = uproject_path is not None

        engine_assoc = None
        plugin_names = []
        plugin_enabled = []
        if uproject_path:
            try:
                with open(uproject_path, "r", encoding="utf-8") as f:
                    uproject = json.load(f)
                engine_assoc = uproject.get("EngineAssociation")
                plugins = uproject.get("Plugins") or []
                for p in plugins:
                    name = p.get("Name")
                    if not name:
                        continue
                    plugin_names.append(name)
                    if p.get("Enabled") is True:
                        plugin_enabled.append(name)
            except Exception:
                pass

        raytracing = self._detect_raytracing(repo_path)

        size_summary = ""
        if include_size:
            size_summary = self._get_repo_size_summary(repo_path)

        unreal_summary = "Unreal project: No"
        if is_unreal:
            unreal_summary = f"Unreal project: Yes ({os.path.basename(uproject_path)})"

        engine_summary = "Unreal Engine version: Unknown"
        if engine_assoc:
            engine_summary = f"Unreal Engine version (EngineAssociation): {engine_assoc}"

        plugins_summary = "Unreal plugins: Unknown"
        if is_unreal:
            if plugin_names:
                enabled_note = ""
                if plugin_enabled and len(plugin_enabled) != len(plugin_names):
                    enabled_note = f" (enabled: {', '.join(sorted(plugin_enabled))})"
                plugins_summary = f"Unreal plugins ({len(plugin_names)}): {', '.join(sorted(plugin_names))}{enabled_note}"
            else:
                plugins_summary = "Unreal plugins: None listed in .uproject"

        ray_summary = "RayTracing: Unknown"
        if raytracing is True:
            ray_summary = "RayTracing: Enabled (found in Config/DefaultEngine.ini)"
        elif raytracing is False:
            ray_summary = "RayTracing: Not enabled (no enabling setting found)"

        lines = [
            "Repository context (auto-detected):",
            f"- Path: {repo_path}",
            f"- {unreal_summary}",
            f"- {engine_summary}",
            f"- {plugins_summary}",
            f"- {ray_summary}",
        ]

        if size_summary:
            lines.append(f"- Local size: {size_summary}")

        return "\n".join(lines)

    def _find_uproject(self, repo_path: str) -> str | None:
        try:
            for entry in os.scandir(repo_path):
                if entry.is_file() and entry.name.lower().endswith(".uproject"):
                    return entry.path
        except Exception:
            pass

        try:
            for root, dirs, files in os.walk(repo_path):
                for f in files:
                    if f.lower().endswith('.uproject'):
                        return os.path.join(root, f)
        except Exception:
            return None

        return None

    def _detect_raytracing(self, repo_path: str) -> bool | None:
        ini_path = os.path.join(repo_path, "Config", "DefaultEngine.ini")
        if not os.path.exists(ini_path):
            return None

        try:
            with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read()
        except Exception:
            return None

        patterns_true = [
            r"(?im)^\s*r\.raytracing\s*=\s*1\s*$",
            r"(?im)^\s*r\.raytracing\s*=\s*true\s*$",
            r"(?im)^\s*r\.supportraytracing\s*=\s*1\s*$",
            r"(?im)^\s*r\.supportraytracing\s*=\s*true\s*$",
            r"(?im)^\s*benableraytracing\s*=\s*true\s*$",
            r"(?im)^\s*benableraytracing\s*=\s*1\s*$",
        ]
        patterns_false = [
            r"(?im)^\s*r\.raytracing\s*=\s*0\s*$",
            r"(?im)^\s*r\.raytracing\s*=\s*false\s*$",
            r"(?im)^\s*benableraytracing\s*=\s*false\s*$",
            r"(?im)^\s*benableraytracing\s*=\s*0\s*$",
        ]

        for p in patterns_true:
            if re.search(p, data):
                return True
        for p in patterns_false:
            if re.search(p, data):
                return False

        return False

    def _get_repo_size_summary(self, repo_path: str) -> str:
        git_dir_size = None
        worktree_size = None

        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            is_git = result.returncode == 0 and "true" in (result.stdout or "").lower()
        except Exception:
            is_git = False

        if is_git:
            try:
                result = subprocess.run(
                    ["git", "-C", repo_path, "rev-parse", "--git-dir"],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                if result.returncode == 0:
                    git_dir = result.stdout.strip()
                    if not os.path.isabs(git_dir):
                        git_dir = os.path.join(repo_path, git_dir)
                    git_dir_size = self._safe_directory_size(git_dir, time_limit_s=5.0, file_limit=200000)
                # Try to get git object size estimate via git count-objects
                try:
                    co = subprocess.run(["git", "-C", repo_path, "count-objects", "-vH"], capture_output=True, text=True, timeout=2)
                    if co.returncode == 0 and co.stdout:
                        for line in co.stdout.splitlines():
                            if line.lower().startswith("size-pack:") or line.lower().startswith("size:"):
                                pack_est = line.split(':', 1)[1].strip()
                                git_dir_size = git_dir_size or 0
                                git_dir_size = f"{pack_est} (git objects estimate)"
                                break
                except Exception:
                    pass
            except Exception:
                pass

        try:
            worktree_size = self._safe_directory_size(repo_path, time_limit_s=5.0, file_limit=200000, exclude_dirs={".git"})
        except Exception:
            pass

        parts = []
        if worktree_size is not None:
            if isinstance(worktree_size, str):
                parts.append(f"working tree ~{worktree_size}")
            else:
                parts.append(f"working tree ~{self._format_bytes(worktree_size)}")
        if git_dir_size is not None:
            if isinstance(git_dir_size, str):
                parts.append(f".git ~{git_dir_size}")
            else:
                parts.append(f".git ~{self._format_bytes(git_dir_size)}")

        if parts:
            return ", ".join(parts) + " (best-effort estimate)"
        return "Unknown"

    def _safe_directory_size(
        self,
        root: str,
        time_limit_s: float = 1.0,
        file_limit: int = 200000,
        exclude_dirs: set[str] | None = None,
    ) -> int | None:
        exclude_dirs = exclude_dirs or set()
        start = time.monotonic()
        total = 0
        files_seen = 0

        for dirpath, dirnames, filenames in os.walk(root):
            if (time.monotonic() - start) > time_limit_s:
                break

            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

            for name in filenames:
                files_seen += 1
                if files_seen > file_limit:
                    return total

                path = os.path.join(dirpath, name)
                try:
                    total += os.path.getsize(path)
                except Exception:
                    continue

            if (time.monotonic() - start) > time_limit_s:
                break

        return total

    def _format_bytes(self, size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        for unit in units:
            if value < 1024.0 or unit == units[-1]:
                if unit == "B":
                    return f"{int(value)} {unit}"
                return f"{value:.2f} {unit}"
            value /= 1024.0

