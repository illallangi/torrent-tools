from setuptools import setup, find_packages

setup(
    name="torrent_tools",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "appdirs",
        "Click",
        "deluge_client",
        "loguru",
        "more_itertools",
        "requests_cache",
        "tqdm",
        "yarl",
    ],
    entry_points={
        "console_scripts": [
            "deluge-rename=torrent_tools.scripts.deluge_rename:cli",
            "ops-index=torrent_tools.scripts.ops_index:cli",
            "btn-index=torrent_tools.scripts.btn_index:cli",
        ],
    },
)
