import random
from src.config import CHARS, PASSWORD_LENGTH

class PasswordGenerator:
    @staticmethod
    def generate(length: int = PASSWORD_LENGTH) -> str:
        """Generate a strong password."""
        if length < 8:
            raise ValueError("Password length should be at least 8 characters.")
        
        # Ensure at least one character from each category
        password = [
            random.choice(CHARS['lowercase']),
            random.choice(CHARS['uppercase']),
            random.choice(CHARS['digits']),
            random.choice(CHARS['special'])
        ]
        
        # Fill remaining length with random characters
        all_characters = CHARS['lowercase'] + CHARS['uppercase'] + CHARS['digits'] + CHARS['special']
        password.extend(random.choices(all_characters, k=length - len(password)))
        
        # Shuffle the password
        random.shuffle(password)
        
        return ''.join(password)
