from api_gateway.gateway import APIGateway
from token_manager.manager import TokenManager

if __name__ == "__main__":
    secret = "supersecret"
    manager = TokenManager(secret)
    access_token, refresh_token = manager.generate_tokens("vu van trung")

    print("Access Token:", access_token)
    print("Refresh Token:", refresh_token)

    # Luu token ra file de tranh loi dut dong khi copy tay
    with open("token.txt", "w") as f:
        f.write(access_token)

    gateway = APIGateway(secret)
    gateway.run()
