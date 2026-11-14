import math

from PIL import Image

from ColorConverter import ColorConverter

try:
    from gaussian_blur_cpp import gaussian_blur as _native_gaussian_blur
except ModuleNotFoundError as error:
    if error.name != "gaussian_blur_cpp":
        raise
    _native_gaussian_blur = None


class ImageProcessor:

    @staticmethod
    def _rgb_image(size, pixels):
        image = Image.new("RGB", size)
        image.putdata(pixels)
        return image

    @staticmethod
    def _convert_cmyk(image):
        if image.mode == "CMYK":
            return ColorConverter.convert_image_to_rgb(image)
        return image

    @staticmethod
    def invert_colors(image_data):
        if image_data is None:
            return None
        image_data = ImageProcessor._convert_cmyk(image_data).convert("RGB")
        return image_data.point([255 - value for value in range(256)] * 3)
    
    @staticmethod
    def linear_scaling(image_data, width, height):
        if image_data is None:
            return None

        pixels = list(image_data.getdata())
        r_vals = [p[0] for p in pixels]
        g_vals = [p[1] for p in pixels]
        b_vals = [p[2] for p in pixels]

        min_r, max_r = min(r_vals), max(r_vals)
        min_g, max_g = min(g_vals), max(g_vals)
        min_b, max_b = min(b_vals), max(b_vals)

        def scale(val, v_min, v_max):
            if v_max == v_min:
                return val
            return int((val - v_min) * 255 / (v_max - v_min))

        scaled_pixels = [
            (scale(p[0], min_r, max_r), scale(p[1], min_g, max_g), scale(p[2], min_b, max_b))
            for p in pixels
        ]

        return ImageProcessor._rgb_image((width, height), scaled_pixels)

    @staticmethod
    def point_operation(image_data, operation_type, values):

        if image_data is None:
            return None

        if image_data.mode != "RGB":
            image_data = image_data.convert("RGB")

        width, height = image_data.size
        pixels = list(image_data.getdata())
        new_pixels = []

        for p in pixels:
            r, g, b = p[:3]

            if operation_type == 'add':
                r = int(min(255, max(0, r + values[0])))
                g = int(min(255, max(0, g + values[1])))
                b = int(min(255, max(0, b + values[2])))
            elif operation_type == 'sub':
                r = int(min(255, max(0, r - values[0])))
                g = int(min(255, max(0, g - values[1])))
                b = int(min(255, max(0, b - values[2])))
            elif operation_type == 'mul':
                r = int(min(255, max(0, r * values[0])))
                g = int(min(255, max(0, g * values[1])))
                b = int(min(255, max(0, b * values[2])))
            elif operation_type == 'div':
                r = int(min(255, max(0, r / values[0]))) if values[0] != 0 else r
                g = int(min(255, max(0, g / values[1]))) if values[1] != 0 else g
                b = int(min(255, max(0, b / values[2]))) if values[2] != 0 else b
            elif operation_type == 'brightness':
                r = int(min(255, max(0, r + values[0])))
                g = int(min(255, max(0, g + values[0])))
                b = int(min(255, max(0, b + values[0])))

            new_pixels.append((r, g, b))

        return ImageProcessor._rgb_image((width, height), new_pixels)

    @staticmethod
    def convert_to_grayscale(image_data, method="average"):

        if image_data is None:
            return None

        working_img = ImageProcessor._convert_cmyk(image_data)

        width, height = working_img.size
        pixels = list(working_img.getdata())
        new_pixels = []

        for p in pixels:
            r, g, b = p[0], p[1], p[2]
            if method == "average":
                gray = int((r + g + b) / 3)
            elif method == "luminosity":
                gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            else:
                gray = r

            new_pixels.append((gray, gray, gray))

        return ImageProcessor._rgb_image((width, height), new_pixels)

    @staticmethod
    def _get_pixel_padded(pixels, width, height, x, y):
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))
        return pixels[y * width + x]

    @staticmethod
    def _apply_kernel(pixels, width, height, kernel, normalize=True):
        k_height = len(kernel)
        k_width = len(kernel[0])
        ky_radius = k_height // 2
        kx_radius = k_width // 2

        k_sum = sum(sum(row) for row in kernel) if normalize else 1.0

        lut = {}
        new_pixels = []

        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = 0.0
                for j in range(k_height):
                    for i in range(k_width):
                        px_x = x + i - kx_radius
                        px_y = y + j - ky_radius
                        pixel = ImageProcessor._get_pixel_padded(pixels, width, height, px_x, px_y)
                        w = kernel[j][i]

                        cache_key = (pixel, w)
                        if cache_key in lut:
                            r_w, g_w, b_w = lut[cache_key]
                        else:
                            pr, pg, pb = pixel
                            r_w = pr * w
                            g_w = pg * w
                            b_w = pb * w
                            lut[cache_key] = (r_w, g_w, b_w)

                        r_sum += r_w
                        g_sum += g_w
                        b_sum += b_w

                if normalize and k_sum != 0:
                    r_sum /= k_sum
                    g_sum /= k_sum
                    b_sum /= k_sum

                new_pixels.append((
                    int(min(255, max(0, round(r_sum)))),
                    int(min(255, max(0, round(g_sum)))),
                    int(min(255, max(0, round(b_sum))))
                ))

        return new_pixels

    @staticmethod
    def smoothing_filter(image_data):
        kernel = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        return ImageProcessor._convolve_image(image_data, kernel, normalize=True)

    @staticmethod
    def sharpening_filter(image_data):
        kernel = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]
        return ImageProcessor._convolve_image(image_data, kernel, normalize=False)

    @staticmethod
    def custom_convolution(image_data, kernel):
        return ImageProcessor._convolve_image(image_data, kernel, normalize=True)

    @staticmethod
    def _convolve_image(image_data, kernel, normalize):
        if image_data is None:
            return None
        image_data = ImageProcessor._convert_cmyk(image_data)
        width, height = image_data.size
        pixels = list(image_data.getdata())

        new_pixels = ImageProcessor._apply_kernel(pixels, width, height, kernel, normalize=normalize)
        return ImageProcessor._rgb_image((width, height), new_pixels)



    @staticmethod
    def median_filter(image_data):
        if image_data is None:
            return None
        image_data = ImageProcessor._convert_cmyk(image_data)
        width, height = image_data.size
        pixels = list(image_data.getdata())
        new_pixels = []

        for y in range(height):
            for x in range(width):
                r_list, g_list, b_list = [], [], []
                for j in range(-1, 2):
                    for i in range(-1, 2):
                        pr, pg, pb = ImageProcessor._get_pixel_padded(pixels, width, height, x + i, y + j)
                        r_list.append(pr)
                        g_list.append(pg)
                        b_list.append(pb)
                r_list.sort()
                g_list.sort()
                b_list.sort()
                mid = len(r_list) // 2
                new_pixels.append((r_list[mid], g_list[mid], b_list[mid]))

        return ImageProcessor._rgb_image((width, height), new_pixels)

    @staticmethod
    def sobel_filter(image_data):
        if image_data is None:
            return None
        image_data = ImageProcessor._convert_cmyk(image_data)
        width, height = image_data.size
        pixels = list(image_data.getdata())
        new_pixels = []

        gx_kernel = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
        gy_kernel = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]

        lut = {}

        for y in range(height):
            for x in range(width):
                rx = gx = ry = gy = bx = by = 0
                for j in range(-1, 2):
                    for i in range(-1, 2):
                        pixel = ImageProcessor._get_pixel_padded(pixels, width, height, x + i, y + j)
                        wx = gx_kernel[j + 1][i + 1]
                        wy = gy_kernel[j + 1][i + 1]

                        cache_key_x = (pixel, wx)
                        if cache_key_x in lut:
                            r_wx, g_wx, b_wx = lut[cache_key_x]
                        else:
                            pr, pg, pb = pixel
                            r_wx = pr * wx
                            g_wx = pg * wx
                            b_wx = pb * wx
                            lut[cache_key_x] = (r_wx, g_wx, b_wx)

                        rx += r_wx
                        gx += g_wx
                        bx += b_wx

                        cache_key_y = (pixel, wy)
                        if cache_key_y in lut:
                            r_wy, g_wy, b_wy = lut[cache_key_y]
                        else:
                            pr, pg, pb = pixel
                            r_wy = pr * wy
                            g_wy = pg * wy
                            b_wy = pb * wy
                            lut[cache_key_y] = (r_wy, g_wy, b_wy)

                        ry += r_wy
                        gy += g_wy
                        by += b_wy

                r = int(min(255, max(0, (rx ** 2 + ry ** 2) ** 0.5)))
                g = int(min(255, max(0, (gx ** 2 + gy ** 2) ** 0.5)))
                b = int(min(255, max(0, (bx ** 2 + by ** 2) ** 0.5)))
                new_pixels.append((r, g, b))

        return ImageProcessor._rgb_image((width, height), new_pixels)

    @staticmethod
    def gaussian_blur(image_data, sigma=1.0):
        if image_data is None:
            return None
        if not math.isfinite(sigma) or sigma <= 0:
            raise ValueError("sigma must be a positive finite number")
        image_data = ImageProcessor._convert_cmyk(image_data)
        if image_data.mode != "RGB":
            image_data = image_data.convert("RGB")

        width, height = image_data.size
        if _native_gaussian_blur is not None and width and height:
            pixels = _native_gaussian_blur(image_data.tobytes(), width, height, sigma)
            return Image.frombytes("RGB", (width, height), pixels)

        img_size = width * height
        pixel_list = list(image_data.getdata())

        radius = max(1, int(math.ceil(3.0 * sigma)))

        kernel_weights = []
        kernel_sum = 0.0
        for offset in range(-radius, radius + 1):
            weight = math.exp(-(offset ** 2) / (2.0 * (sigma ** 2)))
            kernel_weights.append((offset, weight))
            kernel_sum += weight

        multiplication_tables = []

        for offset, weight in kernel_weights:
            normalized_weight = weight / kernel_sum
            table = [intensity * normalized_weight for intensity in range(256)]
            multiplication_tables.append(table)

        horizontal_indices = [
            [min(width - 1, max(0, x + offset)) for offset, _ in kernel_weights]
            for x in range(width)
        ]
        vertical_indices = [
            [min(height - 1, max(0, y + offset)) * width for offset, _ in kernel_weights]
            for y in range(height)
        ]

        horizontal_pixels = [None] * img_size
        for y in range(height):
            row_offset = y * width
            for x in range(width):
                r_sum = g_sum = b_sum = 0.0

                for px, lookup in zip(horizontal_indices[x], multiplication_tables):
                    pr, pg, pb = pixel_list[row_offset + px]
                    r_sum += lookup[pr]
                    g_sum += lookup[pg]
                    b_sum += lookup[pb]

                horizontal_pixels[row_offset + x] = (
                    int(min(255, max(0, round(r_sum)))),
                    int(min(255, max(0, round(g_sum)))),
                    int(min(255, max(0, round(b_sum))))
                )

        final_pixels = [None] * img_size
        for y in range(height):
            row_offset = y * width
            for x in range(width):
                r_sum = g_sum = b_sum = 0.0

                for row_index, lookup in zip(vertical_indices[y], multiplication_tables):
                    pr, pg, pb = horizontal_pixels[row_index + x]
                    r_sum += lookup[pr]
                    g_sum += lookup[pg]
                    b_sum += lookup[pb]

                final_pixels[row_offset + x] = (
                    int(min(255, max(0, round(r_sum)))),
                    int(min(255, max(0, round(g_sum)))),
                    int(min(255, max(0, round(b_sum))))
                )

        return ImageProcessor._rgb_image((width, height), final_pixels)