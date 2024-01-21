from . import templates as tpl
from .general import Config, Profile, Worker, ignoreStderr
from .recognizers import sphinx, vosk, whisper

Config = Config()
Profile = Profile()

allRecognizers = {
    "vosk": {"recognizer": vosk, "options": ("Model",)},
    "whisper": {"recognizer": whisper, "options": ("Language", "Model")},
    "sphinx": {"recognizer": sphinx, "options": ()},
}

__all__ = (
    "Config",
    "Profile",
    "Worker",
    "ignoreStderr",
    "tpl",
    "allRecognizers",
)
