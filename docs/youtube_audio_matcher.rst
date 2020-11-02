Python API
==========

The YouTube Audio Matcher Python API comprises the main
``youtube_audio_matcher`` package and three standalone submodules that handle
audio/fingerprinting functionality, mass download functionality, and
database functionality (:doc:`youtube_audio_matcher.audio`,
:doc:`youtube_audio_matcher.download`, and
:doc:`youtube_audio_matcher.database`, respectively). The main module, detailed
in the :ref:`main-module` section below, contains functions that tie the three
submodules together to download and fingerprint files, then add them to the
database or match them against the database.


Subpackages
-----------

.. toctree::
   :maxdepth: 2

   youtube_audio_matcher.audio
   youtube_audio_matcher.database
   youtube_audio_matcher.download

.. _main-module:

Module contents
---------------

.. automodule:: youtube_audio_matcher
   :members:
   :undoc-members:
   :show-inheritance:
