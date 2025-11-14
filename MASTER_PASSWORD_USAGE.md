# MASTER_PASSWORD 使用说明

## 📋 概述

`MASTER_PASSWORD` 是用于加密和解密 API 密钥的主密码。它在两个关键时刻被使用：

1. **迁移时（写入）**: 加密 API 密钥并保存到 `.keystore`
2. **运行时（读取）**: 解密 `.keystore` 中的密钥供程序使用

---

## 🔄 完整流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    迁移阶段 (Migrate)                        │
└─────────────────────────────────────────────────────────────┘

1. 你设置环境变量
   export MASTER_PASSWORD="MyStr0ng@Password"
                ↓
2. 运行迁移命令
   python security/encryption.py migrate
                ↓
3. 程序读取 MASTER_PASSWORD
   master_password = os.getenv('MASTER_PASSWORD')
                ↓
4. 派生加密密钥 (PBKDF2-HMAC-SHA256)
   salt = b'backpack-mm-salt'
   kdf = PBKDF2HMAC(SHA256, length=32, salt=salt, iterations=100000)
   encryption_key = kdf.derive(master_password.encode())
                ↓
5. 读取环境变量中的明文密钥
   BACKPACK_KEY="QjbyOsRIHHURKXqkp+pDlUCPf..."
   BACKPACK_SECRET="dziyjXcBYbnAsc7mribB6i4Y..."
                ↓
6. 加密密钥 (Fernet = AES-128-CBC + HMAC)
   data = {"backpack": {"api_key": "...", "secret_key": "..."}}
   encrypted = Fernet(encryption_key).encrypt(json.dumps(data))
                ↓
7. 保存到 .keystore 文件
   写入加密后的二进制数据
   设置文件权限: chmod 600 .keystore

┌─────────────────────────────────────────────────────────────┐
│                    运行阶段 (Runtime)                        │
└─────────────────────────────────────────────────────────────┘

1. 你设置相同的密码
   export MASTER_PASSWORD="MyStr0ng@Password"
                ↓
2. 运行策略
   python run.py --exchange backpack ...
                ↓
3. load_credentials('backpack') 被调用
                ↓
4. 程序读取 MASTER_PASSWORD
   master_password = os.getenv('MASTER_PASSWORD')
                ↓
5. 派生相同的加密密钥
   kdf = PBKDF2HMAC(SHA256, length=32, salt=salt, iterations=100000)
   encryption_key = kdf.derive(master_password.encode())
                ↓
6. 读取 .keystore 文件
   encrypted_data = open('.keystore', 'rb').read()
                ↓
7. 解密数据
   decrypted = Fernet(encryption_key).decrypt(encrypted_data)
   credentials = json.loads(decrypted)
                ↓
8. 提取 backpack 凭证
   backpack_creds = credentials['backpack']
   api_key = backpack_creds['api_key']
   secret_key = backpack_creds['secret_key']
                ↓
9. 使用密钥连接交易所
   client = BackpackClient(api_key, secret_key)
```

---

## 🔑 密码使用的三个关键点

### 1️⃣ 密钥派生 (Key Derivation)

**位置**: `security/encryption.py:48-70`

```python
def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
    """从主密码派生加密密钥"""
    salt = b'backpack-mm-salt'  # 固定盐值

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,                    # 生成32字节密钥
        salt=salt,
        iterations=100000,            # 100,000次迭代
    )

    # 将你的密码转换为加密密钥
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key
```

**作用**:
- 将你的密码（如 "MyPassword123"）转换为一个32字节的加密密钥
- 使用 100,000 次迭代增强安全性（防止暴力破解）

---

### 2️⃣ 加密数据 (Encryption)

**位置**: `security/encryption.py:72-106`

```python
def encrypt_credentials(self, credentials: Dict[str, str]) -> None:
    """加密并保存凭证"""

    # 准备数据
    data = {
        'backpack': {
            'api_key': 'QjbyOsRIHHURKXqkp+pDl...',
            'secret_key': 'dziyjXcBYbnAsc7mribB6i4Y...'
        }
    }

    # 转换为JSON
    json_data = json.dumps(data)

    # 使用派生的密钥加密
    encrypted_data = self.cipher.encrypt(json_data.encode())

    # 保存到文件
    with open('.keystore', 'wb') as f:
        f.write(encrypted_data)
