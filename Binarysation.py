import math

from ColorConverter import ColorConverter


class Binarysation:

    @staticmethod
    def _gray(image):
        if image.mode == "CMYK":
            image = ColorConverter.convert_image_to_rgb(image)
        return image.convert("RGB").convert("L")

    @staticmethod
    def _render(gray, threshold):
        table = [0] * (threshold + 1) + [255] * (255 - threshold)

        return gray.point(table).convert("RGB")

    @staticmethod
    def manual(image, threshold):
        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 255:
            raise ValueError("threshold must be between 0 and 255")
        return Binarysation._render(Binarysation._gray(image), threshold)

    @staticmethod
    def percent_black(image, percent):
        if not isinstance(percent, (int, float)) or not 0 <= percent <= 100:
            raise ValueError("percent must be between 0 and 100")
        gray = Binarysation._gray(image)
        counts = gray.histogram()
        total = sum(counts)
        target = total * percent / 100
        cumulative = 0
        threshold = -1
        best = abs(target)
        for value, count in enumerate(counts):
            cumulative += count
            error = abs(cumulative - target)
            if error < best:
                threshold, best = value, error
        return Binarysation._render(gray, threshold)

    @staticmethod
    def iterative_mean(image):
        gray = Binarysation._gray(image)
        counts = gray.histogram()
        occupied = [i for i, count in enumerate(counts) if count]
        if len(occupied) < 2:
            return Binarysation._render(gray, occupied[0] if occupied else 0)
        threshold = (occupied[0] + occupied[-1]) // 2
        while True:
            lower = sum(counts[:threshold + 1])
            upper = sum(counts[threshold + 1:])
            if not lower or not upper:
                break
            mean_low = sum(i * counts[i] for i in range(threshold + 1)) / lower
            mean_high = sum(i * counts[i] for i in range(threshold + 1, 256)) / upper
            new_threshold = int((mean_low + mean_high) / 2)
            if new_threshold == threshold:
                break
            threshold = new_threshold
        return Binarysation._render(gray, threshold)

    @staticmethod
    def _optimal(image, criterion):
        gray = Binarysation._gray(image)
        counts = gray.histogram()
        occupied = [i for i, count in enumerate(counts) if count]
        if len(occupied) < 2:
            return Binarysation._render(gray, occupied[0] if occupied else 0)
        total = sum(counts)
        best_score = math.inf
        best_threshold = occupied[0]
        for threshold in range(occupied[0], occupied[-1]):
            low = [(i, counts[i]) for i in range(threshold + 1) if counts[i]]
            high = [(i, counts[i]) for i in range(threshold + 1, 256) if counts[i]]
            score = criterion(low, high, total)
            if score < best_score:
                best_score, best_threshold = score, threshold
        return Binarysation._render(gray, best_threshold)

    @staticmethod
    def entropy(image):
        def score(low, high, total):
            entropy = 0.0
            for group in (low, high):
                size = sum(count for _, count in group)
                entropy -= sum((count / size) * math.log(count / size)
                               for _, count in group)
            return -entropy
        return Binarysation._optimal(image, score)

    @staticmethod
    def minimum_error(image):
        def score(low, high, total):
            result = 0.0
            for group in (low, high):
                size = sum(count for _, count in group)
                mean = sum(i * count for i, count in group) / size
                variance = sum(count * (i - mean) ** 2 for i, count in group) / size
                if variance <= 0:
                    return math.inf
                probability = size / total
                result += probability * (math.log(variance) - 2 * math.log(probability))
            return result
        return Binarysation._optimal(image, score)

    @staticmethod
    def fuzzy_minimum_error(image):
        def score(low, high, total):
            result = 0.0
            for group in (low, high):
                size = sum(count for _, count in group)
                mean = sum(i * count for i, count in group) / size
                for i, count in group:
                    membership = 1 / (1 + abs(i - mean) / 255)
                    if membership < 1:
                        result -= count * (membership * math.log(membership) +
                                           (1 - membership) * math.log(1 - membership))
            return result / total
        return Binarysation._optimal(image, score)