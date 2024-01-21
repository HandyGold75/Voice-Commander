import os
import sys
from contextlib import contextmanager
from json import dump, load
from traceback import format_exc

from PySide6.QtCore import QObject, QRunnable, Signal, Slot
from speech_recognition import Microphone


class Config:
    def __init__(self):
        self.workFolder = os.path.split(__file__)[0].replace("\\", "/").replace("/lib", "")

        with ignoreStderr():
            microphones = Microphone.list_microphone_names()
        defaultMic = tuple(mic for mic in microphones if "default" in mic)[0]

        self.defaultConfig = {"Profile": "Default.json", "Microphone": defaultMic, "Phrase time": 2, "Speach Recognizer": "vosk", "vosk:Model": "small-en", "whisper:Language": "english", "whisper:Model": "tiny"}

        if not os.path.exists(f"{self.workFolder}/config.json"):
            with open(f"{self.workFolder}/config.json", "w") as fileW:
                dump(self.defaultConfig, fileW, indent=4)

        with open(f"{self.workFolder}/config.json", "r") as fileR:
            if tuple(load(fileR)) == tuple(self.defaultConfig):
                return None

        with open(f"{self.workFolder}/config.json", "w") as fileW:
            dump(self.defaultConfig, fileW, indent=4)

    def get(self):
        with open(f"{self.workFolder}/config.json", "r") as fileR:
            return load(fileR)

    def set(self, key: str, value: any):
        if not key in self.defaultConfig:
            raise ValueError(f"Key {key} not in config!")

        if not type(value) is type(self.defaultConfig[key]):
            raise ValueError(f"Value type incorrect! {type(self.defaultConfig[key])} != {type(value)}")

        currentConfig = self.get()
        currentConfig[key] = value
        with open(f"{self.workFolder}/config.json", "w") as fileW:
            dump(currentConfig, fileW, indent=4)


class Profile:
    def __init__(self):
        self.workFolder = os.path.split(__file__)[0].replace("\\", "/").replace("/lib", "")

        if not os.path.exists(f"{self.workFolder}/profiles"):
            os.makedirs(f"{self.workFolder}/profiles")

        self.config = Config()

        self.defaultProfile = {"voiceCommands": []}
        self.voiceCommandsTemplate = {"command": str, "macro": str, "sensitivity": int}

        if len(os.listdir(f"{self.workFolder}/profiles")) == 0:
            with open(f"{self.workFolder}/profiles/Default.json", "w") as fileW:
                dump(self.defaultProfile, fileW, indent=4)

            self.config.set("Profile", "default")

    def _voiceCommandsVerifyRecord(self, record):
        if not type(record) is dict:
            raise ValueError(f"Value type incorrect! {type(record)} != {dict}")

        if {k: type(record[k]) for k in record} != self.voiceCommandsTemplate:
            raise ValueError(f"Dict format incorrect! {dict({k: type(record[k]) for k in record})} != {self.voiceCommandsTemplate}")

    def getProfile(self):
        return self.config.get()["Profile"]

    def getShortProfile(self):
        return self.config.get()["Profile"].replace(".json", "")

    def setProfile(self, profile: str):
        if profile != "" and not profile in os.listdir(f"{self.workFolder}/profiles"):
            raise ValueError(f"Profile {profile} not present!")

        self.config.set("Profile", profile)

    def new(self, profile):
        with open(f"{self.workFolder}/profiles/{profile}", "w") as fileW:
            dump(self.defaultProfile, fileW, indent=4)

    def delete(self, profile):
        os.remove(f"{self.workFolder}/profiles/{profile}")

    def list(self):
        return tuple(folder for folder in sorted(os.listdir(f"{self.workFolder}/profiles")) if folder.endswith(".json"))

    def listShort(self):
        return tuple(folder.replace(".json", "", 1) for folder in sorted(os.listdir(f"{self.workFolder}/profiles")) if folder.endswith(".json"))

    def get(self):
        with open(f"{self.workFolder}/profiles/{self.getProfile()}", "r") as fileR:
            return load(fileR)

    def set(self, key: str, value: any):
        if not type(value) is type(self.defaultProfile[key]):
            raise ValueError(f"Value type incorrect! {type(self.defaultProfile[key])} != {type(value)}")

        currentProfile = self.get()
        currentProfile[key] = value
        with open(f"{self.workFolder}/profiles/{self.getProfile()}", "w") as fileW:
            dump(currentProfile, fileW, indent=4)

    def addCommand(self, record: dict):
        self._voiceCommandsVerifyRecord(record)

        currentProfile = self.get()
        currentProfile["voiceCommands"].append(record)

        with open(f"{self.workFolder}/profiles/{self.getProfile()}", "w") as fileW:
            dump(currentProfile, fileW, indent=4)

    def setCommand(self, index: int, record: dict):
        self._voiceCommandsVerifyRecord(record)

        currentProfile = self.get()
        currentProfile["voiceCommands"][index] = record

        with open(f"{self.workFolder}/profiles/{self.getProfile()}", "w") as fileW:
            dump(currentProfile, fileW, indent=4)

    def delCommand(self, index: int):
        currentProfile = self.get()
        currentProfile["voiceCommands"].pop(index)

        with open(f"{self.workFolder}/profiles/{self.getProfile()}", "w") as fileW:
            dump(currentProfile, fileW, indent=4)


class Worker(QRunnable):
    class WorkerSignals(QObject):
        log = Signal(str, str)
        result = Signal(object)
        error = Signal(object)

    def __init__(self, function, acceptsSignals: bool = False, *args, **kwargs):
        super().__init__()

        self.function = function
        self.acceptsSignals = acceptsSignals
        self.args = args
        self.kwargs = kwargs

        self.signals = self.WorkerSignals()

    @Slot()
    def run(self):
        try:
            if self.acceptsSignals:
                out = self.function(*self.args, **self.kwargs, signals=self.signals)
            else:
                out = self.function(*self.args, **self.kwargs)
        except Exception as err:
            print(format_exc())
            self.signals.error.emit(format_exc())
            return None

        try:
            self.signals.result.emit(out)
        except RuntimeError:
            sys.exit()


@contextmanager
def ignoreStderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        yield
    finally:
        os.dup2(old_stderr, 2)
        os.close(old_stderr)
