from setuptools import setup

setup(
    name="youtube-audio-matcher",
    version="0.6",
    url="https://github.com/nrsyed/youtube-audio-matcher",
    author="Najam R Syed",
    author_email="najam.r.syed@gmail.com",
    license="MIT",
    packages=["youtube_audio_matcher"],
    install_requires=[
        "bs4", "matplotlib", "numpy", "psycopg2", "pydub", "scipy", "selenium",
        "sqlalchemy", "youtube-dl",
    ],
    entry_points={
        "console_scripts": [
            "yamdl = youtube_audio_matcher.download.__main__:main",
            "yamfp = youtube_audio_matcher.audio.__main__:main"
        ],
    },
)
