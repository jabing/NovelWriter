"""加密工具测试模块

测试 DataEncryption 类的加密解密功能。
"""

import pytest
import os
import sys
from pathlib import Path

# 添加 LSP 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'LSP'))

from novelwriter_lsp.utils.encryption import DataEncryption


class TestDataEncryptionBasic:
    """基础加密解密测试"""
    
    def test_encrypt_decrypt_string(self):
        """测试字符串加密和解密"""
        encryptor = DataEncryption()
        original = "Hello, World!"
        
        encrypted = encryptor.encrypt(original)
        decrypted = encryptor.decrypt(encrypted)
        
        assert original == decrypted
        assert encrypted != original  # 确保已加密
        assert len(encrypted) > len(original)  # 加密后应该更长
    
    def test_encrypt_decrypt_empty_string(self):
        """测试空字符串加密"""
        encryptor = DataEncryption()
        original = ""
        
        encrypted = encryptor.encrypt(original)
        decrypted = encryptor.decrypt(encrypted)
        
        assert original == decrypted
    
    def test_encrypt_decrypt_unicode(self):
        """测试 Unicode 字符串加密"""
        encryptor = DataEncryption()
        original = "你好，世界！🌍 Привет мир!"
        
        encrypted = encryptor.encrypt(original)
        decrypted = encryptor.decrypt(encrypted)
        
        assert original == decrypted
    
    def test_encrypt_non_string_raises_error(self):
        """测试非字符串输入抛出错误"""
        encryptor = DataEncryption()
        
        with pytest.raises(TypeError):
            encryptor.encrypt(123)
        
        with pytest.raises(TypeError):
            encryptor.encrypt(None)
    
    def test_decrypt_non_string_raises_error(self):
        """测试非字符串解密输入抛出错误"""
        encryptor = DataEncryption()
        
        with pytest.raises(TypeError):
            encryptor.decrypt(123)


