"""
GitWorker - Background thread for Git operations.

This module provides a QThread-based worker to run Git operations
without blocking the UI.
"""

from PyQt6.QtCore import QThread, QObject, pyqtSignal


class GitOperationSignals(QObject):
    """Signals for Git operation progress and completion."""
    started = pyqtSignal()
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    error = pyqtSignal(str)


class GitWorker(QThread):
    """
    Worker thread for running Git operations asynchronously.
    
    Usage:
        worker = GitWorker(git_manager.push)
        worker.signals.finished.connect(on_push_finished)
        worker.start()
    """
    
    def __init__(self, operation, *args, parent=None, progress_callback=None, **kwargs):
        """
        Initialize the worker.
        
        Args:
            operation: Callable that returns (success: bool, message: str)
            *args: Arguments to pass to the operation
            parent: Parent QObject for proper cleanup
            progress_callback: If True, pass a progress callback to the operation
            **kwargs: Keyword arguments to pass to the operation
        """
        super().__init__(parent)
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
        self.signals = GitOperationSignals()
        self._use_progress_callback = progress_callback
        
    def run(self):
        """Execute the Git operation in a background thread."""
        self.signals.started.emit()
        
        try:
            if self._use_progress_callback:
                # Pass a progress callback that emits signals
                self.kwargs['progress_callback'] = lambda msg: self.signals.progress.emit(msg)
            
            success, message = self.operation(*self.args, **self.kwargs)
            self.signals.finished.emit(success, message)
        except Exception as e:
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False, str(e))


class GitPullWorker(GitWorker):
    """Specialized worker for pull operations."""
    
    def __init__(self, git_manager, parent=None):
        super().__init__(git_manager.pull, parent=parent)


class GitPushWorker(GitWorker):
    """Specialized worker for push operations with progress."""
    
    def __init__(self, git_manager, parent=None):
        super().__init__(git_manager.push, parent=parent, progress_callback=True)


class GitFetchWorker(GitWorker):
    """Specialized worker for fetch operations."""
    
    def __init__(self, git_manager, parent=None):
        super().__init__(git_manager.fetch, parent=parent)


class GitCommitWorker(GitWorker):
    """Specialized worker for commit operations."""
    
    def __init__(self, git_manager, message, parent=None):
        super().__init__(git_manager.commit, message, parent=parent)
