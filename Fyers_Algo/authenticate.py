from fyers_apiv3 import fyersModel
import webbrowser

# Replace these with your actual Fyers App details
CLIENT_ID = "91I39L89HO-100" 
SECRET_KEY = "STOLNOHN4C"  # Get this from your Fyers API Dashboard
REDIRECT_URI = "https://127.0.0.1/" # Must match what you set in Fyers Dashboard

def generate_daily_token():
    # 1. Initialize the Session
    session = fyersModel.SessionModel(
        client_id=CLIENT_ID,
        secret_key=SECRET_KEY,
        redirect_uri=REDIRECT_URI,
        response_type="code",
        grant_type="authorization_code"
    )

    # 2. Generate the Login URL and open it in your browser
    auth_link = session.generate_authcode()
    print("🌐 Opening Browser for Fyers Login...")
    print(f"If browser doesn't open, click here:\n{auth_link}\n")
    webbrowser.open(auth_link)

    # 3. After you log in, Fyers redirects you to an error page (127.0.0.1)
    # The URL will look like: https://127.0.0.1/?auth_code=XXXXXXXXX&state=None
    # Copy that XXXXXXXXX part and paste it below.
    auth_code = input("Enter the 'auth_code' from the URL: ")

    # 4. Exchange Auth Code for Access Token
    session.set_token(auth_code)
    response = session.generate_token()

    if response.get("s") == "ok":
        access_token = response["access_token"]
        print("\n✅ SUCCESS! Here is your Access Token for today:")
        print("="*60)
        print(access_token)
        print("="*60)
        print("Copy this entire string and paste it into ACCESS_TOKEN in your main trading bot.")
    else:
        print(f"❌ Failed to generate token: {response}")

if __name__ == "__main__":
    generate_daily_token()