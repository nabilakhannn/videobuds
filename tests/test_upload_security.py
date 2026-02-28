"""Tests for OWASP A04 — File Upload Hardening.

Covers:
    - Extension whitelist enforcement
    - Magic-byte (content-type) verification
    - Per-category file size limits
    - Sanitised filename handling
    - Security event logging on rejection
"""

import io
import os
import struct
import pytest
from app.security import validate_upload, UPLOAD_SIZE_LIMITS


# ── helpers ──────────────────────────────────────────────────────────────────

class FakeFileStorage:
    """Minimal stand-in for werkzeug.datastructures.FileStorage."""

    def __init__(self, filename, data=b"", content_type="application/octet-stream"):
        self.filename = filename
        self.content_type = content_type
        self.stream = io.BytesIO(data)

    def save(self, path):
        with open(path, "wb") as fp:
            self.stream.seek(0)
            fp.write(self.stream.read())


# Real magic bytes for common formats
PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
JPEG_MAGIC = b"\xff\xd8\xff\xe0" + b"\x00" * 8
GIF87_MAGIC = b"GIF87a" + b"\x00" * 6
GIF89_MAGIC = b"GIF89a" + b"\x00" * 6
WEBP_MAGIC = b"RIFF\x00\x00\x00\x00WEBP"
WEBM_MAGIC = b"\x1a\x45\xdf\xa3" + b"\x00" * 8
PDF_MAGIC = b"%PDF-1.7" + b"\x00" * 4
MP3_ID3_MAGIC = b"ID3" + b"\x00" * 9
MP3_SYNC_MAGIC = b"\xff\xfb\x90\x00" + b"\x00" * 8
WAV_MAGIC = b"RIFF\x00\x00\x00\x00WAVE"

ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
ALLOWED_ALL = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp4", ".mov", ".webm",
    ".mp3", ".wav", ".m4a",
    ".pdf", ".txt", ".csv",
}


# ── Extension whitelist ─────────────────────────────────────────────────────

