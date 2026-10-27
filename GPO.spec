# -*- mode: python ; coding: utf-8 -*-
# Сборка: uv run pyinstaller GPO.spec --noconfirm --clean
#
# Рабочая БД app.db НЕ вшивается и не создаётся рядом с exe —
# она создаётся при первом запуске в %LOCALAPPDATA%\GPO (см. app/paths.py).
# cars.db (~3 ГБ) вшивается в сжатом виде (cars.zip, ~440 МБ) и один раз
# распаковывается в %LOCALAPPDATA%\GPO\cars.db при первом запуске (см. app/bundled_data.py).
# ВАЖНО: после изменения db/cars.db пересоберите cars.zip.
from pathlib import Path

ROOT = Path(SPECPATH)

datas = [
    # Небольшая база аналогов для автоподбора в «Судебной оценке».
    (str(ROOT / 'db' / 'sales.db'), 'db'),
    # Предгенерированные социально-экономические отчёты (окно «Анализ рынка»).
    (str(ROOT / 'kiril' / 'reports'), 'kiril/reports'),
    # Полная база аналогов cars.db в сжатом виде.
    (str(ROOT / 'cars.zip'), '.'),
]

a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'sqlalchemy.dialects.sqlite',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # dev-инструменты и тесты не нужны в exe
        'pytest',
        '_pytest',
        'basedpyright',
        'ruff',
        'app.services.valuation.tests',
        'tests',
        # тяжёлые необязательные зависимости pandas
        'matplotlib',
        'IPython',
        'notebook',
        'scipy',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GPO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
