from setuptools import setup

setup(
    name="youtube-audio-matcher",
    version="0.7",
    url="https://github.com/nrsyed/youtube-audio-matcher",
    author="Najam R Syed",
    author_email="najam.r.syed@gmail.com",
    license="MIT",
    packages=[
        "youtube_audio_matcher",
        "youtube_audio_matcher.audio",
        "youtube_audio_matcher.database",
        "youtube_audio_matcher.download",
    ],
    install_requires=[
        "bs4", "matplotlib", "numpy", "pydub", "scipy", "selenium",
        "sqlalchemy", "youtube-dl",
    ],
    entry_points={
        "console_scripts": [
            "yam = youtube_audio_matcher.__main__:cli",
            "yamdb = youtube_audio_matcher.database.__main__:cli",
            "yamdl = youtube_audio_matcher.download.__main__:cli",
            "yamfp = youtube_audio_matcher.audio.__main__:cli"
        ],
    },
)
