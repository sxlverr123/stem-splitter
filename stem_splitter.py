import os
import sys
import subprocess
import threading
import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox

import numpy as np

try:
    import customtkinter as ctk
except ImportError:
    import tkinter
    _root = tkinter.Tk()
    _root.withdraw()
    messagebox.showerror("Missing dependency",
                         "customtkinter is not installed.\nRun install.bat first.")
    sys.exit(1)

try:
    import soundfile as sf
    from scipy.signal import butter, sosfiltfilt
except ImportError:
    sf = None

# Folder where this script lives (the output folder is created here)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

# Audio processing

def run_demucs(audio_path: Path, out_dir: Path, six_stems: bool, log):
    """Runs Demucs (AI) and returns the folder that contains the stems."""
    model = "htdemucs_6s" if six_stems else "htdemucs"
    py = sys.executable
    if py.lower().endswith("pythonw.exe"):  # started by double-click (no console)
        py = py[:-len("pythonw.exe")] + "python.exe"
    cmd = [py, "-m", "demucs", "-n", model, "-o", str(out_dir),
           "--float32", str(audio_path)]
    log(f"Starting AI separation ({model})... this can take a few minutes.")
    flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace",
                            creationflags=flags)
    for line in proc.stdout:
        line = line.strip()
        if line:
            log(line[-110:])
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError("Demucs failed. Make sure demucs, torch and FFmpeg "
                           "are installed.")
    stem_dir = out_dir / model / audio_path.stem
    if not stem_dir.exists():
        raise RuntimeError("Stem folder not found.")
    return stem_dir


def _filter(data, sr, kind, freq):
    sos = butter(4, freq, btype=kind, fs=sr, output="sos")
    return sosfiltfilt(sos, data, axis=0)


def split_drums(drums_path: Path, out_dir: Path, log):
    """Splits the drums into kick / snare / hats using frequency filters."""
    data, sr = sf.read(str(drums_path), always_2d=True)
    log("Splitting drums into kick, snare, hats...")
    kick = _filter(data, sr, "lowpass", 150)
    hats = _filter(data, sr, "highpass", 6000)
    snare = _filter(_filter(data, sr, "highpass", 150), sr, "lowpass", 5000)
    paths = {}
    for name, sig in (("kick", kick), ("snare", snare), ("hats", hats)):
        p = out_dir / f"{name}.wav"
        sf.write(str(p), np.clip(sig, -1, 1), sr, subtype="PCM_24")
        paths[name] = p
        log(f"Saved {p.name}")
    return paths


def save_wav(src: Path, dst: Path):
    data, sr = sf.read(str(src), always_2d=True)
    sf.write(str(dst), np.clip(data, -1, 1), sr, subtype="PCM_24")


# MIDI

def drum_to_midi(wav_path: Path, note: int, pm, name: str):
    import librosa
    import pretty_midi
    y, sr = librosa.load(str(wav_path), sr=22050, mono=True)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, units="time", backtrack=False)
    env = librosa.feature.rms(y=y)[0]
    inst = pretty_midi.Instrument(program=0, is_drum=True, name=name)
    for t in onsets:
        idx = min(int(t * sr / 512), len(env) - 1)
        vel = int(np.clip(env[idx] / (env.max() + 1e-9) * 127 * 1.3, 40, 127))
        inst.notes.append(pretty_midi.Note(vel, note, float(t), float(t) + 0.1))
    pm.instruments.append(inst)


def melody_to_midi(wav_path: Path, pm, name: str, fmin: str, fmax: str, program=0):
    """Extracts a monophonic line (808 / vocal) and converts it to MIDI notes."""
    import librosa
    import pretty_midi
    y, sr = librosa.load(str(wav_path), sr=22050, mono=True)
    f0, voiced, _ = librosa.pyin(y, fmin=librosa.note_to_hz(fmin),
                                 fmax=librosa.note_to_hz(fmax), sr=sr)
    times = librosa.times_like(f0, sr=sr)
    inst = pretty_midi.Instrument(program=program, name=name)
    cur, start = None, 0.0
    for t, f, v in zip(times, f0, voiced):
        note = int(round(librosa.hz_to_midi(f))) if v and not np.isnan(f) else None
        if note != cur:
            if cur is not None and t - start > 0.06:
                inst.notes.append(pretty_midi.Note(100, cur, float(start), float(t)))
            cur, start = note, t
    pm.instruments.append(inst)


