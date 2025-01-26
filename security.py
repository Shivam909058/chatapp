from passlib.context import CryptContext
import secrets
import string

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def generate_room_id(length: int = 8) -> str:
    """Generate a secure random room ID"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in string.punctuation for c in password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong" 