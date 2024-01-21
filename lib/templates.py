from PySide6.QtWidgets import QComboBox, QFrame, QLabel, QPushButton, QSizePolicy, QSpinBox, QTextBrowser, QTextEdit


def getLabel(text: str, sizePolicy: (QSizePolicy.Policy, QSizePolicy.Policy) = (QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)):
    label = QLabel(text)
    label.setSizePolicy(*sizePolicy)

    return label


def getButton(text: str, connect: object = lambda: None, sizePolicy: (QSizePolicy.Policy, QSizePolicy.Policy) = (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)):
    button = QPushButton(text)
    button.setSizePolicy(*sizePolicy)
    button.clicked.connect(connect)

    return button


def getComboBox(items: list | tuple, current: str = "", connect: object = lambda: None, sizePolicy: (QSizePolicy.Policy, QSizePolicy.Policy) = (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)):
    combo = QComboBox()
    combo.setSizePolicy(*sizePolicy)
    combo.addItems(items)

    index = combo.findText(current)
    index = 0 if index < 0 and combo.count() > 0 else index
    if index > -1:
        combo.setCurrentIndex(index)

    combo.currentIndexChanged.connect(connect)

    return combo


def getTextBrowser(text, sizePolicy: (QSizePolicy.Policy, QSizePolicy.Policy) = (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)):
    textbrowser = QTextBrowser()
    textbrowser.setSizePolicy(*sizePolicy)
    textbrowser.setLineWrapMode(QTextEdit.NoWrap)
    textbrowser.insertHtml(text)

    return textbrowser


def getSpinBox(value: int, range: tuple, connect: object = lambda: None, sizePolicy: (QSizePolicy.Policy, QSizePolicy.Policy) = (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)):
    spinbox = QSpinBox()
    spinbox.setValue(value)
    spinbox.setRange(*range)
    spinbox.setSizePolicy(*sizePolicy)
    spinbox.textChanged.connect(connect)

    return spinbox


def getSpacer(shape: QFrame.Shape = QFrame.Shape.VLine):
    splitter = QFrame()
    splitter.setMinimumWidth(10)
    splitter.setLineWidth(2)
    splitter.setFrameShape(shape)

    return splitter
