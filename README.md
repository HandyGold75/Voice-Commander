# Voice Commander

This program can be used to set up macros that will trigger after a voice command has been spoken.

## Configurations

The application can and should be configured to your needs and set up for the best experience.
Profiles can be used to set up different macros to easily switch between.

### Settings

* Microphone
  * Select a Microphone that will be listened to.
  * Note that some Microphones might not work or might even crash the application.
* Calibrate Microphone
  * While calibrating the microphone it will listen for surrounding noise to try and adjust noise levels for better recognition of when speech starts and stops.
* Phrase time
  * The maximum length a spoken phrase can have in seconds (0 to disable).
  * Note that when starting to talk the spoken phrase will be cut off after the selected time.
  * Also note that changing any settings only apply after an phrase ending is recognized and processed.
  * This can help if background noise stops the recognition of a phrase ending.
* Recognizer
  * Select the desired Speech Recognizer.
  * Please refer to the Speach Reconizers section for more details.

### Profiles

* Command
  * A voice command the program will listen for.
  * While a phrase can be configured sticking to single words will result in more stable recognition.
* Macro
  * A macro that will be executed when a voice command is recognized.
  * Any (series of) keys can be configured to be pressed like "H" or "Hello World" which would be typed out as if were manually typed.
  * Special keys can be configured by typing them out and splitting them with ";" from other parts like "enter" or "Hello;enter;World"
  * If the word of a special key is desired to be typed out instead of hitting the key it can be done by splitting the word up with ";" like "ent;er" or "Hello ent;er"
* Sensitivity
  * Determines if the whole spoken phrase needs to match (0), or if single words of a spoken phrase can match (1 and anything higher).
  * Sphinx uses this setting further, please refer to the Sphinx section for more details.

## Speach Reconizers

Different speech recognizers are available for use, these are explained in more detail.

All speech recognizers will work offline after they have downloaded their speech-to-text model, these will be automatically downloaded when selected.

### Vosk

Vosk will try to recognize all spoken phrases with accuracy. This causes Vosk to be quite accurate but might miss some speech.

Supports many different languages (OOTB only en-us and NL).

To add other languages or models go to the file reconizers.py in the class Vosk and add a record to the variable allModels containing `"Model name": ("Full Model Name", "Download URL")`.
At [Vosk Models](https://alphacephei.com/vosk/models) more models can be found. Models from other sources are also supported.

Vosk offers the following settings:

* Sensitivity
  * Determines if the whole spoken phrase needs to match (0), or if single words of a spoken phrase can match (1 and anything higher).
* Model
  * The Vosk model to use.
  * it is highly advised to use a small model.

### Whisper

Whisper should be used if Vosk isn't recognizing your voice enough.

Whisper will try to recognize all spoken phrases with confidence. This causes Wisper to be very likely to recognize something from your speech however this comes at a cost of accuracy as recognized phrases might differ just enough from to configured commands to not trigger the macros.

Supports many different languages. Also supports multiple languages sinuously (not recommended).

Whisper offers the following settings:

* Language
  * Determines which spoken language will be listened to.
* Model
  * The model size, bigger models will require more RAM and be slower but can recognize more.
  * It's advised to keep this at tiny.

### Sphinx

Sphinx should only be used as a last resort when Vosk and Whisper can't recognize your speech accurately enough.

Sphinx will only recognize phrases that are defined in the profile. This causes Sphinx to be very likely to trigger a macro, however, this comes at the cost that false positives are quite common.

Only supports the English language.

Sphinx offers the following settings:

* Sensitivity
  * Determines how easily a voice command is recognized.
  * Configured in the profile.

## Run from source

The package portaudio19-dev is required for PyAudio

```bash
git clone <URL>
cd ./Voice\ Commander
python3 -m pip install -r requirements.txt
python3 ./Voice\ Commander.py
```

If the following error ocures during the install of the pip requirements you will need to install portaudio19 or portaudio19-dev on your device: `ERROR: Could not build wheels for PyAudio, which is required to install pyproject.toml-based projects`
