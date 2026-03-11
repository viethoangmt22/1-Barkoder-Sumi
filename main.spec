# -*- mode: python ; coding: utf-8 -*-

# Spec file cho PyInstaller - build chương trình main.py
# Chạy lệnh:
#   pyinstaller main.spec
#
# Lưu ý:
# - Dùng onedir để config.json nằm cạnh file .exe, dễ sửa cho vận hành
# - Giữ console=True để xem log runtime (quan trọng khi debug COM/scan)

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# uiautomator2 có import động, collect_submodules để tránh thiếu module lúc chạy exe
hiddenimports = []
hiddenimports += collect_submodules("uiautomator2")

# Thêm thư viện thường đi kèm uiautomator2 trong runtime
# (an toàn hơn cho máy vận hành không có môi trường dev)
hiddenimports += collect_submodules("adbutils")
hiddenimports += collect_submodules("retry")

# uiautomator2 cần file data trong package (đặc biệt assets/u2.jar)
datas = []
datas += collect_data_files("uiautomator2")

# Giữ config runtime cạnh exe
datas += [
    ("config.json", "."),
]

# Thêm thư mục adb local để không phụ thuộc PATH hệ thống
# Bao gồm tất cả file trong thư mục adb/ (adb.exe, dll, v.v.)
import os
if os.path.exists("adb"):
    # Thêm toàn bộ thư mục adb vào build
    from glob import glob
    for item in glob("adb/*"):
        if os.path.isfile(item):
            datas += [(item, "adb")]


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="barkoder_auto",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="barkoder_auto",
)
