import hashlib
import logging

import numpy as np
import pydub
import scipy.io.wavfile


def generate_waveform(
    shape="sine", duration=1, num_samples=None, sample_rate=44100,
    frequency=440, amplitude=1.0, duty_cycle=0.5, width=1, out_path=None
):
    """
    Generate an int16 waveform signal.

    Args:
        shape (str): {"sine", "sawtooth", "square"}
            Type of waveform to generate.
        duration (float): Duration of audio signal in seconds. If `num_samples`
            is provided, `duration` is ignored.
        num_samples (int): Number of samples to generate. If None, `duration`
            is used to compute the number of samples based on `sample_rate`.
        sample_rate (int): Audio signal sample rate in Hz.
        frequency (float): Audio signal frequency in Hz.
        amplitude (float): Amplitude as a fraction [0, 1] of the total range.
            Values are first computed as floats in the range [-1.0, 1.0], then
            scaled to the int16 range [-32768, 32767]. This argument
            effectively sets the volume of the generated audio signal as a
            fraction of maximum possible volume.
        duty_cycle (float): Duty cycle in the range [0, 1] for square wave.
            See `scipy.signal.square`_.
        width (float): Sawtooth wave width argument in the range [0, 1]. See
            `scipy.signal.sawtooth`_.
        out_path (str): Filepath to which the audio signal should be written as
            a WAV file. If None, file is not saved.

    Returns:
        np.ndarray: Array representing the audio signal.

    .. _`scipy.signal.square`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.square.html
    .. _`scipy.signal.sawtooth`:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sawtooth.html
    """
    if num_samples is None:
        num_samples = duration * sample_rate

    x = np.arange(num_samples)
    t = 2 * np.pi * frequency * x / sample_rate

    if shape == "sine":
        y = np.sin(t)
    elif shape == "square":
        y = scipy.signal.square(t, duty=duty_cycle)
    elif shape == "sawtooth":
        y = scipy.signal.sawtooth(t, width=width)

    # Scale y from float32 range to int16 range and convert to int16.
    amplitude = max(amplitude, 1.0)
    y = (amplitude * y * 32767).astype(np.int16)

    if out_path is not None:
        scipy.io.wavfile.write(out_path, sample_rate, y)
    return y


def hash_file(fpath, block_size=2**16):
    """
    Get the SHA1 hash of a file.

    Args:
        fpath (str): Path to file.
        block_size (int): Number of bytes to read from the file at a time.

    Returns:
        str: hash
            SHA1 digest as a hex string.
    """
    hash_ = hashlib.sha1()
    with open(fpath, "rb") as f:
        while (buf := f.read(block_size)):
            hash_.update(buf)
    return hash_.hexdigest()


def read_file(fpath, num_retries=3):
    """
    Read an audio file and extract audio information and file SHA1 hash.

    Args:
        fpath (str): Path to file.

    Returns:
        tuple: (channel_data, sample_rate, sha1_hash)
            - channel_data (List[np.ndarray]): Data for each audio channel.
            - sample_rate (int): Audio sample rate (samples per second).
            - sha1_hash (str): SHA1 hash of the file.

    .. note::
        Does not support 24-bit (use wavio for 24-bit files).
    """
    audio_seg = pydub.AudioSegment.from_file(fpath)
    raw_data = np.frombuffer(audio_seg.raw_data, np.int16)

    num_channels = audio_seg.channels
    channel_data = [raw_data[ch::num_channels] for ch in range(num_channels)]
    sample_rate = audio_seg.frame_rate
    filehash = hash_file(fpath)

    return channel_data, sample_rate, filehash
