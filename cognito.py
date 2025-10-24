import boto3, json, time, random, string, os

# ---------- CONFIGURATION ----------
REGION = "us-east-1"
USER_POOL_NAME = "demo-userpool-" + ''.join(random.choices(string.ascii_lowercase, k=5))
IDENTITY_POOL_NAME = "demo-identitypool-" + ''.join(random.choices(string.ascii_lowercase, k=5))
USERNAME = "demo_user"
PASSWORD = "DemoUser@123"
EMAIL = "demo_user@example.com"

# ---------- CLIENTS ----------
cognito_idp = boto3.client('cognito-idp', region_name=REGION)
cognito_identity = boto3.client('cognito-identity', region_name=REGION)

print("\n🚀 Starting AWS Cognito Demo...\n")

# ---------- CREATE USER POOL ----------
print("🔹 Creating User Pool...")
pool = cognito_idp.create_user_pool(PoolName=USER_POOL_NAME)
user_pool_id = pool['UserPool']['Id']
print(f"✅ User Pool created: {user_pool_id}")

# ---------- CREATE APP CLIENT ----------
print("🔹 Creating App Client...")
app_client = cognito_idp.create_user_pool_client(
    UserPoolId=user_pool_id,
    ClientName='demo-app-client',
    GenerateSecret=False,
    ExplicitAuthFlows=['ALLOW_USER_PASSWORD_AUTH', 'ALLOW_REFRESH_TOKEN_AUTH', 'ALLOW_USER_SRP_AUTH'],
    AllowedOAuthFlows=['code', 'implicit'],
    AllowedOAuthScopes=['email', 'openid', 'aws.cognito.signin.user.admin'],
    SupportedIdentityProviders=['COGNITO'],
    CallbackURLs=['https://example.com/callback']
)
client_id = app_client['UserPoolClient']['ClientId']
print(f"✅ App Client created: {client_id}")

# ---------- CREATE USER ----------
print("🔹 Creating test user...")
cognito_idp.admin_create_user(
    UserPoolId=user_pool_id,
    Username=USERNAME,
    UserAttributes=[
        {'Name': 'email', 'Value': EMAIL},
        {'Name': 'email_verified', 'Value': 'true'}
    ],
    MessageAction='SUPPRESS'
)

# Set password and confirm
cognito_idp.admin_set_user_password(
    UserPoolId=user_pool_id,
    Username=USERNAME,
    Password=PASSWORD,
    Permanent=True
)
print(f"✅ User created and confirmed: {USERNAME}")

# ---------- AUTHENTICATION FLOW ----------
print("🔹 Authenticating using SRP (USER_PASSWORD_AUTH)...")
auth_response = cognito_idp.initiate_auth(
    ClientId=client_id,
    AuthFlow='USER_PASSWORD_AUTH',
    AuthParameters={'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
)

id_token = auth_response['AuthenticationResult']['IdToken']
access_token = auth_response['AuthenticationResult']['AccessToken']
refresh_token = auth_response['AuthenticationResult']['RefreshToken']

print("\n🔑 Cognito Tokens:")
print("ID Token:", id_token[:60] + "...")       # shortened for display
print("Access Token:", access_token[:60] + "...")
print("Refresh Token:", refresh_token[:60] + "...")

# ---------- CREATE IDENTITY POOL ----------
print("\n🔹 Creating Identity Pool (federation demo)...")
id_pool = cognito_identity.create_identity_pool(
    IdentityPoolName=IDENTITY_POOL_NAME,
    AllowUnauthenticatedIdentities=False,
    CognitoIdentityProviders=[{
        'ProviderName': f'cognito-idp.{REGION}.amazonaws.com/{user_pool_id}',
        'ClientId': client_id
    }]
)
identity_pool_id = id_pool['IdentityPoolId']
print(f"✅ Identity Pool created: {identity_pool_id}")

# ---------- DEMO COMPLETE ----------
print("\n🎯 Demo Summary:")
print(json.dumps({
    "UserPoolId": user_pool_id,
    "AppClientId": client_id,
    "IdentityPoolId": identity_pool_id,
    "Username": USERNAME,
    "AuthenticationFlow": "USER_PASSWORD_AUTH (SRP)",
    "Tokens": {
        "ID": id_token[:60] + "...",
        "Access": access_token[:60] + "...",
        "Refresh": refresh_token[:60] + "..."
    }
}, indent=2))

# ---------- CLEANUP ----------
print("\n🧹 Cleaning up resources in 5 seconds...")
time.sleep(5)
cognito_idp.delete_user_pool(UserPoolId=user_pool_id)
cognito_identity.delete_identity_pool(IdentityPoolId=identity_pool_id)
print("✅ Cleanup complete. Demo finished successfully.")
