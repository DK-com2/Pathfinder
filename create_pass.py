import bcrypt

def hash_password(password: str) -> str:
    """パスワードをハッシュ化して返す"""
    salt = bcrypt.gensalt()  # ランダムなソルトを生成
    hashed_password = bcrypt.hashpw(password.encode(), salt)  # ハッシュ化
    return hashed_password.decode()  


password = input("保存するパスワードを入力してください: ")
hashed = hash_password(password)

print("\n🔹 ハッシュ化されたパスワード (これをDBに保存してください) 🔹")
print(hashed)