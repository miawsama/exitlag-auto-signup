import random
import string

class PasswordGenerator:
    def __init__(self):
        # Define character sets, excluding specific symbols
        self.chars = {
            'uppercase': string.ascii_uppercase,
            'lowercase': string.ascii_lowercase,
            'digits': string.digits,
            'special': ''.join(c for c in string.punctuation if c not in "'\".,")
        }

    def generate(self, length: int = 12) -> str:
        """Generate a strong password with specific pattern:
        - Starts with uppercase
        - Followed by lowercase
        - Ends with alternating digits and special characters
        """
        if length < 8:
            raise ValueError("Password length should be at least 8 characters.")
        
        # Calculate section lengths
        uppercase_len = length // 4
        lowercase_len = length // 4
        remaining_len = length - (uppercase_len + lowercase_len)
        digits_special_len = remaining_len // 2
        
        # Generate parts
        uppercase_part = ''.join(random.choices(self.chars['uppercase'], k=uppercase_len))
        lowercase_part = ''.join(random.choices(self.chars['lowercase'], k=lowercase_len))
        
        # Generate alternating digits and special characters
        mixed_part = []
        for i in range(remaining_len):
            if i % 2 == 0:
                mixed_part.append(random.choice(self.chars['digits']))
            else:
                mixed_part.append(random.choice(self.chars['special']))
        
        # Combine all parts
        password = list(uppercase_part + lowercase_part + ''.join(mixed_part))
        
        # Shuffle the mixed part to make it less predictable
        mixed_start_index = uppercase_len + lowercase_len
        mixed_part = password[mixed_start_index:]
        random.shuffle(mixed_part)
        password[mixed_start_index:] = mixed_part
        
        return ''.join(password)
