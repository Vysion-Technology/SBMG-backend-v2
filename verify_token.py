from jose import jwt, JWTError

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3NzgxNDAwMX0.6gdubJGi35eRrley9ke7ZNE5X8l1Jj0CDRMt1OJoZnA"
secret = "your-secret-key-here-change-in-production"
algo = "HS256"

try:
    payload = jwt.decode(token, secret, algorithms=[algo])
    print(f"Valid! Payload: {payload}")
except JWTError as e:
    print(f"Invalid! Error: {e}")
