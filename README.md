# Fit-Star Telegram Bot

Fit-Star Telegram Bot is a fitness-focused Telegram bot designed to assist beginner athletes with guides and advice. This bot was created specifically for one fitness coach to provide valuable resources and support to their clients.

## Configuration

Before deploying the Fit-Star Telegram Bot, ensure you set up the configuration properly in the `config.py` file. Here are the configurations you need to specify:

- `BOT_TOKEN`: Your Telegram Bot token.
- `ADMIN_IDS`: List of admin Telegram user IDs.
- `BOT_DB_PATH`: Path to the SQLite database file for storing user data.
- `PRIVATE_CHANNEL_ID`: ID of the private Telegram channel for the course content.
- `CHANNEL_INVITE_LINK`: Invite link to the private Telegram channel.
- `QUESTIONS_DB_PATH`: Path to the SQLite database file for storing user questions.
- `PAYMENTS_DB_PATH`: Path to the SQLite database file for storing payment details.

Ensure you fill in the appropriate values for each configuration parameter.

## Getting Started

To deploy the Fit-Star Telegram Bot, follow these steps:

1. Clone this repository to your local machine.
2. Set up the configuration in the `config.py` file as described above.
3. Install the necessary dependencies using `pip install -r requirements.txt`.
4. Run the bot using `python main.py`.

## Features

- **Fitness Guides**: Provides guides and advice tailored for beginner sports enthusiasts.
- **User Interaction**: Allows users to ask questions and receive assistance.
- **Private Channel Access**: Grants access to a private Telegram channel for course content.
- **Payment Handling**: Manages payment details securely using SQLite database.

## Usage

Once deployed, users can interact with the Fit-Star Telegram Bot by sending commands and accessing the available features. The bot provides a seamless experience for beginners to kickstart their fitness journey.

## Contributing

Contributions to the Fit-Star Telegram Bot are welcome! If you have suggestions, feature requests, or bug reports, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

