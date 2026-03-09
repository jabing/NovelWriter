"""数据加密工具模块

提供敏感数据加密功能，保护 API 密钥和其他机密信息。
使用 Fernet 对称加密确保数据安全存储。
"""

from cryptography.fernet import Fernet
import base64
import os
from typing import Optional, Any


class DataEncryption:
    """数据加密工具类
    
    提供安全的字符串加密和解密功能，适用于：
    - API 密钥加密存储
    - 敏感配置数据加密
    - 用户凭证保护
    
    Attributes:
        key: 加密密钥
        cipher: Fernet 加密器实例
    """
    
    def __init__(self, key: Optional[str] = None):
        """初始化加密器
        
        Args:
            key: 可选的加密密钥。如果未提供，将生成新密钥。
                密钥应为 32 字节的 URL-safe base64 编码字符串
        """
        if key is None:
            self.key = Fernet.generate_key()
        else:
            # 确保密钥是正确格式
            key_bytes = key.encode() if isinstance(key, str) else key
            # 如果密钥不是 32 字节，使用 base64 编码
            if len(key_bytes) != 32:
                self.key = base64.urlsafe_b64encode(key_bytes.ljust(32)[:32])
            else:
                self.key = base64.urlsafe_b64encode(key_bytes)
        
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """加密字符串
        
        Args:
            data: 要加密的原始字符串
            
        Returns:
            加密后的字符串（URL-safe base64 编码）
            
        Raises:
            TypeError: 如果输入不是字符串
        """
        if not isinstance(data, str):
            raise TypeError("Data must be a string")
        
        encrypted = self.cipher.encrypt(data.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密字符串
        
        Args:
            encrypted_data: 要解密的加密字符串
            
        Returns:
            解密后的原始字符串
            
        Raises:
            TypeError: 如果输入不是字符串
            cryptography.fernet.InvalidToken: 如果解密失败（密钥错误或数据损坏）
        """
        if not isinstance(encrypted_data, str):
            raise TypeError("Encrypted data must be a string")
        
        decrypted = self.cipher.decrypt(encrypted_data.encode('utf-8'))
        return decrypted.decode('utf-8')
    
    def encrypt_api_key(self, api_key: str) -> str:
        """加密 API 密钥
        
        Args:
            api_key: 要加密的 API 密钥
            
        Returns:
            加密后的 API 密钥
            
        Note:
            此方法与 encrypt() 方法功能相同，但语义更明确，
            便于代码阅读和维护
        """
        return self.encrypt(api_key)
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """解密 API 密钥
        
        Args:
            encrypted_key: 加密的 API 密钥
            
        Returns:
            解密后的 API 密钥
            
        Note:
            此方法与 decrypt() 方法功能相同，但语义更明确
        """
        return self.decrypt(encrypted_key)
    
    def encrypt_sensitive_data(self, data: dict[str, Any]) -> str:
        """加密敏感数据字典
        
        Args:
            data: 要加密的字典数据
            
        Returns:
            加密后的 JSON 字符串
        """
        import json
        json_str = json.dumps(data, sort_keys=True)
        return self.encrypt(json_str)
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> dict[str, Any]:
        """解密敏感数据字典
        
        Args:
            encrypted_data: 加密的 JSON 字符串
            
        Returns:
            解密后的字典数据
        """
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)
    
    @staticmethod
    def generate_key() -> str:
        """生成新的加密密钥
        
        Returns:
            URL-safe base64 编码的 32 字节密钥字符串
            
        Example:
            >>> key = DataEncryption.generate_key()
            >>> encryptor = DataEncryption(key)
        """
        return Fernet.generate_key().decode('utf-8')
    
    @staticmethod
    def save_key(key: str, filepath: str) -> None:
        """安全地保存密钥到文件
        
        Args:
            key: 要保存的密钥
            filepath: 密钥文件路径
            
        Note:
            密钥文件权限将设置为 600（仅所有者可读写）
        """
        with open(filepath, 'w') as f:
            f.write(key)
        # 设置文件权限为 600（仅所有者可读写）
        os.chmod(filepath, 0o600)
    
    @staticmethod
    def load_key(filepath: str) -> str:
        """从文件加载密钥
        
        Args:
            filepath: 密钥文件路径
            
        Returns:
            加载的密钥字符串
        """
        with open(filepath, 'r') as f:
            return f.read().strip()


# 使用示例
if __name__ == "__main__":
    # 示例 1: 使用自动生成的密钥
    print("=== 示例 1: 自动生成密钥 ===")
    encryptor = DataEncryption()
    api_key = "sk-1234567890abcdef"
    encrypted = encryptor.encrypt_api_key(api_key)
    decrypted = encryptor.decrypt_api_key(encrypted)
    print(f"原始 API 密钥：{api_key}")
    print(f"加密后：{encrypted}")
    print(f"解密后：{decrypted}")
    print(f"验证：{api_key == decrypted}")
    
    # 示例 2: 使用指定密钥
    print("\n=== 示例 2: 使用指定密钥 ===")
    key = DataEncryption.generate_key()
    encryptor2 = DataEncryption(key)
    sensitive_data = {"password": "secret123", "token": "abc-xyz"}
    encrypted_data = encryptor2.encrypt_sensitive_data(sensitive_data)
    decrypted_data = encryptor2.decrypt_sensitive_data(encrypted_data)
    print(f"原始数据：{sensitive_data}")
    print(f"加密后：{encrypted_data}")
    print(f"解密后：{decrypted_data}")
    print(f"验证：{sensitive_data == decrypted_data}")
    
    # 示例 3: 密钥持久化
    print("\n=== 示例 3: 密钥持久化 ===")
    key_file = "encryption_key.txt"
    DataEncryption.save_key(key, key_file)
    loaded_key = DataEncryption.load_key(key_file)
    encryptor3 = DataEncryption(loaded_key)
    decrypted_again = encryptor3.decrypt(encrypted)
    print(f"使用持久化密钥解密：{decrypted_again}")
    print(f"验证：{api_key == decrypted_again}")
    
    # 清理示例文件
    os.remove(key_file)
    print("\n所有示例完成！")
