# logic/audio_listener.py

import time
import threading
import azure.cognitiveservices.speech as speechsdk
from config.settings import (
    AZURE_SPEECH_KEY,
    AZURE_SPEECH_REGION,
    ALLOWED_REGION
)


# ═══════════════════════════════════════════════════════
# CLASS 1 — System Audio Listener
# ═══════════════════════════════════════════════════════
class AudioListener:

    def __init__(self, on_recognized, on_recognizing, on_status):
        self._on_recognized  = on_recognized
        self._on_recognizing = on_recognizing
        self._on_status      = on_status
        self._recognizer     = None
        self._is_listening   = False

    def start(self):
        if self._is_listening:
            return
        threading.Thread(
            target = self._do_start,
            daemon = True
        ).start()

    def _do_start(self):
        try:
            speech_config = self._build_config()
            audio_config  = speechsdk.audio.AudioConfig(
                use_default_speaker_microphone = True
            )
            self._recognizer = speechsdk.SpeechRecognizer(
                speech_config = speech_config,
                audio_config  = audio_config
            )
            self._wire_events()
            self._recognizer\
                .start_continuous_recognition_async().get()
            self._is_listening = True
            self._on_status("🔊 System audio ON...")

        except Exception as ex:
            self._on_status(
                f"⚠️ System audio error: {str(ex)}"
            )
            self._is_listening = False

    def stop(self):
        if not self._is_listening:
            return
        threading.Thread(
            target = self._do_stop,
            daemon = True
        ).start()

    def _do_stop(self):
        try:
            if self._recognizer:
                self._recognizer\
                    .stop_continuous_recognition_async().get()
                self._recognizer.recognized.disconnect_all()
                self._recognizer.recognizing.disconnect_all()
                self._recognizer.canceled.disconnect_all()
                self._recognizer.session_stopped.disconnect_all()
                self._recognizer = None
            self._is_listening = False
            self._on_status("⏹️ System audio OFF.")
        except Exception as ex:
            self._on_status(f"⚠️ Stop error: {str(ex)}")
            self._is_listening = False

    def _build_config(self) -> speechsdk.SpeechConfig:
        cfg = speechsdk.SpeechConfig(
            subscription = AZURE_SPEECH_KEY,
            region       = AZURE_SPEECH_REGION
        )
        cfg.speech_recognition_language = ALLOWED_REGION
        cfg.set_property(
            speechsdk.PropertyId
            .Speech_SegmentationSilenceTimeoutMs,
            "2000"
        )
        cfg.set_property(
            speechsdk.PropertyId
            .SpeechServiceConnection_InitialSilenceTimeoutMs,
            "30000"
        )
        cfg.set_property(
            speechsdk.PropertyId
            .SpeechServiceConnection_EndSilenceTimeoutMs,
            "2000"
        )
        return cfg

    def _wire_events(self):
        self._recognizer.recognized.connect(
            self._handle_recognized
        )
        self._recognizer.recognizing.connect(
            self._handle_recognizing
        )
        self._recognizer.canceled.connect(
            self._handle_canceled
        )
        self._recognizer.session_stopped.connect(
            self._handle_stopped
        )

    def _handle_recognized(self, evt):
        if evt.result.reason == \
                speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip()
            if text:
                self._on_recognized(text)

    def _handle_recognizing(self, evt):
        text = evt.result.text.strip()
        if text:
            self._on_recognizing(text)

    def _handle_canceled(self, evt):
        details = evt.cancellation_details
        self._on_status(
            f"⚠️ System audio: {details.error_details}"
        )
        self._is_listening = False

    def _handle_stopped(self, evt):
        self._is_listening = False

    @property
    def is_listening(self) -> bool:
        return self._is_listening