def export_midi(stems: dict, out_dir: Path, bpm_hint, log):
    import librosa
    import pretty_midi
    ref = stems.get("drums") or next(iter(stems.values()))
    y, sr = librosa.load(str(ref), sr=22050, mono=True)
    tempo = float(np.atleast_1d(librosa.beat.beat_track(y=y, sr=sr)[0])[0])
    tempo = bpm_hint or tempo
    log(f"BPM: {tempo:.1f}")
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)

    if "kick" in stems:
        log("MIDI: kick..."); drum_to_midi(stems["kick"], 36, pm, "Kick")
    if "snare" in stems:
        log("MIDI: snare..."); drum_to_midi(stems["snare"], 38, pm, "Snare")
    if "hats" in stems:
        log("MIDI: hats..."); drum_to_midi(stems["hats"], 42, pm, "Hats")
    if "bass" in stems:
        log("MIDI: 808 / bass..."); melody_to_midi(stems["bass"], pm, "808", "C1", "C4", 38)
    if "vocals" in stems:
        log("MIDI: vocal melody..."); melody_to_midi(stems["vocals"], pm, "Vocal", "C3", "C6", 54)
    out = out_dir / "recreation.mid"
    pm.write(str(out))
    log(f"Created {out.name} (drag it into FL Studio: each track becomes a channel).")


# Full pipeline

def output_folder_for(audio_file) -> Path:
    return BASE_DIR / f"{Path(audio_file).stem}_FL_stems"


def process(audio_file, mode, six_stems, split_drums_opt, bpm, log):
    audio = Path(audio_file)
    out_dir = output_folder_for(audio)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        stem_dir = run_demucs(audio, Path(tmp), six_stems, log)
        names = {"vocals": "vocals", "bass": "808_bass", "drums": "drums",
                 "other": "other_melodies", "piano": "piano", "guitar": "guitar"}
        stems = {}
        for f in stem_dir.glob("*.wav"):
            dst = out_dir / f"{names.get(f.stem, f.stem)}.wav"
            save_wav(f, dst)
            stems[f.stem] = dst
            log(f"Saved {dst.name}")

        if split_drums_opt and "drums" in stems:
            stems.update(split_drums(stems["drums"], out_dir, log))

    if mode == "midi":
        export_midi(stems, out_dir, bpm, log)

    log(f"DONE! Files saved in: {out_dir}")
    return out_dir


def open_folder(path: Path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])


# Modern GUI (CustomTkinter)

