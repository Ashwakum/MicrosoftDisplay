    # build.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex        = ['.'],
    binaries      = [],
    datas         = [
        ('config',  'config'),    # ✅ include config folder
        ('ui',      'ui'),        # ✅ include ui folder
        ('logic',   'logic'),     # ✅ include logic folder
    ],
    hiddenimports = [
        'tkinter',
        'tkinterweb',
        'openai',
        'sounddevice',
        'azure.cognitiveservices.speech',
        'langdetect',
        'numpy',
        'win32gui',
        'win32con',
        'win32api',
    ],
    hookspath      = [],
    runtime_hooks  = [],
    excludes       = [],
    cipher         = block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name          = 'AIAssistant',     # ✅ your EXE name
    debug         = False,
    strip         = False,
    upx           = True,
    console       = False,             # ✅ no black terminal window
    onefile       = True,              # ✅ single EXE file
)