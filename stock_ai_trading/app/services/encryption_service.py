"""
API密钥加密存储服务
提供安全的API密钥加密、解密和哈希功能
"""

import os
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EncryptionService:
    """API密钥加密服务"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        初始化加密服务
        
        Args:
            master_key: 主密钥，如果不提供则从环境变量获取
        """
        self.master_key = master_key or os.getenv('ENCRYPTION_MASTER_KEY', 'default_master_key_change_in_production')
        self.salt = b'stable_salt_for_key_derivation'  # 在生产环境中应该使用随机盐
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """获取Fernet加密实例"""
        if self._fernet is None:
            # 从主密钥派生加密密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self.salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 要加密的明文
            
        Returns:
            加密后的字符串（Base64编码）
        """
        try:
            if not plaintext:
                return ""
            
            fernet = self._get_fernet()
            encrypted_bytes = fernet.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"加密失败: {str(e)}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串
        
        Args:
            ciphertext: 要解密的密文（Base64编码）
            
        Returns:
            解密后的明文
        """
        try:
            if not ciphertext:
                return ""
            
            fernet = self._get_fernet()
            encrypted_bytes = base64.urlsafe_b64decode(ciphertext.encode('utf-8'))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"解密失败: {str(e)}")
    
    def hash_key(self, key: str) -> str:
        """
        生成密钥的哈希值（用于验证）
        
        Args:
            key: 要哈希的密钥
            
        Returns:
            SHA256哈希值（十六进制字符串）
        """
        try:
            if not key:
                return ""
            
            # 使用SHA256生成哈希
            hash_object = hashlib.sha256()
            hash_object.update(key.encode('utf-8'))
            return hash_object.hexdigest()
        except Exception as e:
            logger.error(f"Hashing failed: {e}")
            raise ValueError(f"哈希生成失败: {str(e)}")
    
    def verify_key(self, key: str, hash_value: str) -> bool:
        """
        验证密钥是否匹配哈希值
        
        Args:
            key: 要验证的密钥
            hash_value: 存储的哈希值
            
        Returns:
            是否匹配
        """
        try:
            return self.hash_key(key) == hash_value
        except Exception as e:
            logger.error(f"Key verification failed: {e}")
            return False
    
    def generate_key(self) -> str:
        """
        生成新的加密密钥
        
        Returns:
            新的Fernet密钥（Base64编码）
        """
        return Fernet.generate_key().decode('utf-8')

# 全局加密服务实例
encryption_service = EncryptionService()