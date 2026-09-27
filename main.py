from __future__ import annotations

import mimetypes
import os
import shutil
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from yt_dlp import YoutubeDL

KV = r'''
#:import dp kivy.metrics.dp

<FlatButton@Button>:
    background_normal: ''
    background_down: ''
    background_color: (0, 0, 0, 0)
    color: app.WHITE
    bold: True
    font_size: '14sp'

<MainRoot>:
    orientation: 'vertical'
    padding: dp(20)
    spacing: dp(14)
    canvas.before:
        Color:
            rgba: app.BG
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(54)
        spacing: dp(12)
        canvas.before:
            Color:
                rgba: app.SURFACE
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(16), dp(16), dp(16), dp(16)]
        Label:
            text: 'LINKDROP'
            color: app.BLACK
            bold: True
            font_size: '20sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            padding_x: dp(16)
        Label:
            text: 'SOCIAL DOWNLOADER'
            color: app.PURPLE
            bold: True
            font_size: '10sp'
            halign: 'right'
            valign: 'middle'
            text_size: self.size
            padding_right: dp(16)

    Label:
        text: 'Paste a public link from TikTok, Instagram, Facebook and other yt-dlp supported sites.'
        color: app.MUTED
        font_size: '13sp'
        size_hint_y: None
        height: dp(46)
        text_size: self.width, None
        halign: 'left'
        valign: 'middle'

    BoxLayout:
        size_hint_y: None
        height: dp(58)
        spacing: dp(8)
        padding: dp(6)
        canvas.before:
            Color:
                rgba: app.WHITE
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(14), dp(14), dp(14), dp(14)]
            Color:
                rgba: app.BORDER
            Line:
                rounded_rectangle: self.x, self.y, self.width, self.height, dp(14)
                width: 1.0
        TextInput:
            id: url_input
            hint_text: 'Paste URL here'
            hint_text_color: app.MUTED
            foreground_color: app.BLACK
            background_color: (0, 0, 0, 0)
            cursor_color: app.BLUE
            multiline: False
            font_size: '14sp'
            padding: dp(10), dp(11)
            on_text_validate: root.analyze_url()
        FlatButton:
            text: 'PASTE'
            color: app.BLUE
            size_hint_x: None
            width: dp(70)
            on_release: root.paste_url()

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(10)
        FlatButton:
            text: 'ANALYZE'
            canvas.before:
                Color:
                    rgba: app.BLUE
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(12), dp(12), dp(12), dp(12)]
            on_release: root.analyze_url()
        FlatButton:
            text: 'DOWNLOAD'
            disabled: root.busy
            canvas.before:
                Color:
                    rgba: (app.PURPLE[0], app.PURPLE[1], app.PURPLE[2], 0.45 if self.disabled else 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(12), dp(12), dp(12), dp(12)]
            on_release: root.download_url()

    BoxLayout:
        size_hint_y: None
        height: dp(122)
        orientation: 'vertical'
        padding: dp(14)
        spacing: dp(7)
        canvas.before:
            Color:
                rgba: app.WHITE
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(16), dp(16), dp(16), dp(16)]
            Color:
                rgba: app.BORDER
            Line:
                rounded_rectangle: self.x, self.y, self.width, self.height, dp(16)
                width: 1.0
        Label:
            text: root.status_title
            color: app.BLACK
            bold: True
            font_size: '15sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
        Label:
            text: root.status_detail
            color: app.MUTED
            font_size: '12sp'
            halign: 'left'
            valign: 'top'
            text_size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(76)
        orientation: 'vertical'
        spacing: dp(7)
        ProgressBar:
            id: progress
            max: 100
            value: 0
        Label:
            text: root.progress_text
            color: app.MUTED
            font_size: '11sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size

    Widget:

    Label:
        text: 'Downloads are saved to your Android Downloads folder.'
        color: app.MUTED
        font_size: '11sp'
        size_hint_y: None
        height: dp(24)
        halign: 'center'
        valign: 'middle'
        text_size: self.size

    Label:
        text: 'Use only content you have permission to download.'
        color: app.MUTED
        font_size: '10sp'
        size_hint_y: None
        height: dp(24)
        halign: 'center'
        valign: 'middle'
        text_size: self.size
'''

Builder.load_string(KV)


