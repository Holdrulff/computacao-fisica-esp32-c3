"""
Morse code encoder with LED signaling.

International Morse Code standard (ITU-R M.1677-1).
"""
import asyncio
from core.logger import get_logger

# Morse code dictionary (A-Z, 0-9, common punctuation)
MORSE_CODE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',

    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.',

    '.': '.-.-.-', ',': '--..--', '?': '..--..',
    '!': '-.-.--', '-': '-....-',

    ' ': ' '  # Space between words
}


class MorseEncoder:
    """
    Morse code encoder with LED blinking.

    Implements international Morse code timing standard:
    - Dot duration: base unit (default 0.2s)
    - Dash duration: 3x dot
    - Symbol gap: 1x dot (between dots/dashes in a letter)
    - Letter gap: 3x dot (between letters)
    - Word gap: 7x dot (between words)
    """

    def __init__(self, led, display=None, dot_duration=0.2):
        """
        Initialize Morse encoder.

        Args:
            led: LED instance for signaling (dependency injection)
            display: Display instance for showing progress (optional)
            dot_duration: Duration of dot in seconds (default 0.2)
        """
        self.led = led
        self.display = display
        self.dot_duration = dot_duration
        self.dash_duration = dot_duration * 3
        self.symbol_gap = dot_duration
        self.letter_gap = dot_duration * 3
        self.word_gap = dot_duration * 7
        self.logger = get_logger('Morse')

        self.logger.info(f"MorseEncoder initialized (dot={dot_duration}s, display={'yes' if display else 'no'})")

    def text_to_morse(self, text: str) -> str:
        """
        Convert text to Morse code string.

        Args:
            text: Text to convert (A-Z, 0-9, punctuation)

        Returns:
            Morse code string (e.g., "... --- ...")

        Raises:
            ValueError: If text contains unsupported characters
        """
        text = text.upper().strip()
        morse_chars = []

        for char in text:
            if char not in MORSE_CODE:
                raise ValueError(f"Unsupported character: {char}")
            morse_chars.append(MORSE_CODE[char])

        # Join with space (letter separator)
        return ' '.join(morse_chars)

    async def _blink_dot(self):
        """Blink a dot pattern (short blink)."""
        self.led.on()
        await asyncio.sleep(self.dot_duration)
        self.led.off()

    async def _blink_dash(self):
        """Blink a dash pattern (long blink)."""
        self.led.on()
        await asyncio.sleep(self.dash_duration)
        self.led.off()

    def _update_display(self, text):
        """
        Update display with current progress - OPTIMIZED with throttling.

        Args:
            text: Text to display
        """
        if self.display and self.display.is_available:
            self.display.show_message(text)
            self.logger.debug(f"Display updated: {text}")

    async def blink_morse(self, text: str) -> dict:
        """
        Blink LED in Morse code pattern - OPTIMIZED with display throttling.

        Args:
            text: Text to encode and blink

        Returns:
            Dictionary with:
                - text: Original text
                - morse: Morse code representation
                - duration: Total duration in seconds
                - led: Final LED state

        Raises:
            ValueError: If text contains unsupported characters
        """
        import time

        # Convert to Morse code
        morse = self.text_to_morse(text)
        self.logger.info(f"Encoding: '{text}' -> '{morse}'")

        # Save initial LED state
        initial_state = self.led.is_on
        start_time = time.time()

        # Track position in original text for display
        text_upper = text.upper().strip()
        char_index = 0

        # Display buffer - build string incrementally, update every N chars
        display_buffer = []
        UPDATE_INTERVAL = 3  # Update display every 3 characters (reduces I2C calls)

        # Blink the pattern
        words = morse.split('  ')  # Double space = word separator

        for word_idx, word in enumerate(words):
            letters = word.split(' ')  # Single space = letter separator

            for letter_idx, letter in enumerate(letters):
                # Add current character to buffer
                if char_index < len(text_upper):
                    display_buffer.append(text_upper[char_index])

                # Throttled display update - every N characters instead of every character
                if len(display_buffer) % UPDATE_INTERVAL == 0:
                    self._update_display(''.join(display_buffer))

                # Blink each symbol in the letter
                for symbol_idx, symbol in enumerate(letter):
                    if symbol == '.':
                        await self._blink_dot()
                    elif symbol == '-':
                        await self._blink_dash()

                    # Gap between symbols (within letter)
                    if symbol_idx < len(letter) - 1:
                        await asyncio.sleep(self.symbol_gap)

                # Move to next character in original text
                char_index += 1

                # Gap between letters
                if letter_idx < len(letters) - 1:
                    await asyncio.sleep(self.letter_gap)

            # Gap between words (space character)
            if word_idx < len(words) - 1:
                await asyncio.sleep(self.word_gap)
                if char_index < len(text_upper):
                    display_buffer.append(' ')
                char_index += 1  # Account for space in original text

        # Final display update (show complete text)
        if display_buffer:
            self._update_display(''.join(display_buffer))

        # Restore initial LED state
        if initial_state:
            self.led.on()
        else:
            self.led.off()

        duration = time.time() - start_time
        self.logger.info(f"Morse completed in {duration:.2f}s")

        return {
            'text': text,
            'morse': morse,
            'duration': round(duration, 2),
            'led': 'on' if self.led.is_on else 'off'
        }
