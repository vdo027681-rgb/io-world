[app]
title = Io
package.name = io
package.domain = org.io
source.dir = .
source.include_exts = py,txt
version = 0.1.0

requirements = python3,kivy,numpy,requests

orientation = portrait

android.permissions = INTERNET
android.accept_license = True

android.api = 31
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
