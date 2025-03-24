from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "json", 
        "logging", 
        "zk", 
        "tqdm",
       "tkinter",
        "tkinter.filedialog",
        "tkinter.messagebox"
    ],
    "include_files": [],
    "excludes": [
        "unittest", 
        "email", 
        "http", 
        "xml",
        "IPython",
        "dask",
        "matplotlib",
        "numpy",
        "pandas",
        "requests",
        "setuptools_scm",
        "slack_sdk",
        "tensorflow"
    ],
    "include_msvcr": True,  # Include Visual C++ runtime
    "optimize": 2
}

setup(
    name="KupalDownloader",
    version="1.0",
    description="ZKTeco Fingerprint Data Tool",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": {
            "add_to_path": False,
            "initial_target_dir": r"[ProgramFilesFolder]\KupalDownloader"
        }
    },
    executables=[
        Executable(
            "kupaldownloader.py",
            base="Win32GUI",
            target_name="KupalDownloader.exe",
            icon="fingerprint.ico"  # Optional: Add your own icon
        )
    ]
)
