import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from src.audio import AudioCapture
from src.transcriber import Transcriber


class SilenceTests(unittest.TestCase):
    def test_only_chunks_with_speech_are_dispatched(self):
        with patch.object(AudioCapture, '_init_device'):
            capture = AudioCapture()
        received = []
        clock = [0.0]

        def run_inline(**kwargs):
            return SimpleNamespace(start=lambda: kwargs['target'](*kwargs['args']))

        with patch.object(capture, 'is_available', return_value=True), \
                patch('src.audio.sd.InputStream') as stream, \
                patch('src.audio.time.time', side_effect=lambda: clock[0]), \
                patch('src.audio.threading.Thread', side_effect=run_inline):
            self.assertTrue(capture.start_recording(vad_callback=received.append))
            callback = stream.call_args.kwargs['callback']

            def feed(level, count):
                for _ in range(count):
                    clock[0] += capture.chunk_size / capture.sample_rate
                    callback(np.full((capture.chunk_size, 1), level, dtype=np.float32),
                             capture.chunk_size, None, None)

            # Nonzero room noise below the existing silence threshold.
            feed(0.001, 60)
            self.assertEqual(len(received), 0)
            feed(0.05, 8)
            feed(0.001, 20)
            self.assertEqual(len(received), 1)
            feed(0.001, 60)
            self.assertEqual(len(received), 1)
            capture.stop_recording()
            self.assertEqual(len(received), 1)

            # Restart and stopping mid-speech still flushes the final chunk.
            capture.start_recording(vad_callback=received.append)
            callback = stream.call_args.kwargs['callback']
            feed(0.05, 8)
            capture.stop_recording()
            self.assertEqual(len(received), 2)

    def test_swedish_annotations_are_filtered_but_speech_is_preserved(self):
        transcriber = Transcriber()
        transcriber.ready = True
        transcriber._model = Mock()
        examples = {
            '[Länk]': '',
            '[Lägg av film]': '',
            '[Till de senaste året]': '',
            '(sighs) [music]': '',
            'Här är en länk till filmen.': 'Här är en länk till filmen.',
            'Hej [Länk] världen.': 'Hej världen.',
            '[123]': '[123]',
        }
        for text, expected in examples.items():
            with self.subTest(text=text):
                transcriber._model.transcribe.return_value = [SimpleNamespace(text=text)]
                self.assertEqual(transcriber.transcribe(np.ones(1600, dtype=np.float32)),
                                 expected)


if __name__ == '__main__':
    unittest.main()
