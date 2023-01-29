from BotService import app, bot


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url='https://jekafst.net/webhook')
    app.run()