class TestAPIKeyEncryption:
    """API 密钥加密测试"""
    
    def test_encrypt_decrypt_api_key(self):
        """测试 API 密钥加密和解密"""
        encryptor = DataEncryption()
        api_key = "sk-1234567890abcdef1234567890abcdef"
        
        encrypted = encryptor.encrypt_api_key(api_key)
        decrypted = encryptor.decrypt_api_key(encrypted)
        
        assert api_key == decrypted
        assert encrypted != api_key
    
    def test_api_key_format_preserved(self):
        """测试 API 密钥格式保持"""
        encryptor = DataEncryption()
        api_keys = [
            "sk-abc123",
            "Bearer token123",
            "api_key_9876543210",
            "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        ]
        
        for key in api_keys:
            encrypted = encryptor.encrypt_api_key(key)
            decrypted = encryptor.decrypt_api_key(encrypted)
            assert key == decrypted
    
    def test_multiple_api_keys_independent(self):
        """测试多个 API 密钥独立加密"""
        encryptor = DataEncryption()
        key1 = "api_key_1"
        key2 = "api_key_2"
        
        encrypted1 = encryptor.encrypt_api_key(key1)
        encrypted2 = encryptor.encrypt_api_key(key2)
        
        # 确保加密结果不同
        assert encrypted1 != encrypted2
        
        # 确保解密正确
        assert encryptor.decrypt_api_key(encrypted1) == key1
        assert encryptor.decrypt_api_key(encrypted2) == key2


class TestSensitiveDataEncryption:
    """敏感数据加密测试"""
    
    def test_encrypt_decrypt_dict(self):
        """测试字典数据加密和解密"""
        encryptor = DataEncryption()
        data = {
            "username": "admin",
            "password": "secret123",
            "token": "abc-xyz-789"
        }
        
        encrypted = encryptor.encrypt_sensitive_data(data)
        decrypted = encryptor.decrypt_sensitive_data(encrypted)
        
        assert data == decrypted
    
    def test_nested_dict_encryption(self):
        """测试嵌套字典加密"""
        encryptor = DataEncryption()
        data = {
            "user": {
                "name": "John",
                "credentials": {
                    "api_key": "sk-123",
                    "secret": "xyz"
                }
            }
        }
        
        encrypted = encryptor.encrypt_sensitive_data(data)
        decrypted = encryptor.decrypt_sensitive_data(encrypted)
        
        assert data == decrypted
    
    def test_empty_dict_encryption(self):
        """测试空字典加密"""
        encryptor = DataEncryption()
        data = {}
        
        encrypted = encryptor.encrypt_sensitive_data(data)
        decrypted = encryptor.decrypt_sensitive_data(encrypted)
        
        assert data == decrypted


class TestKeyManagement:
    """密钥管理测试"""
    
    def test_generate_key(self):
        """测试密钥生成"""
        key1 = DataEncryption.generate_key()
        key2 = DataEncryption.generate_key()
        
        # 确保生成的密钥不同
        assert key1 != key2
        # 确保密钥长度合理（Fernet 密钥是 32 字节的 base64 编码）
        assert len(key1) > 30
    
    def test_custom_key_initialization(self):
        """测试使用自定义密钥初始化"""
        key = DataEncryption.generate_key()
        encryptor = DataEncryption(key)
        
        data = "test data"
        encrypted = encryptor.encrypt(data)
        decrypted = encryptor.decrypt(encrypted)
        
        assert data == decrypted
    
    def test_same_key_same_result(self):
        """测试相同密钥产生相同加密器"""
        key = DataEncryption.generate_key()
        encryptor1 = DataEncryption(key)
        encryptor2 = DataEncryption(key)
        
        data = "test data"
        encrypted1 = encryptor1.encrypt(data)
        encrypted2 = encryptor2.encrypt(data)
        
        # 使用相同密钥可以互相解密
        assert encryptor1.decrypt(encrypted2) == data
        assert encryptor2.decrypt(encrypted1) == data
    
    def test_different_key_cannot_decrypt(self):
        """测试不同密钥无法解密"""
        key1 = DataEncryption.generate_key()
        key2 = DataEncryption.generate_key()
        
        encryptor1 = DataEncryption(key1)
        encryptor2 = DataEncryption(key2)
        
        data = "secret data"
        encrypted = encryptor1.encrypt(data)
        
        # 使用错误的密钥应该抛出异常
        with pytest.raises(Exception):  # cryptography.fernet.InvalidToken
            encryptor2.decrypt(encrypted)
    
    def test_save_and_load_key(self, tmp_path):
        """测试密钥保存和加载"""
        key = DataEncryption.generate_key()
        key_file = tmp_path / "test_key.txt"
        
        # 保存密钥
        DataEncryption.save_key(key, str(key_file))
        
        # 验证文件权限（Unix 系统）
        if os.name != 'nt':  # 非 Windows 系统
            file_mode = os.stat(str(key_file)).st_mode & 0o777
            assert file_mode == 0o600  # 仅所有者可读写
        
        # 加载密钥
        loaded_key = DataEncryption.load_key(str(key_file))
        
        assert key == loaded_key
        
        # 使用加载的密钥加密解密
        encryptor = DataEncryption(loaded_key)
        data = "test"
        encrypted = encryptor.encrypt(data)
        decrypted = encryptor.decrypt(encrypted)
        assert data == decrypted


class TestEncryptionDeterminism:
    """加密随机性测试"""
    
    def test_same_input_different_output(self):
        """测试相同输入产生不同输出（Fernet 特性）"""
        encryptor = DataEncryption()
        data = "same data"
        
        encrypted1 = encryptor.encrypt(data)
        encrypted2 = encryptor.encrypt(data)
        
        # Fernet 加密包含时间戳和随机 IV，所以每次加密结果不同
        assert encrypted1 != encrypted2
        
        # 但都能正确解密
        assert encryptor.decrypt(encrypted1) == data
        assert encryptor.decrypt(encrypted2) == data


class TestEdgeCases:
    """边界情况测试"""
    
    def test_very_long_string(self):
        """测试长字符串加密"""
        encryptor = DataEncryption()
        data = "A" * 10000
        
        encrypted = encryptor.encrypt(data)
        decrypted = encryptor.decrypt(encrypted)
        
        assert data == decrypted
    
    def test_special_characters(self):
        """测试特殊字符加密"""
        encryptor = DataEncryption()
        data = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        encrypted = encryptor.encrypt(data)
        decrypted = encryptor.decrypt(encrypted)
        
        assert data == decrypted
    
    def test_newlines_and_tabs(self):
        """测试换行符和制表符"""
        encryptor = DataEncryption()
        data = "Line 1\nLine 2\tTabbed\r\nWindows"
        
        encrypted = encryptor.encrypt(data)
        decrypted = encryptor.decrypt(encrypted)
        
        assert data == decrypted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