ACCENT = "#7c5cff"
ACCENT_HOVER = "#6a49f0"
CARD = ("#ececf3", "#1b1b26")
BG = ("#f6f6fb", "#12121a")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Stem Splitter for FL Studio")
        self.geometry("720x800")
        self.minsize(660, 740)
        self.configure(fg_color=BG)

        self.file_path = None
        self.result_dir = None

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(26, 10))
        ctk.CTkLabel(header, text="Stem Splitter",
                     font=ctk.CTkFont(size=30, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header, text="AI-powered audio separation for FL Studio",
                     font=ctk.CTkFont(size=14), text_color=("gray35", "gray65")
                     ).pack(anchor="w")

        # Card 1: audio file
        c1 = self.card("1  ·  Audio file")
        row = ctk.CTkFrame(c1, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 6))
        self.file_label = ctk.CTkLabel(
            row, text="No file selected", anchor="w",
            text_color=("gray40", "gray60"), font=ctk.CTkFont(size=13))
        self.file_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(row, text="Browse", width=110, height=34, corner_radius=10,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self.pick_file).pack(side="right")
        self.out_label = ctk.CTkLabel(
            c1, text=f"Output folder will be created in:  {BASE_DIR}",
            anchor="w", justify="left", wraplength=620,
            text_color=("gray40", "gray55"), font=ctk.CTkFont(size=11))
        self.out_label.pack(fill="x", padx=18, pady=(0, 14))

        # Card 2: mode
        c2 = self.card("2  ·  Mode")
        self.mode_btn = ctk.CTkSegmentedButton(
            c2, values=["Stems only", "Stems + MIDI"], height=36,
            selected_color=ACCENT, selected_hover_color=ACCENT_HOVER)
        self.mode_btn.set("Stems only")
        self.mode_btn.pack(fill="x", padx=18, pady=(0, 14))

        # Card 3: options
        c3 = self.card("3  ·  Options")
        self.six_switch = ctk.CTkSwitch(
            c3, text="6-stem model (adds piano and guitar)", progress_color=ACCENT)
        self.six_switch.select()
        self.six_switch.pack(anchor="w", padx=18, pady=4)
        self.drums_switch = ctk.CTkSwitch(
            c3, text="Split drums into kick / snare / hats", progress_color=ACCENT)
        self.drums_switch.select()
        self.drums_switch.pack(anchor="w", padx=18, pady=4)
        bpm_row = ctk.CTkFrame(c3, fg_color="transparent")
        bpm_row.pack(fill="x", padx=18, pady=(6, 14))
        ctk.CTkLabel(bpm_row, text="BPM (MIDI mode)").pack(side="left")
        self.bpm_entry = ctk.CTkEntry(bpm_row, width=90, placeholder_text="Auto",
                                      corner_radius=10)
        self.bpm_entry.pack(side="left", padx=10)

        # Action
        self.run_btn = ctk.CTkButton(
            self, text="Split audio", height=48, corner_radius=14,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self.start)
        self.run_btn.pack(fill="x", padx=28, pady=(14, 8))

        self.progress = ctk.CTkProgressBar(self, mode="indeterminate",
                                           progress_color=ACCENT, height=8)
        self.progress.pack(fill="x", padx=28)
        self.progress.set(0)

        self.status = ctk.CTkLabel(self, text="Ready", anchor="w",
                                   text_color=("gray35", "gray65"))
        self.status.pack(fill="x", padx=30, pady=(6, 4))

        # Log
        self.log_box = ctk.CTkTextbox(
            self, height=150, corner_radius=12, fg_color=CARD,
            font=ctk.CTkFont(family="Consolas", size=12), state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=28, pady=(0, 10))

        self.open_btn = ctk.CTkButton(
            self, text="Open output folder", height=36, corner_radius=10,
            fg_color="transparent", border_width=1, border_color=ACCENT,
            text_color=("gray10", "gray90"), hover_color=("gray80", "gray25"),
            command=self.open_result)
        # shown only after a successful run

    # helpers
    def card(self, title):
        frame = ctk.CTkFrame(self, corner_radius=16, fg_color=CARD)
        frame.pack(fill="x", padx=28, pady=7)
        ctk.CTkLabel(frame, text=title, anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(fill="x", padx=18, pady=(14, 8))
        return frame

    def pick_file(self):
        p = filedialog.askopenfilename(
            title="Select an audio file",
            filetypes=[("Audio files", "*.mp3 *.wav *.flac *.m4a *.ogg *.aac"),
                       ("All files", "*.*")])
        if p:
            self.file_path = p
            self.file_label.configure(text=Path(p).name,
                                      text_color=("gray10", "gray95"))
            self.out_label.configure(
                text=f"Output folder:  {output_folder_for(p)}")

    def log(self, msg):
        def _w():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _w)

    def set_status(self, text):
        self.after(0, lambda: self.status.configure(text=text))

    def open_result(self):
        if self.result_dir:
            open_folder(self.result_dir)

    # run
    def start(self):
        if not self.file_path or not Path(self.file_path).exists():
            messagebox.showwarning("No file", "Please select an audio file first.")
            return
        if sf is None:
            messagebox.showerror("Missing libraries",
                                 "Run:  pip install soundfile scipy numpy")
            return
        txt = self.bpm_entry.get().strip()
        try:
            bpm = float(txt) if txt else None
        except ValueError:
            messagebox.showwarning("BPM", "BPM must be a number.")
            return

        self.open_btn.pack_forget()
        self.run_btn.configure(state="disabled", text="Working...")
        self.progress.configure(mode="indeterminate")
        self.progress.start()
        self.set_status("Processing...")
        mode = "midi" if self.mode_btn.get() == "Stems + MIDI" else "stem"
        args = (mode, bool(self.six_switch.get()), bool(self.drums_switch.get()), bpm)
        threading.Thread(target=self.worker, args=args, daemon=True).start()

    def worker(self, mode, six, drums, bpm):
        try:
            out = process(self.file_path, mode, six, drums, bpm, self.log)
            self.result_dir = out
            self.set_status("Done ✔")
            self.after(0, lambda: self.open_btn.pack(fill="x", padx=28, pady=(0, 20)))
        except Exception as e:
            self.log(f"ERROR: {e}")
            self.set_status("Error")
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            def _end():
                self.progress.stop()
                self.progress.set(0)
                self.run_btn.configure(state="normal", text="Split audio")
            self.after(0, _end)


if __name__ == "__main__":
    App().mainloop()
