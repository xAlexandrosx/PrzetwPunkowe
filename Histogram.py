from PIL import Image

from ColorConverter import ColorConverter


class Histogram:
    @staticmethod
    def _rgb_image(image):
        if image.mode == "CMYK":
            return ColorConverter.convert_image_to_rgb(image)
        return image.convert("RGB")

    @staticmethod
    def stretch(image):
        image = Histogram._rgb_image(image)
        channels = []
        for channel in image.split():
            low, high = channel.getextrema()
            if low == high:
                channels.append(channel)
            else:
                channels.append(channel.point([int((value - low) * 255 / (high - low))
                                               for value in range(256)]))
        return Image.merge("RGB", channels)

    @staticmethod
    def equalize(image):
        image = Histogram._rgb_image(image)
        channels = []
        for channel in image.split():
            counts = channel.histogram()
            total = sum(counts)
            first = next((count for count in counts if count), 0)
            if total == first:
                channels.append(channel)
                continue
            cumulative = 0
            table = []
            for count in counts:
                cumulative += count
                table.append(max(0, (cumulative - first) * 255 // (total - first)))
            channels.append(channel.point(table))
        return Image.merge("RGB", channels)