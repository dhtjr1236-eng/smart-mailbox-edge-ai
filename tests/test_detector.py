import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from edge.detector import (Config, Pipeline, capture_image, main, run_gemini,
                           run_yolo, send_to_server, simulation_pipeline)


class DetectorTests(unittest.TestCase):
    def test_import_has_no_optional_dependency_or_hardware_side_effect(self):
        root = str(Path(__file__).resolve().parents[1])
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-c", "import sys; import edge.detector; "
                                     "assert not any(n in sys.modules for n in "
                                     "['cv2','requests','ultralytics','Jetson.GPIO','google.generativeai'])"],
                                    cwd=directory, env={**os.environ, "PYTHONPATH": root}, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_environment_config(self):
        config = Config.from_env({"MAILBOX_SERVER_URL": "http://host:8000/", "MAILBOX_CAMERA": "csi-pipeline",
                                  "MAILBOX_SENSOR_PIN": "13", "MAILBOX_MODEL_PATH": "custom.pt",
                                  "MAILBOX_CONFIDENCE": "0.8", "GEMINI_API_KEY": "test",
                                  "MAILBOX_GEMINI_MODEL": "configured-model", "MAILBOX_SAVE_DIR": "/tmp/test",
                                  "MAILBOX_TIMEOUT": "3"})
        self.assertEqual((config.server_url, config.camera, config.sensor_pin), ("http://host:8000", "csi-pipeline", 13))
        self.assertEqual((config.model_path, config.confidence, config.timeout), ("custom.pt", .8, 3))
        self.assertEqual(config.gemini_key, "test")

    def test_invalid_config(self):
        for env in ({"MAILBOX_CONFIDENCE": "nan"}, {"MAILBOX_CONFIDENCE": "1.1"},
                    {"MAILBOX_TIMEOUT": "0"}, {"MAILBOX_SERVER_URL": "file:///tmp"},
                    {"MAILBOX_SENSOR_PIN": "0"}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                Config.from_env(env)

    def test_capture_and_release(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(save_dir=Path(directory))
            cap = Mock()
            cap.read.return_value = (True, "frame")
            cv = Mock()
            cv.VideoCapture.return_value = cap
            path = capture_image(config, cv)
            cap.release.assert_called_once()
            cv.imwrite.assert_called_once_with(str(path), "frame")

    def test_capture_failures_release_camera(self):
        for opened, read_ok in ((False, True), (True, False)):
            with tempfile.TemporaryDirectory() as directory:
                cap = Mock()
                cap.isOpened.return_value = opened
                cap.read.return_value = (read_ok, None)
                cv = Mock()
                cv.VideoCapture.return_value = cap
                with self.assertRaises(RuntimeError):
                    capture_image(Config(save_dir=Path(directory)), cv)
                cap.release.assert_called_once()

    def test_write_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            cv = Mock()
            cv.VideoCapture.return_value.read.return_value = (True, "frame")
            cv.imwrite.return_value = False
            with self.assertRaises(RuntimeError):
                capture_image(Config(save_dir=Path(directory)), cv)

    def test_fake_model_selects_highest_confidence_and_empty(self):
        model = Mock(names={0: "object", 1: "other"})
        model.return_value = [SimpleNamespace(boxes=[SimpleNamespace(conf=.6, cls=0), SimpleNamespace(conf=.8, cls=1)])]
        self.assertEqual(run_yolo("image.jpg", model, .5), {"detected": True, "confidence": .8, "label": "other"})
        model.return_value = []
        self.assertFalse(run_yolo("image.jpg", model, .5)["detected"])

    def test_pipeline_fake_camera_model_server(self):
        capture = Mock(return_value="test.jpg")
        detect = Mock(return_value={"detected": True, "confidence": .6, "label": "fake"})
        analyze = Mock(return_value="analysis")
        send = Mock(return_value={"detection_id": 42})
        self.assertEqual(Pipeline(capture, detect, analyze, send).run(), {"detection_id": 42})
        detect.assert_called_once_with("test.jpg")
        send.assert_called_once_with("test.jpg", detect.return_value, "analysis")
        detect.return_value["confidence"] = .9
        analyze.reset_mock()
        Pipeline(capture, detect, analyze, send).run()
        analyze.assert_not_called()

    def test_pipeline_stops_on_capture_failure(self):
        detect, analyze, send = Mock(), Mock(), Mock()
        with self.assertRaises(RuntimeError):
            Pipeline(Mock(side_effect=RuntimeError()), detect, analyze, send).run()
        detect.assert_not_called()
        send.assert_not_called()

    def test_http_payload_and_closed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jpg"
            path.write_bytes(b"jpeg")
            http = Mock()
            http.post.return_value.json.return_value = {"detection_id": 7}
            result = send_to_server(path, {"detected": False, "confidence": 0, "label": ""}, "", Config(), http)
            self.assertEqual(result, {"detection_id": 7})
            args, kwargs = http.post.call_args
            self.assertTrue(args[0].endswith("/api/detections"))
            self.assertEqual(kwargs["data"]["detected"], "false")
            self.assertTrue(kwargs["data"]["timestamp"].endswith("+00:00"))
            self.assertTrue(kwargs["files"]["image"][1].closed)
            http.post.return_value.raise_for_status.side_effect = RuntimeError("HTTP error")
            with self.assertRaises(RuntimeError):
                send_to_server(path, {"detected": False, "confidence": 0, "label": ""}, "", Config(), http)

    def test_optional_analysis_failure(self):
        self.assertEqual(run_gemini("missing.jpg", None), "")
        self.assertEqual(run_gemini("missing.jpg", Mock()), "")

    def test_explicit_offline_simulation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jpg"
            path.write_bytes(b"\xff\xd8\xfftest")
            self.assertEqual(simulation_pipeline(Config(), path).run()["status"], "simulated")
            self.assertEqual(main(["--simulate", "--once", "--image", str(path)]), 0)
            path.write_bytes(b"bad")
            with self.assertRaises(ValueError):
                simulation_pipeline(Config(), path)


if __name__ == "__main__":
    unittest.main()
