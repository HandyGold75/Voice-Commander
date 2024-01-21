import os
import sys
from string import printable
from time import sleep
from traceback import format_exc

from lib import Config, Profile, Worker, allRecognizers, ignoreStderr, tpl
from pynput.keyboard import Controller, Key
from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLineEdit, QMainWindow, QPushButton, QSizePolicy, QSpinBox, QStatusBar, QVBoxLayout, QWidget
from speech_recognition import Microphone, Recognizer, WaitTimeoutError


class VCEngine:
    def __init__(self):
        self.stop = False

        self.currentConfig = {}
        self.currentProfile = {}

        self.updateRecognizer = False
        self.updateMicrophone = False
        self.currentRecognizer = None
        self.currentMicrophone = None

        self.signals = None

        self.listner = Recognizer()
        self.keyboard = Controller()

        self.app = QApplication(sys.argv)
        self.window = VCMainWindow(self.app, self)
        self.threadpool = QThreadPool()

        self.app.aboutToQuit.connect(self.quit)

        self.threadAudioListner = None
        self.threadConfigListner = None

    def startAudioListner(self):
        def handleError(err):
            self.window.passLog(err, "Red")
            self.startAudioListner()

        self.threadAudioListner = Worker(self.audioListner, acceptsSignals=True)
        self.threadAudioListner.signals.log.connect(self.window.passLog)
        self.threadAudioListner.signals.result.connect(self.window.passLog)
        self.threadAudioListner.signals.error.connect(handleError)

        self.threadpool.start(self.threadAudioListner)

    def audioListner(self, signals):
        self.signals = signals

        self.updateConfig()
        self.updateProfile()
        self.doUpdateRecognizer()
        self.doUpdateMicrophone()

        while not self.stop:
            while self.currentRecognizer is None or self.currentMicrophone is None or self.currentConfig == {}:
                sleep(0.1)

            if self.updateRecognizer:
                self.updateRecognizer = False
                self.doUpdateRecognizer()

            if self.updateMicrophone:
                self.updateMicrophone = False
                self.doUpdateMicrophone()

            try:
                with ignoreStderr():
                    with self.currentMicrophone as source:
                        audio = self.listner.listen(source, timeout=1, phrase_time_limit=self.currentConfig["Phrase time"])
            except (WaitTimeoutError, AssertionError):
                sleep(0.1)
                continue
            except AttributeError:
                print(format_exc())
                self.updateMicrophone = True
                continue

            command = self.currentRecognizer.run(audio)
            if not command is None and command != "":
                self.parseCommand(command)

    def updateConfig(self):
        self.currentConfig = Config.get()
        self.signals.log.emit(f"Loaded config", "Green")

    def updateProfile(self):
        self.currentProfile = Profile.get()
        self.signals.log.emit(f"Loaded profile: {self.currentConfig['Profile']}", "Green")

    def doUpdateRecognizer(self):
        self.currentRecognizer = allRecognizers[self.currentConfig["Speach Recognizer"]]["recognizer"](signals=self.signals, config=Config.get(), profile=Profile.get())
        self.signals.log.emit(f"Loaded recognizer: {self.currentConfig['Speach Recognizer']}", "Green")

    def doUpdateMicrophone(self):
        with ignoreStderr():
            newMicrophone = tuple(Microphone(i) for i, mic in enumerate(Microphone.list_microphone_names()) if mic == self.currentConfig["Microphone"])[0]

        try:
            with ignoreStderr():
                with newMicrophone as source:
                    self.listner.adjust_for_ambient_noise(source, 3)
        except AttributeError:
            with ignoreStderr():
                spoofedMicrophone = tuple(mic for mic in Microphone.list_microphone_names() if "default" in mic)[0]
            Config.set("Microphone", spoofedMicrophone)
            self.signals.log.emit(f"Failed to select microphone: {spoofedMicrophone}", "Red")

            self.updateConfig()
            self.updateMicrophone = True

            return None

        self.currentMicrophone = newMicrophone
        self.signals.log.emit(f"Listening to microphone: {self.currentConfig['Microphone']}", "Green")

    def parseCommand(self, command: str):
        selectedIndex = None

        for index, com, sensitivity in tuple((i, record["command"], record["sensitivity"]) for i, record in enumerate(self.currentProfile["voiceCommands"])):
            if command == com:
                self.exec(self.currentProfile["voiceCommands"][index]["macro"].split(";"))
                return None

            if not selectedIndex is None or sensitivity < 1:
                continue

            for subCom in command.split(" "):
                if subCom == com:
                    selectedIndex = index
                    break

        if not selectedIndex is None:
            self.exec(self.currentProfile["voiceCommands"][selectedIndex[0]]["macro"].split(";"))

    def exec(self, commands):
        for sequence in commands:
            if hasattr(Key, sequence):
                key = getattr(Key, sequence)
                if not callable(key):
                    self.keyboard.press(key)
                    self.keyboard.release(key)
                    sleep(0.1)
                    continue

            for key in tuple(sequence):
                if key in printable:
                    self.keyboard.press(key)
                    self.keyboard.release(key)
                    sleep(0.1)

    def quit(self):
        self.stop = True

    def main(self):
        self.startAudioListner()

        sys.exit(self.app.exec())


