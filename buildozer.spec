[app]
p4a.branch = v2024.01.21

title = Io
package.name = io
package.domain = org.io
source.dir = .
source.include_exts = py,txt
version = 0.1.0

requirements = python3,kivy,numpy,requests

orientation = portrait

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE
android.accept_license = True

android.api = 31
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
