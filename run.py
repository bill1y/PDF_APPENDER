if __name__ == "__main__":
    import os
    import uvicorn
    from pyngrok import ngrok
    from src.fastapi_app.main import app
    import pyfiglet

    port = int(os.getenv('SERVER_PORT', 8080))
    ngrok_domain=os.getenv('NGROK_DOMAIN')
    ngrok_token=os.getenv('NGROK_TOKEN')
    ngrok.set_auth_token(ngrok_token)
    public_url = ngrok.connect(port, domain=ngrok_domain)
    print(f"------------- NGROK tunnel is opened: {public_url} -------------")


    ascii_art = pyfiglet.figlet_format("Hi, Shish!")
    print(ascii_art)

    uvicorn.run(app, host="0.0.0.0", port=port)