class MainRoot(BoxLayout):
    status_title = StringProperty('READY')
    status_detail = StringProperty('Paste a link and tap ANALYZE.')
    progress_text = StringProperty('Idle')
    busy = BooleanProperty(False)

    def paste_url(self) -> None:
        text = Clipboard.paste() or ''
        if text:
            self.ids.url_input.text = text.strip()
            self.analyze_url()

    @staticmethod
    def _valid_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
            return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
        except Exception:
            return False

    def analyze_url(self) -> None:
        if self.busy:
            return
        url = self.ids.url_input.text.strip()
        if not self._valid_url(url):
            self._set_status('INVALID LINK', 'Enter a full http:// or https:// URL.')
            return
        self.busy = True
        self._set_status('ANALYZING', 'Checking the link…')
        self.progress_text = 'Please wait'
        threading.Thread(target=self._analyze_worker, args=(url,), daemon=True).start()

    def _analyze_worker(self, url: str) -> None:
        try:
            opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'noplaylist': False,
            }
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            entries = info.get('entries')
            if entries:
                entries = [entry for entry in entries if entry]
                first = entries[0] if entries else info
                count = len(entries)
                kind = first.get('extractor_key') or first.get('extractor') or '-'
                uploader = first.get('uploader') or first.get('channel') or '-'
                title = first.get('title') or first.get('description') or '-'
                detail = f'{kind} • {count} item(s) • {uploader}\n{title.splitlines()[0][:100]}'
            else:
                kind = info.get('extractor_key') or info.get('extractor') or '-'
                uploader = info.get('uploader') or info.get('channel') or '-'
                title = info.get('title') or info.get('description') or '-'
                detail = f'{kind} • {uploader}\n{title.splitlines()[0][:100]}'
                duration = info.get('duration')
                if duration:
                    detail += f' • {int(duration)}s'

            Clock.schedule_once(lambda _dt: self._analysis_done(detail), 0)
        except Exception as exc:
            msg = _clean_error(str(exc))
            Clock.schedule_once(lambda _dt, m=msg: self._analysis_error(m), 0)

    def _analysis_done(self, detail: str) -> None:
        self.busy = False
        self.status_title = 'LINK READY'
        self.status_detail = detail
        self.progress_text = 'Ready to download'
        self.ids.progress.value = 0

    def _analysis_error(self, message: str) -> None:
        self.busy = False
        self._set_status('ANALYZE FAILED', message)
        self.progress_text = 'Idle'

    def download_url(self) -> None:
        if self.busy:
            return
        url = self.ids.url_input.text.strip()
        if not self._valid_url(url):
            self._set_status('INVALID LINK', 'Enter a full http:// or https:// URL.')
            return
        self.busy = True
        self._set_status('DOWNLOADING', 'Starting download…')
        self.progress_text = '0%'
        self.ids.progress.value = 0
        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    def _download_worker(self, url: str) -> None:
        temp_root = Path(App.get_running_app().user_data_dir) / 'downloads'
        temp_root.mkdir(parents=True, exist_ok=True)
        session_dir = temp_root / str(int(time.time() * 1000))
        session_dir.mkdir(parents=True, exist_ok=True)
        finished_files: list[str] = []

        def hook(data: dict) -> None:
            status = data.get('status')
            if status == 'downloading':
                total = data.get('total_bytes') or data.get('total_bytes_estimate') or 0
                done = data.get('downloaded_bytes', 0) or 0
                pct = (done / total * 100) if total else 0
                filename = Path(data.get('filename', '')).name
                speed = data.get('speed') or 0
                eta = data.get('eta') or 0
                Clock.schedule_once(lambda _dt, p=pct, n=filename, s=speed, e=eta: self._progress(p, n, s, e), 0)
            elif status == 'finished':
                filename = data.get('filename')
                if filename and filename not in finished_files:
                    finished_files.append(filename)
                Clock.schedule_once(lambda _dt: self._status_only('FINALIZING', 'Saving the downloaded file…'), 0)

        opts = {
            'outtmpl': str(session_dir / '%(uploader,channel,id)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [hook],
            'format': 'best',
            'noplaylist': False,
            'restrictfilenames': True,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
        }

        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])

            files_to_save = []
            for item in sorted(session_dir.iterdir()):
                if item.is_file() and not item.name.endswith(('.part', '.ytdl')):
                    files_to_save.append(item)

            if not files_to_save:
                raise RuntimeError('The site did not return a downloadable file.')

            saved = 0
            for item in files_to_save:
                _save_to_android_downloads(item)
                saved += 1
                percent = saved / len(files_to_save) * 100
                Clock.schedule_once(lambda _dt, p=percent: self._progress(p, 'Saving files', 0, 0), 0)

            shutil.rmtree(session_dir, ignore_errors=True)
            Clock.schedule_once(lambda _dt, n=saved: self._download_done(n), 0)
        except Exception as exc:
            shutil.rmtree(session_dir, ignore_errors=True)
            msg = _clean_error(str(exc))
            Clock.schedule_once(lambda _dt, m=msg: self._download_error(m), 0)

    def _progress(self, pct: float, filename: str, speed: float, eta: int) -> None:
        self.ids.progress.value = max(0, min(100, pct))
        speed_text = _format_size(speed) + '/s' if speed else ''
        eta_text = f' • ETA {eta}s' if eta else ''
        self.status_title = 'DOWNLOADING'
        self.status_detail = filename[:85] if filename else 'Downloading…'
        self.progress_text = f'{pct:.1f}%{(" • " + speed_text) if speed_text else ""}{eta_text}'

    def _status_only(self, title: str, detail: str) -> None:
        self.status_title = title
        self.status_detail = detail

    def _set_status(self, title: str, detail: str) -> None:
        self.status_title = title
        self.status_detail = detail

    def _download_done(self, count: int) -> None:
        self.busy = False
        self.ids.progress.value = 100
        self.status_title = 'DONE'
        self.status_detail = f'{count} file(s) saved to Downloads.'
        self.progress_text = '100% complete'

    def _download_error(self, message: str) -> None:
        self.busy = False
        self.status_title = 'DOWNLOAD FAILED'
        self.status_detail = message
        self.progress_text = 'Idle'


