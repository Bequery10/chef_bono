import sys
import time
from pathlib import Path

import cv2
import shutil


def _open_camera(camera_index: int) -> cv2.VideoCapture:
    """
    Open a camera capture in a reasonably compatible way.
    On macOS, CAP_AVFOUNDATION often works best if available.
    """
    if sys.platform == "darwin":
        cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
        if cap is not None and cap.isOpened():
            return cap

    cap = cv2.VideoCapture(camera_index)
    return cap


def capture_every_second(
    output_file_path: str = "recording_utils/current_image.jpg",
    camera_index: int = 0,
    interval_sec: float = 1.0,
    jpeg_quality: int = 95,
    png_compression: int = 3,
) -> None:
    """
    Captures one frame every `interval_sec` seconds and overwrites the same file.

    The write is "atomic": it writes to a temp image file with the same extension
    (e.g. current_image.tmp.jpg) then replaces the target, so readers don't see
    a partially written image.
    """
    import shutil

    output_path = Path(output_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # If target exists as a directory, remove it
    if output_path.exists() and output_path.is_dir():
        shutil.rmtree(output_path)

    # Also clean up any stray temp files
    tmp_pattern = output_path.with_name(output_path.stem + ".tmp*")
    for tmp_file in output_path.parent.glob(tmp_pattern.name):
        if tmp_file.exists():
            tmp_file.unlink()

    suffix = output_path.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        raise ValueError(
            f"Unsupported output extension '{output_path.suffix}'. Use .jpg, .jpeg, or .png"
        )

    cap = _open_camera(camera_index)
    if cap is None or not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}")

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print("Warning: failed to read frame; retrying...", flush=True)
                time.sleep(interval_sec)
                continue

            tmp_path = output_path.with_name(
                output_path.stem + ".tmp" + output_path.suffix
            )

            if suffix in {".jpg", ".jpeg"}:
                params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]
            else:
                params = [int(cv2.IMWRITE_PNG_COMPRESSION), int(png_compression)]

            wrote = cv2.imwrite(str(tmp_path), frame, params)
            if not wrote:
                raise RuntimeError(f"cv2.imwrite failed for {tmp_path}")

            tmp_path.replace(output_path)
            print(f"Updated {output_path}", flush=True)

            time.sleep(interval_sec)

    except KeyboardInterrupt:
        print("Stopping...", flush=True)
    finally:
        cap.release()


def capture_sharpest_frame(
    output_file_path: str = "recording_utils/current_image.jpg",
    camera_index: int = 0,
    num_frames: int = 5,
    jpeg_quality: int = 95,
    png_compression: int = 3,
) -> None:
    """
    Captures multiple frames and saves the sharpest (least blurry) one.
    Uses Laplacian variance to measure image sharpness.
    Higher variance = sharper image.
    """

    output_path = Path(output_file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # If target exists as a directory, remove it
    if output_path.exists() and output_path.is_dir():
        shutil.rmtree(output_path)

    suffix = output_path.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        raise ValueError(
            f"Unsupported output extension '{output_path.suffix}'. Use .jpg, .jpeg, or .png"
        )

    cap = _open_camera(camera_index)
    if cap is None or not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}")

    try:
        frames = []
        sharpness_scores = []

        # Capture num_frames frames
        for i in range(num_frames):
            ok, frame = cap.read()
            if not ok or frame is None:
                print(f"Warning: failed to read frame {i + 1}; retrying...", flush=True)
                continue

            # Calculate Laplacian variance (blur metric: higher = sharper)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            frames.append(frame)
            sharpness_scores.append(laplacian_var)
            print(f"Frame {i + 1} sharpness score: {laplacian_var:.2f}", flush=True)

        if not frames:
            raise RuntimeError("No frames captured")

        # Find the sharpest frame (highest Laplacian variance)
        sharpest_idx = sharpness_scores.index(max(sharpness_scores))
        sharpest_frame = frames[sharpest_idx]

        print(
            f"Selected frame {sharpest_idx + 1} as sharpest (score: {sharpness_scores[sharpest_idx]:.2f})",
            flush=True,
        )

        # Save the sharpest frame
        if suffix in {".jpg", ".jpeg"}:
            params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]
        else:
            params = [int(cv2.IMWRITE_PNG_COMPRESSION), int(png_compression)]

        wrote = cv2.imwrite(str(output_path), sharpest_frame, params)
        if not wrote:
            raise RuntimeError(f"cv2.imwrite failed for {output_path}")

        print(f"Saved sharpest frame to {output_path}", flush=True)

    finally:
        cap.release()


def start_recording(interval_sec: float = 1.0):
    capture_every_second(
        output_file_path="recording_utils/current_image.jpg",
        camera_index=0,
        interval_sec=interval_sec,
    )


def get_frame(path: str = "recording_utils/current_image.jpg") -> bytes:
    capture_sharpest_frame(
        output_file_path=path,
        camera_index=0,
        num_frames=5,
    )


if __name__ == "__main__":
    get_frame()