```

**作用**:
- 将明文 API 密钥加密成无法读取的二进制数据
- 保存到 `.keystore` 文件

---

### 3️⃣ 解密数据 (Decryption)

**位置**: `security/encryption.py:111-134`

```python
def load_all_credentials(self) -> Dict[str, Dict[str, str]]:
    """加载所有加密的凭证"""

    # 读取加密文件
    with open('.keystore', 'rb') as f:
        encrypted_data = f.read()

    # 使用相同的密码派生密钥
    # 然后解密数据
    decrypted_data = self.cipher.decrypt(encrypted_data)
    credentials = json.loads(decrypted_data.decode())

    return credentials
```

**作用**:
- 用相同的密码解密 `.keystore`
- 如果密码错误，解密会失败并抛出异常

---

## 🔐 密码安全特性

### 1. PBKDF2-HMAC-SHA256

```python
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=b'backpack-mm-salt',
    iterations=100000  # ← 关键：100,000次迭代
)
```

**防护效果**:
- 即使攻击者获得 `.keystore` 文件
- 暴力破解需要对每个密码尝试进行 100,000 次哈希运算
- 假设攻击者每秒尝试 1,000,000 个密码
- 破解一个12字符密码需要约 **千年时间**

---

### 2. Fernet (AES-128-CBC + HMAC)

```python
cipher = Fernet(encryption_key)
encrypted = cipher.encrypt(data)
```

**组合加密**:
- **AES-128-CBC**: 对称加密算法
- **HMAC**: 消息认证码，防止篡改

**防护效果**:
- 数据即使被截获也无法读取
- 任何修改都会被检测到

---

## 📂 文件内容示例

### .keystore 文件（加密后）

```
$ hexdump -C .keystore | head -5
00000000  67 41 41 41 41 42 68 54  4e 72 65 53 46 62 76 50  |gAAAAABhTNreSFbvP|
00000010  63 78 4f 59 77 73 50 78  6d 51 35 5a 42 4b 78 33  |cxOYwsPxmQ5ZBKx3|
00000020  47 6e 6a 71 6c 38 78 78  72 35 68 76 32 78 4d 78  |Gnjql8xxr5hv2xMx|
...
```
→ **完全无法读取**，只是二进制加密数据

---

### 解密后的数据（内存中）

```json
{
  "backpack": {
    "exchange": "backpack",
    "api_key": "QjbyOsRIHHURKXqkp+pDlUCPf8HqfLGNxjRY64BW9RM=",
    "secret_key": "dziyjXcBYbnAsc7mribB6i4Yuk+U5S6bA8V0CVzSkZM="
  },
  "aster": {
    "exchange": "aster",
    "api_key": "...",
    "secret_key": "..."
  }
}
```
→ **仅在程序运行时存在于内存中**

---

## 🎯 使用场景对比

### 场景 1: 迁移密钥

```bash
# 步骤1: 设置主密码
export MASTER_PASSWORD="MyStr0ng@Password123"

# 步骤2: 设置要迁移的明文密钥（临时）
export BACKPACK_KEY="QjbyOsRIHHURKXqkp+pDlUCPf..."
export BACKPACK_SECRET="dziyjXcBYbnAsc7mribB6i4Y..."

# 步骤3: 运行迁移
python security/encryption.py migrate

# 结果:
# ✅ 已迁移 backpack 的凭证到加密存储
# 创建文件: .keystore (加密后的密钥)

# 步骤4: 删除明文环境变量（可选但推荐）
unset BACKPACK_KEY
unset BACKPACK_SECRET
```

**MASTER_PASSWORD 用途**:
- ✅ 派生加密密钥
- ✅ 加密 API 密钥
- ✅ 写入 `.keystore`

---

### 场景 2: 运行策略

```bash
# 只需要设置主密码（相同的密码）
export MASTER_PASSWORD="MyStr0ng@Password123"

# 直接运行
python run.py --exchange backpack --symbol SOL_USDC_PERP ...

# 内部流程:
# 1. load_credentials('backpack') 被调用
# 2. 读取 MASTER_PASSWORD
# 3. 派生相同的加密密钥
# 4. 解密 .keystore
# 5. 提取 backpack 的 api_key 和 secret_key
# 6. 使用密钥连接交易所
```

**MASTER_PASSWORD 用途**:
- ✅ 派生解密密钥（必须与迁移时相同）
- ✅ 解密 `.keystore`
- ✅ 提取明文密钥供程序使用

---

### 场景 3: 错误的密码

```bash
# 迁移时使用密码 A
export MASTER_PASSWORD="Password_A"
python security/encryption.py migrate  # 创建 .keystore

