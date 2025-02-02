from twilio.rest import Client
def send_otp_phone():


    account_sid = "AC63c4c8107c93726e1cee04f1910264ad"
    auth_token = "d6997c1c330ea7b668c76b147761d621"
    client = Client(account_sid, auth_token)

    message= client.messages.create(
      from_="+12186338258",
      body='HELLO',
      to="+917736609861",
      
    )

    print(message.sid)

send_otp_phone()