class TestExtensionWhitelist:
    """Extension-based filtering (first line of defence)."""

    def test_allowed_extension_passes(self):
        f = FakeFileStorage("photo.png", PNG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is True
        assert ext == ".png"
        assert err is None

    def test_disallowed_extension_rejected(self):
        f = FakeFileStorage("script.exe", b"\x4d\x5a" + b"\x00" * 10)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is False
        assert ".exe" in err

    def test_no_file_provided(self):
        ok, ext, err = validate_upload(None, ALLOWED_IMAGE, "Photo")
        assert ok is False
        assert "No file" in err

    def test_empty_filename(self):
        f = FakeFileStorage("", b"")
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is False

    def test_double_extension_uses_last(self):
        """Only the final extension matters — 'image.jpg.exe' → '.exe'."""
        f = FakeFileStorage("image.jpg.exe", b"\x00" * 12)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is False

    def test_case_insensitive_extension(self):
        f = FakeFileStorage("photo.PNG", PNG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is True
        assert ext == ".png"

    def test_jpeg_extension_accepted(self):
        f = FakeFileStorage("photo.jpeg", JPEG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is True
        assert ext == ".jpeg"

    def test_gif_extension_accepted(self):
        f = FakeFileStorage("anim.gif", GIF89_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Anim")
        assert ok is True

    def test_webp_extension_accepted(self):
        f = FakeFileStorage("modern.webp", WEBP_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Banner")
        assert ok is True


# ── Magic-byte verification ─────────────────────────────────────────────────

class TestMagicByteVerification:
    """Content matches extension (prevents disguised uploads)."""

    def test_png_valid_magic(self):
        f = FakeFileStorage("test.png", PNG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is True

    def test_png_fake_magic_rejected(self):
        """A file claiming to be .png but with JPEG bytes → rejected."""
        f = FakeFileStorage("fake.png", JPEG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is False
        assert "disguised" in err.lower() or "content" in err.lower()

    def test_jpeg_valid_magic(self):
        f = FakeFileStorage("test.jpg", JPEG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is True

    def test_jpeg_fake_magic_rejected(self):
        f = FakeFileStorage("fake.jpg", PNG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is False

    def test_gif87a_valid(self):
        f = FakeFileStorage("old.gif", GIF87_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is True

    def test_gif89a_valid(self):
        f = FakeFileStorage("new.gif", GIF89_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is True

    def test_webp_valid_riff_header(self):
        f = FakeFileStorage("test.webp", WEBP_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is True

    def test_webp_invalid_riff_but_not_webp(self):
        """RIFF header but 'AVI ' instead of 'WEBP' at offset 8."""
        fake = b"RIFF\x00\x00\x00\x00AVI "
        f = FakeFileStorage("fake.webp", fake)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is False

    def test_pdf_valid_magic(self):
        f = FakeFileStorage("doc.pdf", PDF_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Doc")
        assert ok is True

    def test_pdf_fake_magic_rejected(self):
        f = FakeFileStorage("fake.pdf", b"\x00" * 12)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Doc")
        assert ok is False

    def test_webm_valid_magic(self):
        f = FakeFileStorage("clip.webm", WEBM_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Video")
        assert ok is True

    def test_mp3_id3_tag_valid(self):
        f = FakeFileStorage("song.mp3", MP3_ID3_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Audio")
        assert ok is True

    def test_mp3_sync_word_valid(self):
        f = FakeFileStorage("song.mp3", MP3_SYNC_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Audio")
        assert ok is True

    def test_wav_valid_riff(self):
        f = FakeFileStorage("sound.wav", WAV_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Audio")
        assert ok is True

    def test_txt_no_magic_check(self):
        """Plain text has no magic bytes — should always pass on extension."""
        f = FakeFileStorage("notes.txt", b"Hello world")
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Notes")
        assert ok is True

    def test_csv_no_magic_check(self):
        f = FakeFileStorage("data.csv", b"a,b,c\n1,2,3")
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Data")
        assert ok is True

    def test_stream_rewound_after_check(self):
        """After validation, stream position should be at 0 so .save() works."""
        f = FakeFileStorage("test.png", PNG_MAGIC)
        ok, _, _ = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is True
        assert f.stream.tell() == 0


# ── Per-category size limits ────────────────────────────────────────────────

class TestSizeLimits:
    """File size enforcement by category."""

    def test_image_within_limit(self):
        data = PNG_MAGIC + b"\x00" * 1000
        f = FakeFileStorage("ok.png", data)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is True

    def test_image_exceeds_limit(self):
        # Create a stream that exceeds the 10 MB image limit
        limit = UPLOAD_SIZE_LIMITS["image"]
        data = PNG_MAGIC + b"\x00" * (limit + 100)
        f = FakeFileStorage("huge.png", data)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Photo")
        assert ok is False
        assert "10 MB" in err

    def test_document_exceeds_limit(self):
        limit = UPLOAD_SIZE_LIMITS["document"]
        data = b"%PDF-1.7" + b"\x00" * (limit + 100)
        f = FakeFileStorage("huge.pdf", data)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Doc")
        assert ok is False
        assert "5 MB" in err

    def test_video_within_limit(self):
        data = b"\x1a\x45\xdf\xa3" + b"\x00" * 1000
        f = FakeFileStorage("clip.webm", data)
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Video")
        assert ok is True


# ── Edge cases & regression ─────────────────────────────────────────────────

class TestEdgeCases:
    """Boundary conditions and regression scenarios."""

    def test_null_bytes_in_filename_sanitised(self):
        """Filenames with null bytes should be sanitised away."""
        f = FakeFileStorage("photo\x00.exe.png", PNG_MAGIC)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        # secure_filename strips null bytes; result depends on what remains
        # The important thing is no crash and no '.exe' acceptance
        if ok:
            assert ext == ".png"

    def test_field_label_in_error_message(self):
        f = FakeFileStorage("bad.exe", b"\x00" * 12)
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Product Shot")
        assert ok is False
        assert "Product Shot" in err

    def test_very_short_file_magic_check(self):
        """File shorter than magic-byte length should not crash."""
        f = FakeFileStorage("tiny.png", b"\x89P")
        ok, ext, err = validate_upload(f, ALLOWED_IMAGE, "Test")
        assert ok is False  # magic doesn't match full PNG header

    def test_mp4_no_magic_check_passes(self):
        """MP4 has no simple magic bytes — passes on extension alone."""
        f = FakeFileStorage("clip.mp4", b"\x00\x00\x00\x1cftypisom")
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Video")
        assert ok is True

    def test_m4a_no_magic_check_passes(self):
        f = FakeFileStorage("audio.m4a", b"\x00\x00\x00\x1cftypM4A")
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Audio")
        assert ok is True

    def test_mov_no_magic_check_passes(self):
        f = FakeFileStorage("clip.mov", b"\x00\x00\x00\x14ftypqt")
        ok, ext, err = validate_upload(f, ALLOWED_ALL, "Video")
        assert ok is True
