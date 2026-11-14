from PIL import Image
from ColorConverter import ColorConverter


def _matrix_offsets(matrix, hit_miss=False):
    try:
        rows = [list(row) for row in matrix]
    except TypeError as exc:
        raise ValueError("matrix must be a nonempty rectangular sequence") from exc
    if not rows or not rows[0] or len(rows) % 2 == 0 or len(rows[0]) % 2 == 0:
        raise ValueError("matrix dimensions must be nonempty and odd")
    width = len(rows[0])
    allowed = (-1, 0, 1) if hit_miss else (0, 1)
    if any(len(row) != width for row in rows):
        raise ValueError("matrix must be rectangular")
    if any(type(value) is not int or value not in allowed
           for row in rows for value in row):
        raise ValueError("invalid matrix value")
    return [(x - width // 2, y - len(rows) // 2, value)
            for y, row in enumerate(rows) for x, value in enumerate(row)
            if value != (-1 if hit_miss else 0)]


def _read_image(image):
    if not isinstance(image, Image.Image) or image.mode not in ("1", "L", "RGB", "CMYK"):
        raise ValueError("image must be a binary 1, L, RGB or CMYK Pillow image")
    if image.mode == "CMYK":
        image = ColorConverter.convert_image_to_rgb(image)
    image = image.convert("RGB")
    pixels = list(image.getdata())
    if any(pixel not in ((0, 0, 0), (255, 255, 255)) for pixel in pixels):
        raise ValueError("image must contain only black and white pixels")
    return image.size, [pixel == (0, 0, 0) for pixel in pixels]


def _render(size, pixels):
    image = Image.new("RGB", size)
    image.putdata([(0, 0, 0) if pixel else (255, 255, 255) for pixel in pixels])
    return image


def _sample(pixels, width, height, x, y):
    return 0 <= x < width and 0 <= y < height and pixels[y * width + x]


def _apply(size, pixels, offsets, operation):
    width, height = size
    result = []
    for y in range(height):
        for x in range(width):
            if operation == "dilation":
                value = any(_sample(pixels, width, height, x - dx, y - dy)
                            for dx, dy, _ in offsets)
            elif operation == "erosion":
                value = all(_sample(pixels, width, height, x + dx, y + dy)
                            for dx, dy, _ in offsets)
            else:
                value = all(_sample(pixels, width, height, x + dx, y + dy) == bool(expected)
                            for dx, dy, expected in offsets)
            result.append(value)
    return result


def dilation(image, matrix):
    offsets = _matrix_offsets(matrix)
    size, pixels = _read_image(image)
    return _render(size, _apply(size, pixels, offsets, "dilation"))


def erosion(image, matrix):
    offsets = _matrix_offsets(matrix)
    size, pixels = _read_image(image)
    return _render(size, _apply(size, pixels, offsets, "erosion"))


def opening(image, matrix):
    offsets = _matrix_offsets(matrix)
    size, pixels = _read_image(image)
    pixels = _apply(size, pixels, offsets, "erosion")
    return _render(size, _apply(size, pixels, offsets, "dilation"))


def closing(image, matrix):
    offsets = _matrix_offsets(matrix)
    size, pixels = _read_image(image)
    pixels = _apply(size, pixels, offsets, "dilation")
    return _render(size, _apply(size, pixels, offsets, "erosion"))


def hit_or_miss(image, matrix):
    offsets = _matrix_offsets(matrix, hit_miss=True)
    size, pixels = _read_image(image)
    return _render(size, _apply(size, pixels, offsets, "hit_or_miss"))


def thinning(image, matrix):
    offsets = _matrix_offsets(matrix, hit_miss=True)
    size, pixels = _read_image(image)
    matches = _apply(size, pixels, offsets, "hit_or_miss")
    return _render(size, [pixel and not match for pixel, match in zip(pixels, matches)])


def thickening(image, matrix):
    offsets = _matrix_offsets(matrix, hit_miss=True)
    size, pixels = _read_image(image)
    matches = _apply(size, pixels, offsets, "hit_or_miss")
    return _render(size, [pixel or match for pixel, match in zip(pixels, matches)])