# ═══════════════════════════════════════════════════════
# CLASS 2 — Mic Listener (reliable + auto-reconnect)
# ═══════════════════════════════════════════════════════
class MicListener:

    MAX_RETRIES    = 5
    RETRY_DELAY    = 3

    def __init__(self, on_recognized, on_recognizing, on_status):
        self._on_recognized  = on_recognized
        self._on_recognizing = on_recognizing
        self._on_status      = on_status
        self._recognizer     = None
        self._is_listening   = False
        self._should_run     = False
        self._retry_count    = 0
        self._lock           = threading.Lock()

    # ── Build Config — always fresh ───────────────────────────────────
    def _build_config(self) -> speechsdk.SpeechConfig:
        """
        Always build fresh config — no pre-init needed.
        This avoids the 'Mic not ready' race condition.
        """
        cfg = speechsdk.SpeechConfig(
            subscription = AZURE_SPEECH_KEY,
            region       = AZURE_SPEECH_REGION
        )
        cfg.speech_recognition_language = ALLOWED_REGION
        cfg.set_property(
            speechsdk.PropertyId
            .Speech_SegmentationSilenceTimeoutMs,
            "2000"
        )
        cfg.set_property(
            speechsdk.PropertyId
            .SpeechServiceConnection_InitialSilenceTimeoutMs,
            "30000"
        )
        cfg.set_property(
            speechsdk.PropertyId
            .SpeechServiceConnection_EndSilenceTimeoutMs,
            "2000"
        )
        return cfg

    # ── Start ─────────────────────────────────────────────────────────
    def start(self):
        with self._lock:
            self._should_run  = True
            self._retry_count = 0

        # ✅ Run in background thread — no pre-init wait
        threading.Thread(
            target = self._connect,
            daemon = True
        ).start()

    # ── Stop ──────────────────────────────────────────────────────────
    def stop(self):
        with self._lock:
            self._should_run = False

        threading.Thread(
            target = self._do_stop,
            daemon = True
        ).start()

    def _do_stop(self):
        try:
            self._is_listening = False
            if self._recognizer:
                try:
                    self._recognizer\
                        .stop_continuous_recognition_async().get()
                except Exception:
                    pass
                try:
                    self._recognizer.recognized.disconnect_all()
                    self._recognizer.recognizing.disconnect_all()
                    self._recognizer.canceled.disconnect_all()
                    self._recognizer\
                        .session_started.disconnect_all()
                    self._recognizer\
                        .session_stopped.disconnect_all()
                except Exception:
                    pass
                self._recognizer = None
            self._on_status("⏹️ Mic OFF.")
        except Exception as ex:
            self._on_status(f"⚠️ Mic stop error: {str(ex)}")
            self._is_listening = False
            self._recognizer   = None

    # ── Connect — builds everything fresh each time ───────────────────
    def _connect(self):
        with self._lock:
            if not self._should_run:
                return

        try:
            self._on_status("🎤 Connecting mic...")

            # ✅ Clean up old recognizer first
            self._cleanup_recognizer()

            # ✅ Build fresh config + recognizer every time
            speech_config    = self._build_config()
            audio_config     = speechsdk.audio.AudioConfig(
                use_default_microphone = True
            )
            self._recognizer = speechsdk.SpeechRecognizer(
                speech_config = speech_config,
                audio_config  = audio_config
            )

            # ✅ Wire events
            self._recognizer.recognized.connect(
                self._handle_recognized
            )
            self._recognizer.recognizing.connect(
                self._handle_recognizing
            )
            self._recognizer.canceled.connect(
                self._handle_canceled
            )
            self._recognizer.session_started.connect(
                self._handle_session_started
            )
            self._recognizer.session_stopped.connect(
                self._handle_session_stopped
            )

            # ✅ Start and wait for confirmation
            self._recognizer\
                .start_continuous_recognition_async().get()

            with self._lock:
                self._retry_count = 0

            self._is_listening = True
            self._on_status("🎤 Mic ON — speak now...")

        except Exception as ex:
            self._is_listening = False
            self._on_status(
                f"⚠️ Mic error: {str(ex)}"
            )
            self._schedule_reconnect(str(ex))

    # ── Cleanup old recognizer safely ─────────────────────────────────
    def _cleanup_recognizer(self):
        if self._recognizer:
            try:
                self._recognizer\
                    .stop_continuous_recognition_async().get()
            except Exception:
                pass
            try:
                self._recognizer.recognized.disconnect_all()
                self._recognizer.recognizing.disconnect_all()
                self._recognizer.canceled.disconnect_all()
                self._recognizer\
                    .session_started.disconnect_all()
                self._recognizer\
                    .session_stopped.disconnect_all()
            except Exception:
                pass
            self._recognizer = None

    # ── Auto Reconnect ────────────────────────────────────────────────
    def _schedule_reconnect(self, reason: str):
        with self._lock:
            if not self._should_run:
                return
            self._retry_count += 1
            count = self._retry_count

        if count > self.MAX_RETRIES:
            self._on_status(
                f"⚠️ Mic failed {self.MAX_RETRIES} times. "
                f"Click 🔄 Reset."
            )
            with self._lock:
                self._should_run = False
            return

        self._on_status(
            f"🔄 Reconnecting mic "
            f"({count}/{self.MAX_RETRIES})..."
        )

        threading.Thread(
            target = self._delayed_reconnect,
            daemon = True
        ).start()

    def _delayed_reconnect(self):
        time.sleep(self.RETRY_DELAY)
        with self._lock:
            if not self._should_run:
                return
        self._connect()

    # ── Reset — full clean slate ──────────────────────────────────────
    def reset(self):
        """Stop everything and prepare for fresh start"""
        with self._lock:
            self._should_run  = False
            self._retry_count = 0

        threading.Thread(
            target = self._do_reset,
            daemon = True
        ).start()

    def _do_reset(self):
        try:
            self._is_listening = False
            self._cleanup_recognizer()
            self._on_status("✅ Mic reset — ready.")
        except Exception as ex:
            self._on_status(
                f"⚠️ Mic reset error: {str(ex)}"
            )

    # ── Event Handlers ────────────────────────────────────────────────
    def _handle_session_started(self, evt):
        self._on_status("🎤 Mic active — speak now...")

    def _handle_session_stopped(self, evt):
        self._is_listening = False
        with self._lock:
            should = self._should_run
        if should:
            self._schedule_reconnect("session stopped")

    def _handle_recognized(self, evt):
        if evt.result.reason == \
                speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip()
            if text:
                self._on_recognized(text)

    def _handle_recognizing(self, evt):
        text = evt.result.text.strip()
        if text:
            self._on_recognizing(text)

    def _handle_canceled(self, evt):
        details    = evt.cancellation_details
        reason     = details.error_details or "Unknown"
        self._is_listening = False

        print(f"❌ Mic canceled: {reason}")

        if details.reason == speechsdk.CancellationReason.Error:
            retryable = (
                "connection", "network", "timeout",
                "websocket", "1006", "service",
                "unavailable", "unauthorized"
            )
            if any(e in reason.lower() for e in retryable):
                self._schedule_reconnect(reason)
            else:
                self._on_status(f"⚠️ Mic: {reason}")
                with self._lock:
                    self._should_run = False

    @property
    def is_listening(self) -> bool:
        return self._is_listening

    @property
    def is_ready(self) -> bool:
        return True   # ✅ always ready — config built on demand