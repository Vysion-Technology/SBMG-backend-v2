from argon2 import PasswordHasher


hasher = PasswordHasher()

hasher.verify(
    "$argon2id$v=19$m=65536,t=3,p=4$4YRykYbKnD74KdiXlfK5Zw$qbUMJJ+ASeImzAeOjh0Gz0unMcarWT4CpdnDIafZaTQ",
    "A7PMZPXU76w",
)
