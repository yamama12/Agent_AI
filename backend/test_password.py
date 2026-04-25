from api.security import hash_password, verify_password

pwd = "superadmin123"
hashed = hash_password(pwd)

print("HASH:", hashed)
print("VERIFY:", verify_password(pwd, hashed))