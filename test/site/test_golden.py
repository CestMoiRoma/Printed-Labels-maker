"""golden.encode_png: PNG bytes depend on the pixels only."""

import io
import struct
import zlib

import golden
from PIL import Image, PngImagePlugin

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunks(data):
    """(tag, payload) of every chunk, with the CRC checked."""
    assert data.startswith(PNG_SIGNATURE)
    found, pos = [], len(PNG_SIGNATURE)
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        tag, payload = data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
        (crc,) = struct.unpack(">I", data[pos + 8 + length : pos + 12 + length])
        assert crc == zlib.crc32(tag + payload), tag
        found.append((tag, payload))
        pos += 12 + length
    return found


def sample(mode="RGB", size=(7, 5)):
    """A small image where every pixel differs from its neighbours."""
    image = Image.new(mode, size)
    bands = len(image.getbands())
    image.putdata(
        [tuple((x * 37 + y * 11 + b * 53) % 256 for b in range(bands)) for y in range(size[1]) for x in range(size[0])]
    )
    return image


def decode(data):
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        return image.copy()


def test_same_pixels_give_the_same_bytes():
    assert golden.encode_png(sample()) == golden.encode_png(sample())


def test_only_critical_chunks():
    data = golden.encode_png(sample())
    assert [tag for tag, _ in chunks(data)] == [b"IHDR", b"IDAT", b"IEND"]


def test_pixels_survive_the_round_trip():
    image = sample()
    decoded = decode(golden.encode_png(image))
    assert decoded.mode == "RGB" and decoded.size == image.size
    assert decoded.tobytes() == image.tobytes()


def test_metadata_of_the_source_is_dropped():
    info = PngImagePlugin.PngInfo()
    info.add_text("Creation Time", "2026-09-18T10:00:00")
    info.add_text("Software", "anything")
    buffer = io.BytesIO()
    sample().save(buffer, format="PNG", pnginfo=info, dpi=(144, 144), optimize=True)
    decoded = decode(buffer.getvalue())
    assert decoded.info  # the source does carry metadata
    assert golden.encode_png(decoded) == golden.encode_png(sample())


def test_write_png_reencodes_the_screenshot_bytes(tmp_path):
    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "screenshot")
    buffer = io.BytesIO()
    sample().save(buffer, format="PNG", pnginfo=info, compress_level=1)
    path = tmp_path / "shot.png"
    golden.write_png(path, buffer.getvalue())
    assert path.read_bytes() == golden.encode_png(sample())


def test_opaque_alpha_is_encoded_as_rgb():
    image = sample("RGB").convert("RGBA")
    data = golden.encode_png(image)
    ihdr = dict(chunks(data))[b"IHDR"]
    assert ihdr == struct.pack(">IIBBBBB", 7, 5, 8, 2, 0, 0, 0)
    assert data == golden.encode_png(sample("RGB"))


def test_real_transparency_is_kept():
    image = sample("RGBA")
    data = golden.encode_png(image)
    ihdr = dict(chunks(data))[b"IHDR"]
    assert ihdr == struct.pack(">IIBBBBB", 7, 5, 8, 6, 0, 0, 0)
    assert decode(data).tobytes() == image.tobytes()


def test_capture_settings_follow_the_plan():
    assert golden.LOCALE == "fr-FR"
    assert golden.TIMEZONE == "Europe/Paris"
    assert golden.DESKTOP == {"width": 1280, "height": 820}
