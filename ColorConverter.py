from PIL import Image

class ColorConverter:

    @staticmethod
    def rgb_to_cmyk_pixel(r, g, b):

        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0

        k = min(1.0 - r_norm, 1.0 - g_norm, 1.0 - b_norm)

        if k >= 1.0 - 1e-9:
            return 0.0, 0.0, 0.0, 1.0

        c = (1.0 - r_norm - k) / (1.0 - k)
        m = (1.0 - g_norm - k) / (1.0 - k)
        y = (1.0 - b_norm - k) / (1.0 - k)

        c = max(0.0, min(1.0, c))
        m = max(0.0, min(1.0, m))
        y = max(0.0, min(1.0, y))
        k = max(0.0, min(1.0, k))

        return c, m, y, k

    @staticmethod
    def cmyk_to_rgb_pixel(c, m, y, k):

        r = 1.0 - min(1.0, c * (1.0 - k) + k)
        g = 1.0 - min(1.0, m * (1.0 - k) + k)
        b = 1.0 - min(1.0, y * (1.0 - k) + k)

        r_int = int(round(r * 255.0))
        g_int = int(round(g * 255.0))
        b_int = int(round(b * 255.0))

        return (
            max(0, min(255, r_int)),
            max(0, min(255, g_int)),
            max(0, min(255, b_int))
        )

    @classmethod
    def convert_image_to_cmyk(cls, rgb_image):
        if rgb_image is None or rgb_image.mode != "RGB":
            return rgb_image

        width, height = rgb_image.size
        rgb_pixels = list(rgb_image.getdata())
        cmyk_pixels = []

        for r, g, b in rgb_pixels:
            c, m, y, k = cls.rgb_to_cmyk_pixel(r, g, b)
            cmyk_pixels.append((
                int(round(c * 255.0)),
                int(round(m * 255.0)),
                int(round(y * 255.0)),
                int(round(k * 255.0))
            ))

        new_img = Image.new("CMYK", (width, height))
        new_img.putdata(cmyk_pixels)
        return new_img

    @classmethod
    def convert_image_to_rgb(cls, cmyk_image):
        if cmyk_image is None or cmyk_image.mode != "CMYK":
            return cmyk_image

        width, height = cmyk_image.size
        cmyk_pixels = list(cmyk_image.getdata())
        rgb_pixels = []

        for c_b, m_b, y_b, k_b in cmyk_pixels:
            c = c_b / 255.0
            m = m_b / 255.0
            y = y_b / 255.0
            k = k_b / 255.0

            r, g, b = cls.cmyk_to_rgb_pixel(c, m, y, k)
            rgb_pixels.append((r, g, b))

        new_img = Image.new("RGB", (width, height))
        new_img.putdata(rgb_pixels)
        return new_img