class LinkDropApp(App):
    BG = (0.965, 0.970, 0.985, 1)
    SURFACE = (1, 1, 1, 1)
    WHITE = (1, 1, 1, 1)
    BLACK = (0.035, 0.045, 0.075, 1)
    MUTED = (0.38, 0.42, 0.50, 1)
    BLUE = (0.15, 0.38, 0.95, 1)
    PURPLE = (0.48, 0.25, 0.90, 1)
    BORDER = (0.84, 0.86, 0.91, 1)

    def on_start(self):
        # Android 9 and below require runtime permission for the public Downloads path.
        try:
            from jnius import autoclass
            from android.permissions import request_permissions
            BuildVersion = autoclass('android.os.Build$VERSION')
            if int(BuildVersion.SDK_INT) < 29:
                request_permissions(['android.permission.WRITE_EXTERNAL_STORAGE'])
        except Exception:
            pass

    def build(self):
        self.title = 'LinkDrop'
        return MainRoot()


def _format_size(value: float) -> str:
    if not value:
        return '0 B'
    size = float(value)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def _clean_error(message: str) -> str:
    message = message.replace('\n', ' ').strip()
    return message[:260] if message else 'Unknown error.'


def _save_to_android_downloads(source: Path) -> None:
    """Save a finished file to the system Downloads collection."""
    from jnius import autoclass

    BuildVersion = autoclass('android.os.Build$VERSION')
    if int(BuildVersion.SDK_INT) >= 29:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        ContentValues = autoclass('android.content.ContentValues')
        MediaStore = autoclass('android.provider.MediaStore')
        Environment = autoclass('android.os.Environment')

        activity = PythonActivity.mActivity
        resolver = activity.getContentResolver()
        values = ContentValues()
        name = _safe_filename(source.name)
        mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        values.put(MediaStore.MediaColumns.DISPLAY_NAME, name)
        values.put(MediaStore.MediaColumns.MIME_TYPE, mime)
        values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
        values.put(MediaStore.MediaColumns.IS_PENDING, 1)
        uri = resolver.insert(MediaStore.Downloads.getContentUri('external'), values)
        if uri is None:
            raise RuntimeError('Android could not create a Downloads entry.')
        try:
            output = resolver.openOutputStream(uri)
            if output is None:
                raise RuntimeError('Android could not open the Downloads file.')
            try:
                with source.open('rb') as infile:
                    while True:
                        chunk = infile.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)
                output.flush()
            finally:
                output.close()
            values.clear()
            values.put(MediaStore.MediaColumns.IS_PENDING, 0)
            resolver.update(uri, values, None, None)
        except Exception:
            # Do not leave a broken pending item in the Downloads database.
            try:
                resolver.delete(uri, None, None)
            except Exception:
                pass
            raise
        return

    # Android 6–9: public Downloads path, protected by the requested runtime permission.
    public_download = Path('/storage/emulated/0/Download')
    public_download.mkdir(parents=True, exist_ok=True)
    target = public_download / _safe_filename(source.name)
    shutil.copy2(source, target)


def _safe_filename(name: str) -> str:
    cleaned = ''.join(ch if ch not in '\\/:*?"<>|' else '_' for ch in name).strip()
    return cleaned or f'download_{int(time.time())}'


if __name__ == '__main__':
    LinkDropApp().run()