# 运行时使用密码 B（错误）
export MASTER_PASSWORD="Password_B"
python run.py --exchange backpack ...

# 结果:
# ❌ cryptography.fernet.InvalidToken
# ❌ 解密凭证失败
```

**原因**:
- 密码不同 → 派生的密钥不同 → 无法解密

---

## ⚠️ 重要注意事项

### 1. 密码必须一致

```
迁移时的密码 = 运行时的密码
```

如果忘记密码，**必须重新迁移**：
```bash
rm .keystore  # 删除旧的
export MASTER_PASSWORD="new-password"
python security/encryption.py migrate
```

---

### 2. 密码安全性建议

**强密码示例**:
```bash
✅ MyVeryStr0ng@Password!2024
✅ Tr@d1ng$ecure#Key2024
✅ B@ckp@ck#Secure!Pass123
```

**弱密码**:
```bash
❌ password
❌ 123456
❌ backpack
```

**检查强度**:
```bash
# 至少 16 个字符
# 包含: 大写字母 + 小写字母 + 数字 + 特殊字符
```

---

### 3. 密码存储位置

**推荐方式** (按优先级):

1. **密码管理器** (最安全)
   - 1Password, LastPass, Bitwarden
   - 存储为安全笔记

2. **服务器环境变量文件**
   ```bash
   # ~/.bash_profile 或 ~/.bashrc
   export MASTER_PASSWORD="your-password"
   ```

3. **系统密钥环** (macOS/Linux)
   ```bash
   # macOS Keychain
   security add-generic-password -a "$USER" -s "backpack-mm" -w "your-password"

   # 读取
   MASTER_PASSWORD=$(security find-generic-password -a "$USER" -s "backpack-mm" -w)
   ```

**不推荐**:
❌ 硬编码在脚本中
❌ 写在 `.env` 文件中（如果 `.env` 被提交到 git）
❌ 写在纸上或未加密的文件中

---

## 🔄 密码轮换

如果需要更换密码：

```bash
# 1. 设置新密码
export MASTER_PASSWORD="new-strong-password"

# 2. 删除旧密钥库
rm .keystore

# 3. 重新迁移（需要重新设置明文密钥或从旧密码解密）
# 方法 A: 重新设置环境变量
export BACKPACK_KEY="..."
export BACKPACK_SECRET="..."
python security/encryption.py migrate

# 方法 B: 从旧密钥库导出后重新加密
export OLD_PASSWORD="old-password"
python -c "
from security.encryption import KeyEncryption
old = KeyEncryption(master_password='$OLD_PASSWORD', key_file='.keystore.old')
new = KeyEncryption(master_password='$MASTER_PASSWORD', key_file='.keystore')
for exchange, creds in old.load_all_credentials().items():
    new.encrypt_credentials(creds)
"
```

---

## 📊 数据流总结

```
【迁移阶段】
你的密码 (MASTER_PASSWORD)
    ↓ (PBKDF2-HMAC-SHA256, 100k iterations)
派生的加密密钥 (32 bytes)
    ↓
Fernet cipher 对象
    ↓ (AES-128-CBC + HMAC)
加密的 API 密钥
    ↓
.keystore 文件 (二进制加密数据)

【运行阶段】
你的密码 (MASTER_PASSWORD)
    ↓ (相同的 PBKDF2 过程)
派生的解密密钥 (必须相同)
    ↓
Fernet cipher 对象
    ↓ (解密)
.keystore 文件 → 明文 API 密钥
    ↓
程序内存中使用
    ↓
连接交易所
```

---

## 🎓 总结

**MASTER_PASSWORD 的作用**:
1. ✅ **迁移时**: 将明文密钥加密并保存到 `.keystore`
2. ✅ **运行时**: 解密 `.keystore` 并提取密钥供程序使用
3. ✅ **保护**: 即使 `.keystore` 被盗，没有密码也无法解密

**关键点**:
- 🔑 **一个密码，两次使用**: 加密时用一次，解密时用一次
- 🔒 **强加密**: PBKDF2 (100k iterations) + AES-128 + HMAC
- 🛡️ **安全性**: 即使文件被盗也无法读取
- 🔄 **便利性**: 只需记住一个主密码，不需要每次设置多个密钥

**最佳实践**:
1. 使用强密码（16+ 字符）
2. 密码存储在密码管理器中
3. 定期轮换密码
4. 删除 `.env` 中的明文密钥
5. 备份 `.keystore` 文件（加密后的，但仍需密码才能使用）

---

**文档版本**: 1.0
**最后更新**: 2025-11-14
