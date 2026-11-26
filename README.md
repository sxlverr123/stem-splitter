# Stem Splitter for FL Studio

**AI-powered audio stem separation for FL Studio producers.**

Separate vocals, 808s, drums, melodies and more from your favorite audio tracks. Export individual WAV stems or generate an estimated MIDI recreation to take your production workflow to the next level.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9--3.12-blue?logo=python" />
  <img src="https://img.shields.io/badge/AI-Demucs-purple" />
  <img src="https://img.shields.io/badge/DAW-FL%20Studio-orange" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</p>

---

## Features

- **AI Stem Separation** – Powered by Meta's Demucs AI model.
- **4-Stem Separation** – Extract vocals, drums, bass (808) and other melodies.
- **Optional 6-Stem Model** – Additional piano and guitar separation.
- **Drum Separation** – Split drums into kick, snare and hi-hats.
- **MIDI Generation** – Generate an estimated MIDI recreation of the track.
- **Automatic BPM Detection** – Detect the song's tempo or enter it manually.
- **24-bit WAV Export** – High-quality audio files ready for FL Studio.
- **Modern GUI** – Dark-themed graphical interface, no terminal required after installation.
- **Automatic Output Folder** – Each song gets its own organized output folder.

## Interface

A simple workflow designed for music producers:

1. Load your audio file.
2. Select the separation mode.
3. Configure your preferred options.
4. Start the AI separation.
5. Import the resulting stems into FL Studio.

## Separation Modes

### 1. Stems Only

Separates the audio into individual WAV files.

### 2. Stems + MIDI

Performs stem separation and attempts to reconstruct musical elements as MIDI notes.

MIDI generation includes:
- Kick, snare and hi-hat onset detection.
- 808 bass pitch tracking.
- Vocal pitch tracking.
- Automatic BPM detection.

**Note:** MIDI reconstruction is an approximation and may require manual editing.

## Supported Audio Formats

- MP3
- WAV
- FLAC
- M4A
- Other formats supported by FFmpeg.

## ⚙️ Requirements

- Windows (for the included installer and launcher).
- Python 3.9 – 3.12.
- FFmpeg installed and added to PATH.
- NVIDIA GPU recommended.
- CPU-only processing supported.

## Installation (Windows)

### Step 1 – Install Python

Download Python 3.9 – 3.12:

https://www.python.org/downloads/

During installation, enable:

`Add python.exe to PATH`

### Step 2 – Download the Repository

Download or clone this repository.

Make sure these files are in the same folder:

```text
stem_splitter.py
install.bat
```

### Step 3 – Run the Installer

Double-click:

`install.bat`

The installer automatically sets up the required dependencies, including:

- PyTorch
- Torchaudio
- Demucs
- Librosa
- SoundFile
- SciPy
- NumPy
- Pretty MIDI
- CustomTkinter
- FFmpeg

### Step 4 – Launch the Application

The application opens with its graphical interface.

**First launch:** Demucs automatically downloads its AI models. An internet connection is required for this initial download.

## Manual Installation (Any OS)

Clone the repository:

```bash
git clone https://github.com/sxlverr123/stem-splitter.git
cd stem-splitter
```

Install the dependencies:

```bash
pip install "torch~=2.8.0" "torchaudio~=2.8.0" demucs soundfile scipy numpy librosa pretty_midi customtkinter
```

Make sure FFmpeg is installed and available in your system PATH.

Launch the application:

```bash
python stem_splitter.py
```

## How to Use

1. Launch Stem Splitter.
2. Click **Browse** and select your audio file.
3. Choose your preferred mode:
   - Stems Only
   - Stems + MIDI
4. Configure the available options:
   - 6-Stem Model
   - Drum Separation
   - Automatic or Manual BPM
5. Click **Split Audio**.
6. Wait for the separation process to finish.
7. Click **Open Output Folder**.

Your separated audio files are now ready to use!

## Output Structure

The application automatically creates a folder named after your original audio file.

Example:

```text
Stem Splitter/
│
├── stem_splitter_fl.py
│
└── my_song_FL_stems/
    │
    ├── vocals.wav
    ├── 808_bass.wav
    ├── drums.wav
    ├── kick.wav
    ├── snare.wav
    ├── hats.wav
    ├── other_melodies.wav
    │
    ├── piano.wav
    ├── guitar.wav
    │
    └── recreation.mid
```

**Note:**
- Piano and guitar are available with the optional 6-stem model.
- `recreation.mid` is generated only in Stems + MIDI mode.
- Drum subdivisions depend on the drum separation option.

## Using the Stems in FL Studio

Import your separated files directly into FL Studio.

**WAV Stems**
- Drag WAV files into the Playlist to arrange and mix them.
- Drag individual samples into the Channel Rack.
- Process each stem independently using your favorite plugins.

**MIDI File**
- Drag `recreation.mid` into FL Studio.
- Import the generated MIDI patterns.
- Assign instruments and plugins to the resulting channels.
- Edit notes, timing and velocity to refine the reconstruction.

## How It Works

### 1. AI Audio Separation

Demucs uses deep learning to separate an audio track into:

- Vocals
- Drums
- Bass
- Other

The optional 6-stem model provides additional piano and guitar separation.

### 2. Drum Frequency Separation

The drum stem can be divided using frequency-based filtering:

| Stem | Frequency Range |
|---|---|
| Kick | Below 150 Hz |
| Snare | 150 Hz – 5 kHz |
| Hi-Hats | Above 6 kHz |

These filters provide an approximate separation. Overlapping frequencies may cause audio bleed.

### 3. MIDI Reconstruction

When MIDI mode is enabled:

| Element | Detection Method |
|---|---|
| Kick | Onset Detection |
| Snare | Onset Detection |
| Hi-Hats | Onset Detection |
| 808 Bass | pYIN Pitch Tracking |
| Vocals | pYIN Pitch Tracking |

Detected pitches and onsets are converted into MIDI notes using Pretty MIDI.

## Limitations

- Drum separation is frequency-based and not a perfect instrument isolation process.
- Some kick, snare and hi-hat sounds may overlap.
- MIDI reconstruction is an estimation, not an exact transcription.
- Polyphonic instruments and chords may require significant manual cleanup.
- CPU-only processing can be considerably slower.
- Separation quality depends on the original recording and audio mix.

## Troubleshooting

| Problem | Possible Solution |
|---|---|
| Demucs failed | Check PyTorch, Demucs and FFmpeg installation. |
| MP3 files won't load | Make sure FFmpeg is installed and added to PATH. |
| Processing is too slow | Use an NVIDIA GPU or disable the 6-stem model. |
| Missing Python module | Run the pip installation command again. |
| Poor MIDI results | Manually correct notes, timing and velocity in FL Studio. |

## Roadmap

Planned improvements:

- [x] Separate toms, claps and crashes.
- [x] Batch processing for multiple audio files.
- [x] Reverb separation from vocals.
- [x] Improved MIDI reconstruction.
- [x] More advanced drum separation.
- [x] Additional stem export options.

## License

This project is released under the **MIT License**.

Demucs is developed by Meta Research and is distributed under its own MIT License.

## Copyright Notice

This software is intended for audio processing and music production.

Only process audio files that you own or have permission to use.

This project does not grant any rights to copyrighted material processed with the application.

---

<p align="center">
  **Made for FL Studio producers.**
</p>