class VCMainWindow(QMainWindow):
    def __init__(self, app, engine):
        super().__init__()
        self.app = app
        self.engine = engine

        self.setWindowTitle("Voice Commander")
        self.resize(750, 200)

        self.setCentralWidget(VCHomeWidget(self))
        self.setStatusBar(QStatusBar(self))

        self.show()

    def passLog(self, msg, color: str = "White"):
        centralWidget = self.centralWidget()
        if hasattr(centralWidget, "log"):
            centralWidget.log(msg, color)


class VCHomeWidget(QWidget):
    def __init__(self, window):
        super().__init__()
        self.win = window
        self.app = window.app
        self.engine = window.engine

        self.workFolder = os.path.split(__file__)[0].replace("\\", "/")

        self.combo_profile = None
        self.combo_microphone = None
        self.combo_recognizer = None
        self.textbrowser_text = None
        self.spinBox_phraseTime = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.layout_top = QHBoxLayout()
        layout.addLayout(self.layout_top)

        self.layout_left = QVBoxLayout()
        self.layout_right = QVBoxLayout()

        layout_middle = QHBoxLayout()
        layout_middle.addLayout(self.layout_left)
        layout_middle.addLayout(self.layout_right)
        layout.addLayout(layout_middle)

        self.leftLayout()
        self.topLayout()
        self.rightLayout()

    def topLayout(self):
        self.layout_top.addWidget(tpl.getLabel("Profile"))

        self.combo_profile = tpl.getComboBox(Profile.listShort(), Profile.getShortProfile(), connect=self.selectProfile)
        Profile.setProfile(f"{self.combo_profile.currentText()}.json")
        self.layout_top.addWidget(self.combo_profile)

        self.layout_top.addWidget(tpl.getButton("New", connect=self.newProfile))
        self.layout_top.addWidget(tpl.getButton("Edit", connect=self.editProfile))
        self.layout_top.addWidget(tpl.getButton("Delete", connect=self.deleteProfile))

        self.layout_top.addWidget(tpl.getSpacer())

        self.layout_top.addWidget(tpl.getLabel("Microphone"))

        with ignoreStderr():
            microphones = Microphone.list_microphone_names()
        microphone = Config.get()["Microphone"]
        self.combo_microphone = tpl.getComboBox(microphones, microphone if microphone in microphones else microphones[0], connect=self.selectMicrophone)
        Config.set("Microphone", self.combo_microphone.currentText())
        self.layout_top.addWidget(self.combo_microphone)

    def leftLayout(self):
        self.textbrowser_text = tpl.getTextBrowser(f'<img src="{self.workFolder}/images/Yellow.svg" height="10"/> Starting Voice Commander')
        self.layout_left.addWidget(self.textbrowser_text)

    def rightLayout(self):
        self.layout_right.addWidget(tpl.getSpacer(QFrame.Shape.HLine))

        self.layout_right.addWidget(tpl.getButton("Calibrate\nMicrophone", connect=self.calibrateMicrophone, sizePolicy=(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)))

        self.layout_right.addWidget(tpl.getSpacer(QFrame.Shape.HLine))

        self.layout_right.addWidget(tpl.getLabel("Phrase time"))

        self.spinBox_phraseTime = tpl.getSpinBox(Config.get()["Phrase time"], (0, 5), connect=self.setPhraseTime, sizePolicy=(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        self.layout_right.addWidget(self.spinBox_phraseTime)

        self.layout_right.addWidget(tpl.getSpacer(QFrame.Shape.HLine))

        self.layout_right.addWidget(tpl.getLabel("Recognizer"))

        recognizerName = Config.get()["Speach Recognizer"]

        self.combo_recognizer = tpl.getComboBox(tuple(allRecognizers), recognizerName, connect=self.setSpeachRecognizer, sizePolicy=(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        Config.set("Speach Recognizer", self.combo_recognizer.currentText())
        self.layout_right.addWidget(self.combo_recognizer)

        self.layout_right.addWidget(tpl.getSpacer(QFrame.Shape.HLine))

        recognizer = allRecognizers[recognizerName]

        if "Language" in recognizer["options"]:
            self.layout_right.addWidget(tpl.getLabel("Language"))

            self.combo_language = tpl.getComboBox(
                recognizer["recognizer"].allLanguages if hasattr(recognizer["recognizer"], "allLanguages") else (), Config.get()[f"{recognizerName}:Language"], connect=self.setLanguage, sizePolicy=(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            )
            Config.set(f"{recognizerName}:Language", self.combo_language.currentText())
            self.layout_right.addWidget(self.combo_language)

        if "Model" in recognizer["options"]:
            self.layout_right.addWidget(tpl.getLabel("Model"))

            self.combo_model = tpl.getComboBox(
                tuple(recognizer["recognizer"].allModels) if hasattr(recognizer["recognizer"], "allModels") else (), Config.get()[f"{recognizerName}:Model"], connect=self.setModel, sizePolicy=(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            )
            Config.set(f"{recognizerName}:Model", self.combo_model.currentText())
            self.layout_right.addWidget(self.combo_model)

        self.layout_right.addStretch()

    def log(self, msg, color: str = "White"):
        self.textbrowser_text.insertHtml(f'<br><img src="{self.workFolder}/images/{color}.svg" height="10"/> {msg}')
        self.textbrowser_text.moveCursor(QTextCursor.MoveOperation(11), QTextCursor.MoveMode(0))

    def selectProfile(self):
        pf = self.combo_profile.currentText()
        Profile.setProfile(f'{pf}{"" if pf == "" else ".json"}')
        self.log(f"Deselected profiles.", "Red") if pf == "" else self.log(f"Selected profile: {pf}", "Yellow")
        self.engine.updateProfile()

    def selectMicrophone(self):
        mic = self.combo_microphone.currentText()
        Config.set("Microphone", mic)
        self.log(f"Deselected microphone.", "Red") if mic == "" else self.log(f"Selected microphone: {mic}", "Yellow")
        self.engine.updateConfig()
        self.engine.updateMicrophone = True

    def newProfile(self):
        pfs = Profile.list()
        for i in range(1, 1001):
            if f"New Profile {i}.json" in pfs:
                continue

            Profile.new(f"New Profile {i}.json")

            self.combo_profile.addItem(f"New Profile {i}")
            self.log(f"Created profile: New Profile {i}", "Yellow")

            self.combo_profile.setCurrentText(f"New Profile {i}")
            Profile.setProfile(f"New Profile {i}.json")

            break

    def editProfile(self):
        if Profile.getProfile() == "":
            return None

        self.win.setCentralWidget(VCProfileWidget(self.win))

    def deleteProfile(self):
        if self.combo_profile.currentIndex() < 0:
            return None

        pf, pfIndex = (self.combo_profile.currentText(), self.combo_profile.currentIndex())
        Profile.delete(f"{pf}.json")
        self.combo_profile.removeItem(pfIndex)

        self.log(f"Removed profile: {pf}", "Yellow")

    def calibrateMicrophone(self):
        self.log(f"Calibrating microphone: {self.combo_microphone.currentText()}", "Yellow")
        self.engine.updateMicrophone = True

    def setPhraseTime(self):
        Config.set("Phrase time", int(self.spinBox_phraseTime.text()))
        self.engine.updateConfig()

    def setSpeachRecognizer(self):
        Config.set("Speach Recognizer", self.combo_recognizer.currentText())
        self.win.setCentralWidget(VCHomeWidget(self.win))
        self.engine.updateConfig()
        self.engine.updateRecognizer = True

    def setLanguage(self):
        Config.set(f"{Config.get()['Speach Recognizer']}:Language", self.combo_language.currentText())
        self.engine.updateConfig()
        self.engine.updateRecognizer = True

    def setModel(self):
        Config.set(f"{Config.get()['Speach Recognizer']}:Model", self.combo_model.currentText())
        self.engine.updateConfig()
        self.engine.updateRecognizer = True


class VCProfileWidget(QWidget):
    def __init__(self, window, autoFocus: int = 0):
        super().__init__()
        self.win = window
        self.app = window.app
        self.engine = window.engine

        self.inp_newInput = {}
        self.inp_recordInputs = []

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.layout_top = QHBoxLayout()
        layout.addLayout(self.layout_top)
        self.topLayout()

        self.layout_bottom = QVBoxLayout()
        layout.addLayout(self.layout_bottom)
        self.bottomLayout()

        layout.addStretch(0)

        if len(self.inp_recordInputs) < 1:
            return None

        for key in self.inp_recordInputs[autoFocus]:
            if not self.inp_recordInputs[autoFocus][key].text() in ("", "0"):
                QTimer.singleShot(0, self.inp_recordInputs[autoFocus][key], self.inp_recordInputs[autoFocus][key].setFocus)
                QTimer.singleShot(0, self.inp_recordInputs[autoFocus][key], self.inp_recordInputs[autoFocus][key].setCursorPosition(len(self.inp_recordInputs[autoFocus][key].text())))
                break

    def topLayout(self):
        self.layout_top.addWidget(tpl.getLabel(f"Profile: {Profile.getShortProfile()}"))

        button = QPushButton("Done")
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button.clicked.connect(self.done)
        self.layout_top.addWidget(button)

    def bottomLayout(self):
        self.inp_newInput = {}

        self.layout_bottom.addLayout(self._getHeader())

        for layout in self._getRows():
            self.layout_bottom.addLayout(layout)

        self.layout_bottom.addLayout(self._getInputRow())

    def _getHeader(self):
        row = QHBoxLayout()
        for key in Profile.voiceCommandsTemplate:
            label = tpl.getLabel(key, (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
            row.addWidget(label, {str: 4, int: 1}[Profile.voiceCommandsTemplate[key]])

        return row

    def _getRows(self):
        def lineEdited(element, key, index, value):
            if key in "command":
                element.setText("".join(char for char in tuple(value.lower()) if char.isalnum() or char.isspace()))

            record = {key: Profile.voiceCommandsTemplate[key](self.inp_recordInputs[index][key].text()) for key in Profile.voiceCommandsTemplate}

            if record == {key: Profile.voiceCommandsTemplate[key]() for key in Profile.voiceCommandsTemplate}:
                Profile.delCommand(index)
                self.win.setCentralWidget(VCProfileWidget(self.win))
                return None

            Profile.setCommand(index, record)

        rows = []
        for index, record in enumerate(Profile.get()["voiceCommands"]):
            row = QHBoxLayout()
            allLineEdits = {}
            for key in Profile.voiceCommandsTemplate:
                if Profile.voiceCommandsTemplate[key] is str:
                    inp = QLineEdit(record[key])
                    row.addWidget(inp, 4)

                elif Profile.voiceCommandsTemplate[key] is int:
                    inp = QSpinBox()
                    inp.setValue(record[key])
                    inp.setRange(0, 10)
                    row.addWidget(inp, 1)

                inp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                inp.textChanged.connect(lambda value, element=inp, key=key, index=index: lineEdited(element, key, index, value))
                allLineEdits[key] = inp

            self.inp_recordInputs.append(allLineEdits)
            rows.append(row)

        return rows

    def _getInputRow(self):
        def lineEdited():
            Profile.addCommand({key: Profile.voiceCommandsTemplate[key](self.inp_newInput[key].text()) for key in Profile.voiceCommandsTemplate})
            self.win.setCentralWidget(VCProfileWidget(self.win, autoFocus=-1))

        row = QHBoxLayout()
        for key in Profile.voiceCommandsTemplate:
            if Profile.voiceCommandsTemplate[key] is str:
                inp = QLineEdit()
                row.addWidget(inp, 4)

            elif Profile.voiceCommandsTemplate[key] is int:
                inp = QSpinBox()
                inp.setRange(0, 10)
                row.addWidget(inp, 1)

            inp.textChanged.connect(lineEdited)
            inp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            self.inp_newInput[key] = inp

        return row

    def done(self):
        self.win.setCentralWidget(VCHomeWidget(self.win))
        self.engine.updateProfile()


if __name__ == "__main__":
    VCEngine().main()
