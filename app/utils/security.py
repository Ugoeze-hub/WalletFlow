import hashlib

class SecurityUtils:
    
    @staticmethod
    def hash_api_key(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
    
securityutils = SecurityUtils()