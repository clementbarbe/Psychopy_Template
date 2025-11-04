"""
Singleton Logger class for PsychoPy experiments
Equivalent to MATLAB/Psychtoolbox Logger with colored terminal output
"""

import sys
import inspect
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


class TermColors:
    """ANSI color codes for terminal output"""
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    
    # Styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    
    # Matlab-style aliases
    COMMENTS = GREEN  # green for ok/success
    KEYWORDS = BLUE   # blue for warnings
    ERRORS = RED      # red for errors
    STRINGS = MAGENTA # purple for strings
    TEXT = RESET      # default/black


class Logger:
    """
    Singleton Logger class for PsychoPy experiments.
    
    Usage:
        logger = get_logger()
        logger.log("Starting experiment")
        logger.ok("Configuration loaded successfully")
        logger.warn("Using default parameters")
        logger.err("Failed to load stimuli")
        
    Note:
        This logger should NOT be used for real-time logging in tight loops.
        Use standard print() for high-frequency logging.
    """
    
    _instance: Optional['Logger'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger (only once)"""
        if not Logger._initialized:
            self._padding: int = 0
            self._last_msg: str = ''
            self._creation_time: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self._use_colors: bool = self._supports_color()
            self._root_dir: Optional[Path] = self._find_root_dir()
            
            Logger._initialized = True
            
            # Warning message (like in MATLAB version)
            self.warn("Logger class MUST NOT be used for real time logging. Use 'print()' instead.")
    
    @staticmethod
    def _supports_color() -> bool:
        """Check if terminal supports ANSI color codes"""
        # Windows CMD doesn't support colors by default (but Windows Terminal does)
        # Unix terminals usually support colors
        if sys.platform == "win32":
            # Check if running in Windows Terminal or with colorama
            try:
                import colorama
                colorama.init()
                return True
            except ImportError:
                return False
        return True
    
    @staticmethod
    def _find_root_dir() -> Optional[Path]:
        """Find project root directory (where the main script is)"""
        try:
            # Get the main script location
            frame = inspect.stack()[-1]
            main_file = Path(frame.filename).resolve()
            return main_file.parent
        except Exception:
            return None
    
    @staticmethod
    def get_instance() -> 'Logger':
        """Get the singleton instance"""
        return Logger()
    
    @staticmethod
    def get() -> 'Logger':
        """Shortcut to get the singleton instance"""
        return Logger()
    
    @property
    def padding(self) -> int:
        """Get padding value for caller alignment"""
        return self._padding
    
    @padding.setter
    def padding(self, value: int):
        """Set padding value for caller alignment"""
        if not isinstance(value, int) or value < 0:
            raise ValueError("Padding must be a non-negative integer")
        self._padding = value
    
    @property
    def last_msg(self) -> str:
        """Get the last logged message"""
        return self._last_msg
    
    @property
    def creation(self) -> str:
        """Get logger creation timestamp"""
        return self._creation_time
    
    def _get_caller(self) -> str:
        """
        Get the caller's file and function name.
        Mimics MATLAB's dbstack functionality.
        """
        try:
            # Get stack (skip: this method, _format_message, and the log method)
            stack = inspect.stack()[3]
            
            # Get file path
            file_path = Path(stack.filename).resolve()
            
            # Make path relative to root if possible
            if self._root_dir:
                try:
                    file_path = file_path.relative_to(self._root_dir)
                except ValueError:
                    pass  # Keep absolute path if not relative to root
            
            # Remove .py extension
            caller_str = str(file_path).replace('.py', '')
            
            # Convert path separators to dots (package.module style)
            caller_str = caller_str.replace('\\', '.').replace('/', '.')
            
            # Add function name
            func_name = stack.function
            if func_name != '<module>':
                caller_str = f"{caller_str}.{func_name}"
            
            return caller_str
            
        except Exception:
            return ''
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in HH:MM:SS format"""
        return datetime.now().strftime('%H:%M:%S')
    
    def _format_message(self, formatted_str: str, *args, **kwargs) -> str:
        """
        Format message with timestamp and caller information.
        
        Args:
            formatted_str: Format string (like printf/sprintf)
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
        """
        # Format the message
        if args or kwargs:
            msg = formatted_str.format(*args, **kwargs) if '{' in formatted_str else formatted_str % args
        else:
            msg = formatted_str
        
        # Build full message with timestamp and caller
        timestamp = self._get_timestamp()
        caller = self._get_caller()
        
        full_msg = f"[{timestamp} - {caller:<{self._padding}}] {msg}"
        self._last_msg = full_msg
        
        return full_msg
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are supported"""
        if self._use_colors:
            return f"{color}{text}{TermColors.RESET}"
        return text
    
    def log(self, formatted_str: str, *args, **kwargs):
        """
        Log a standard message (black/default color).
        
        Args:
            formatted_str: Format string
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
        """
        msg = self._format_message(formatted_str, *args, **kwargs)
        print(msg)
    
    def ok(self, formatted_str: str, *args, **kwargs):
        """
        Log a success message (green color).
        
        Args:
            formatted_str: Format string
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
        """
        msg = self._format_message(formatted_str, *args, **kwargs)
        print(self._colorize(msg, TermColors.COMMENTS))
    
    def warn(self, formatted_str: str, *args, **kwargs):
        """
        Log a warning message (blue color).
        
        Args:
            formatted_str: Format string
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
        """
        msg = self._format_message(formatted_str, *args, **kwargs)
        print(self._colorize(msg, TermColors.KEYWORDS))
    
    def warning(self, formatted_str: str, *args, **kwargs):
        """
        Log a warning using Python's warning system.
        
        Args:
            formatted_str: Format string
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
        """
        import warnings
        msg = self._format_message(formatted_str, *args, **kwargs)
        warnings.warn(msg, UserWarning, stacklevel=2)
    
    def err(self, formatted_str: str, *args, **kwargs):
        """
        Log an error message (red color) without raising an exception.
        
        Args:
            formatted_str: Format string
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
        """
        msg = self._format_message(formatted_str, *args, **kwargs)
        print(self._colorize(msg, TermColors.ERRORS), file=sys.stderr)
    
    def error(self, formatted_str: str, *args, **kwargs):
        """
        Log an error and raise an exception.
        
        Args:
            formatted_str: Format string
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
            
        Raises:
            RuntimeError: Always raised with the formatted message
        """
        msg = self._format_message(formatted_str, *args, **kwargs)
        raise RuntimeError(msg)
    
    def assert_true(self, condition: bool, formatted_str: str, *args, **kwargs):
        """
        Assert a condition and raise an error if false.
        
        Args:
            condition: Condition to check
            formatted_str: Format string for error message
            *args: Positional arguments for formatting
            **kwargs: Keyword arguments for formatting
            
        Raises:
            AssertionError: If condition is False
        """
        if not condition:
            msg = self._format_message(formatted_str, *args, **kwargs)
            raise AssertionError(msg)


# Module-level convenience function (like MATLAB's getLogger())
def get_logger() -> Logger:
    """
    Get the singleton Logger instance.
    
    Returns:
        Logger: The singleton logger instance
        
    Example:
        >>> logger = get_logger()
        >>> logger.log("Experiment started")
        >>> logger.ok("Stimuli loaded successfully")
    """
    return Logger.get_instance()

