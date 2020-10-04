from setuptools import setup

setup(
    name="youtube-audio-matcher",
    version="0.5",
    url="https://github.com/nrsyed/youtube-audio-matcher",
    author="Najam R Syed",
    author_email="najam.r.syed@gmail.com",
    license="MIT",
    packages=["youtube_audio_matcher", "youtube_audio_matcher.download"],
    install_requires=["bs4", "selenium", "youtube-dl"],
    entry_points={
        "console_scripts": [
            "yamdl = youtube_audio_matcher.download.download:main"
        ],
    },
)
