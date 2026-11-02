import math

from PIL import Image

from ColorConverter import ColorConverter


class ImageProcessor:
    
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

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(scaled_pixels)
        return new_img

    @staticmethod
    def point_operation(image_data, operation_type, values):

        if image_data is None:
            return None

        mode = image_data.mode

        if mode != "RGB":
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

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img

    @staticmethod
    def convert_to_grayscale(image_data, method="average"):

        if image_data is None:
            return None

        working_img = image_data
        if image_data.mode == "CMYK":
            working_img = ColorConverter.convert_image_to_rgb(image_data)

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

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img

    @staticmethod
    def _get_pixel_padded(pixels, width, height, x, y):
        """Pomocnicza funkcja pobierająca piksel z uwzględnieniem replikacji brzegów obrazu."""
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
        """Filtr wygładzający (uśredniający 3x3)."""
        if image_data is None: return None
        if image_data.mode == "CMYK":
            image_data = ColorConverter.convert_image_to_rgb(image_data)
        width, height = image_data.size
        pixels = list(image_data.getdata())

        kernel = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        new_pixels = ImageProcessor._apply_kernel(pixels, width, height, kernel, normalize=True)

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img

    @staticmethod
    def sharpening_filter(image_data):
        if image_data is None: return None
        if image_data.mode == "CMYK":
            image_data = ColorConverter.convert_image_to_rgb(image_data)
        width, height = image_data.size
        pixels = list(image_data.getdata())

        kernel = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]
        new_pixels = ImageProcessor._apply_kernel(pixels, width, height, kernel, normalize=False)

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img

    @staticmethod
    def custom_convolution(image_data, kernel):
        if image_data is None: return None
        if image_data.mode == "CMYK":
            image_data = ColorConverter.convert_image_to_rgb(image_data)
        width, height = image_data.size
        pixels = list(image_data.getdata())

        new_pixels = ImageProcessor._apply_kernel(pixels, width, height, kernel, normalize=True)

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img



    @staticmethod
    def median_filter(image_data):
        if image_data is None: return None
        if image_data.mode == "CMYK":
            image_data = ColorConverter.convert_image_to_rgb(image_data)
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

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img

    @staticmethod
    def sobel_filter(image_data):
        """Filtr wykrywania krawędzi (operator Sobela) z optymalizacją tablicy LUT."""
        if image_data is None: return None
        if image_data.mode == "CMYK":
            image_data = ColorConverter.convert_image_to_rgb(image_data)
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

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img

    @staticmethod
    def gaussian_blur(image_data, sigma=1.0):
        if image_data is None: return None
        if image_data.mode == "CMYK":
            image_data = ColorConverter.convert_image_to_rgb(image_data)
        width, height = image_data.size
        pixels = list(image_data.getdata())

        radius = max(1, int(math.ceil(3.0 * sigma)))
        size = 2 * radius + 1

        kernel = [0.0] * size
        kernel_sum = 0.0
        for i in range(size):
            x_val = i - radius
            val = math.exp(-(x_val ** 2) / (2.0 * (sigma ** 2)))
            kernel[i] = val
            kernel_sum += val
        for i in range(size):
            kernel[i] /= kernel_sum

        lut = {}

        temp_pixels = [(0.0, 0.0, 0.0)] * (width * height)
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = 0.0
                for i in range(size):
                    px_idx = max(0, min(width - 1, x + i - radius))
                    pixel = pixels[y * width + px_idx]
                    w = kernel[i]

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
                temp_pixels[y * width + x] = (r_sum, g_sum, b_sum)

        new_pixels = []
        for y in range(height):
            for x in range(width):
                r_sum = g_sum = b_sum = 0.0
                for j in range(size):
                    py_idx = max(0, min(height - 1, y + j - radius))
                    pixel = temp_pixels[py_idx * width + x]
                    w = kernel[j]

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

                new_pixels.append((
                    int(min(255, max(0, round(r_sum)))),
                    int(min(255, max(0, round(g_sum)))),
                    int(min(255, max(0, round(b_sum))))
                ))

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(new_pixels)
        return new_img