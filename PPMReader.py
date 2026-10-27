class PPMReader:


    buffer_size: int = 65536    



    def read_ppm(self, file_path: str) -> dict:
        try:
            with open(file_path, "rb") as f:
                first_line = f.readline().decode('latin-1', errors='ignore').strip()
            
            if first_line.startswith("P3"):
                return self._read_ppm_p3(file_path)
            elif first_line.startswith("P6"):
                return self._read_ppm_p6(file_path)
            else:
                raise ValueError(f"Nieobsługiwany format PPM (nagłówek: {first_line})")

        except Exception as e:
            raise RuntimeError(f"Błąd parsowania pliku PPM: {e}")








    def _read_ppm_p3(self, file_path: str) -> dict:
        tokens = []
        
        with open(file_path, 'r', encoding='latin-1') as file:
            for line in file:
                if '#' in line:
                    line = line.split('#', 1)[0]
                tokens.extend(line.split())

        if len(tokens) < 4:
            raise ValueError("Niekompletny nagłówek pliku P3 (za mało tokenów).")

        magic = tokens.pop(0)
        width = int(tokens.pop(0))
        height = int(tokens.pop(0))
        max_val = int(tokens.pop(0))

        if max_val <= 0 or max_val > 65535:
            raise ValueError(f"Nieobsługiwana maksymalna wartość koloru: {max_val}.")

        total_pixels_values = width * height * 3
        if len(tokens) < total_pixels_values:
            raise ValueError(f"Plik P3 jest za krótki – oczekiwano {total_pixels_values} wartości, pobrano {len(tokens)}.")

        raw_ints = [int(t) for t in tokens[:total_pixels_values]]
        is_16bit = max_val > 255

        if is_16bit:
            pixels = [int(val * 255 / max_val) for val in raw_ints]
        else:
            pixels = raw_ints

        return {
            "format": magic,
            "width": width,
            "height": height,
            "max_val": max_val,
            "pixels": pixels
        }







    

    def _read_ppm_p6(self, file_path: str) -> dict:
        with open(file_path, "rb") as file_obj:
            tokens = []
            
            for line in file_obj:
                line_str = line.decode('latin-1', errors='ignore')
                
                if '#' in line_str:
                    line_str = line_str.split('#', 1)[0]
                
                parts = line_str.split()
                for token in parts:
                    tokens.append(token)
                    if len(tokens) == 4:
                        break
                if len(tokens) == 4:
                    break

            if len(tokens) < 4:
                raise ValueError("Niekompletny nagłówek pliku P6.")

            magic = tokens[0]
            width = int(tokens[1])
            height = int(tokens[2])
            max_val = int(tokens[3])

            if max_val <= 0 or max_val > 65535:
                raise ValueError(f"Nieobsługiwana maksymalna wartość koloru: {max_val}.")
            
        return self._read_p6_binary_data(file_path, width, height, max_val)





    def _read_p6_binary_data(self, file_path: str, width: int, height: int, max_val: int) -> dict:
        """Metoda doczytująca binarne dane P6 blokowo za pomocą zdefiniowanego bufora."""

        with open(file_path, "rb") as file_obj:
            spaces_count = 0
            while spaces_count < 4:
                byte = file_obj.read(1)
                if not byte:
                    raise ValueError("Błąd struktury pliku P6 – nie znaleziono końca nagłówka.")
                if byte in b" \t\n\r":
                    spaces_count += 1
                    while True:
                        next_byte = file_obj.read(1)
                        if not next_byte:
                            break
                        if next_byte not in b" \t\n\r":
                            file_obj.seek(-1, 1)
                            break

            is_16bit = max_val > 255
            pixels = []

            if is_16bit:
                expected_bytes = width * height * 3 * 2
                bytes_read_total = 0
                carry = b""

                while bytes_read_total < expected_bytes:
                    to_read = min(self.buffer_size, expected_bytes - bytes_read_total)
                    chunk = file_obj.read(to_read)
                    if not chunk and bytes_read_total == 0:
                        raise ValueError("Plik P6 (16-bit) jest niekompletny.")
                    
                    bytes_read_total += len(chunk)
                    data = carry + chunk
                    
                    if len(data) % 2 != 0 and bytes_read_total < expected_bytes:
                        carry = data[-1:]
                        data = data[:-1]
                    else:
                        carry = b""

                    for i in range(0, len(data), 2):
                        val_16bit = (data[i] << 8) + data[i+1]
                        pixels.append(int(val_16bit * 255 / max_val))
            else:
                expected_bytes = width * height * 3
                bytes_read_total = 0

                while bytes_read_total < expected_bytes:
                    to_read = min(self.buffer_size, expected_bytes - bytes_read_total)
                    chunk = file_obj.read(to_read)
                    if not chunk:
                        raise ValueError("Plik P6 jest niekompletny.")
                    
                    pixels.extend(chunk)
                    bytes_read_total += len(chunk)

            return {
                "format": "P6",
                "width": width,
                "height": height,
                "max_val": max_val,
                "pixels": pixels
            }