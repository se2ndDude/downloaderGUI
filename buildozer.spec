[app]
# (str) Title of your application
title = LinkDrop

# (str) Package name
package.name = linkdrop

# (str) Package domain (needed for android package name)
package.domain = com.linkdrop

# (str) Source code where main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,kv,txt,md

# (str) Application version
version = 1.0.0

# (str) Presplash / icon
icon.filename = %(source.dir)s/assets/icon.png

# (str) Supported Kivy/python dependencies
requirements = python3,kivy==2.3.1,yt-dlp==2026.8.19,pyjnius

# (str) Orientation (portrait is intentional for the simple mobile layout)
orientation = portrait
fullscreen = 0

# (str) Android settings
android.api = 35
android.minapi = 24
android.ndk_api = 24
android.enable_androidx = True
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a,x86_64
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE
android.allow_backup = False
android.private_storage = True

# (str) Build behavior
p4a.bootstrap = sdl2
p4a.branch = develop
p4a.commit = e772ad93f20a61c0bbe1cf8955e073cfb41062e1

[buildozer]
log_level = 2
warn_on_root = 1
