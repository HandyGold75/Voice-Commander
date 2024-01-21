import os
from json import loads
from shutil import move, rmtree, unpack_archive
from time import sleep

from requests import get
from speech_recognition import Recognizer, RequestError, UnknownValueError

if False:
    import numpy
    import pocketsphinx
    import PyAudio
    import soundfile
    import torch
    import vosk
    import whisper  # openai-whisper


class vosk:
    # https://alphacephei.com/vosk/models

    allModels = {
        "small-en": ("vosk-model-small-en-us-0.15", "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"),
        "en-us": ("vosk-model-en-us-0.22", "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"),
        "small-nl": ("vosk-model-small-nl-0.22", "https://alphacephei.com/vosk/models/vosk-model-small-nl-0.22.zip"),
        "nl-spraakherkenning": ("vosk-model-nl-spraakherkenning-0.6", "https://alphacephei.com/vosk/models/vosk-model-nl-spraakherkenning-0.6.zip"),
    }

    def __init__(self, signals: object, config: dict, *args, **kwargs):
        self.signals = signals
        self.recognizer = Recognizer()

        self.workfolder = os.path.split(__file__)[0].replace("\\", "/").replace("/lib", "")

        self.model = config["vosk:Model"]

        self.getModel(self.model)

    def getModel(self, model):
        if not os.path.exists(f"{self.workfolder}/models"):
            os.makedirs(f"{self.workfolder}/models")

        if not os.path.exists(f"{self.workfolder}/models/{self.allModels[model][0]}.zip"):
            self.signals.log.emit(f"Downloading vosk model {self.allModels[model][0]}.", "Yellow")

            for i in range(1, 4):
                req = get(self.allModels[model][-1])
                if req.status_code == 200:
                    with open(f"{self.workfolder}/models/{self.allModels[model][0]}.zip", "wb") as fileW:
                        fileW.write(req.content)
                    break

                sleep(i)

        self.signals.log.emit(f"Preparing vosk model {self.allModels[model][0]}.", "Yellow")

        unpack_archive(f"{self.workfolder}/models/{self.allModels[model][0]}.zip", f"{self.workfolder}/models")

        if os.path.exists(f"{self.workfolder}/model"):
            rmtree(f"{self.workfolder}/model")

        move(f"{self.workfolder}/models/{self.allModels[model][0]}", f"{self.workfolder}/model")

        os.chdir(self.workfolder)

    def run(self, audio):
        try:
            out = self.recognizer.recognize_vosk(audio)
            out = "".join(char for char in tuple(loads(out)["text"].lower()) if char.isalnum() or char.isspace()).strip()
            if out != "":
                self.signals.log.emit(out, "Green")
            return out

        except UnknownValueError:
            self.signals.log.emit("Vosk failed to reconize audio!", "Orange")
            return None

        except RequestError as e:
            self.signals.log.emit("Vosk error; {0}".format(e), "Red")
            return None


class whisper:
    # https://github.com/openai/whisper/blob/main/whisper/tokenizer.py

    allLanguages = (
        "",
        "english",
        "chinese",
        "german",
        "spanish",
        "russian",
        "korean",
        "french",
        "japanese",
        "portuguese",
        "turkish",
        "polish",
        "catalan",
        "dutch",
        "arabic",
        "swedish",
        "italian",
        "indonesian",
        "hindi",
        "finnish",
        "vietnamese",
        "hebrew",
        "ukrainian",
        "greek",
        "malay",
        "czech",
        "romanian",
        "danish",
        "hungarian",
        "tamil",
        "norwegian",
        "thai",
        "urdu",
        "croatian",
        "bulgarian",
        "lithuanian",
        "latin",
        "maori",
        "malayalam",
        "welsh",
        "slovak",
        "telugu",
        "persian",
        "latvian",
        "bengali",
        "serbian",
        "azerbaijani",
        "slovenian",
        "kannada",
        "estonian",
        "macedonian",
        "breton",
        "basque",
        "icelandic",
        "armenian",
        "nepali",
        "mongolian",
        "bosnian",
        "kazakh",
        "albanian",
        "swahili",
        "galician",
        "marathi",
        "punjabi",
        "sinhala",
        "khmer",
        "shona",
        "yoruba",
        "somali",
        "afrikaans",
        "occitan",
        "georgian",
        "belarusian",
        "tajik",
        "sindhi",
        "gujarati",
        "amharic",
        "yiddish",
        "lao",
        "uzbek",
        "faroese",
        "haitian creole",
        "pashto",
        "turkmen",
        "nynorsk",
        "maltese",
        "sanskrit",
        "luxembourgish",
        "myanmar",
        "tibetan",
        "tagalog",
        "malagasy",
        "assamese",
        "tatar",
        "hawaiian",
        "lingala",
        "hausa",
        "bashkir",
        "javanese",
        "sundanese",
        "cantonese",
    )

    # https://github.com/openai/whisper/blob/main/whisper/__init__.py

    allModels = ("tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3")

    def __init__(self, signals: object, config: dict, *args, **kwargs):
        self.signals = signals
        self.recognizer = Recognizer()

        self.language = config["whisper:Language"]
        self.model = config["whisper:Model"]

        self.signals.log.emit("Whisper might take some time to load the first time or when selecting new languages.", "White")

    def run(self, audio):
        try:
            out = self.recognizer.recognize_whisper(audio, model=f'{self.model}{".en" if self.language == "english" and self.model != "large" else ""}', language=None if self.language == "" else self.language)
            out = "".join(char for char in tuple(out.lower()) if char.isalnum() or char.isspace()).strip()
            if out != "":
                self.signals.log.emit(out, "Green")
            return out

        except UnknownValueError:
            self.signals.log.emit("Whisper failed to reconize audio!", "Orange")
            return None

        except RequestError as e:
            self.signals.log.emit("Whisper error; {0}".format(e), "Red")
            return None


class sphinx:
    def __init__(self, signals: object, profile: dict, *args, **kwargs):
        self.signals = signals
        self.recognizer = Recognizer()

        self.vcs = tuple((vc["command"], vc["sensitivity"] / 10) for vc in profile["voiceCommands"])

        self.signals.log.emit("Sphinx will only recognize phrases that are defined in the profile.", "White")

    def run(self, audio):
        try:
            out = self.recognizer.recognize_sphinx(audio, language="en-US", keyword_entries=self.vcs)
            out = "".join(char for char in tuple(out.lower()) if char.isalnum() or char.isspace()).strip()
            if out != "":
                self.signals.log.emit(out, "Green")
            return out

        except UnknownValueError:
            self.signals.log.emit("Sphinx failed to reconize audio!", "Orange")
            return None

        except RequestError as e:
            self.signals.log.emit("Sphinx error; {0}".format(e), "Red")
            return None
