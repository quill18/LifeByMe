# LifeByMe

An AI-powered life simulation game created by Martin "quill18" Glaude.

![Screenshot 2024-11-11 125911](https://github.com/user-attachments/assets/1ae9c96a-b56d-42b7-9c0f-c336330f6153)

## About

LifeByMe is a life simulation game where you create and guide a character through their life journey, starting as a high school student. Each choice you make shapes your character's personality traits, stress levels, and relationships with other characters. The game uses AI (powered by OpenAI's API) to generate rich, contextual stories that respond to your character's current state and history.

Key features:
- Create your own character with custom traits and background
- Experience dynamically generated stories that adapt to your character's personality
- Develop relationships with AI-generated characters
- Build a collection of memories that influence future interactions
- Watch your character's personality evolve based on your choices

## Development Status

This project is currently in a semi-complete, playable stage awaiting playtesting. It was started as an exercise in working with the OpenAI API, as well as learning what it's like to develop software through the use of an AI Assitant: It was programmed almost entirely with the assistance of Claude 3.5 Sonnet (Anthropic's AI assistant). While I have a long history of web development experience, it has not been my day job for some time and I explicitly chose Python because it's not a language I'm very familiar with so I would be required to lean on the AI for the actual code generation.

The code is made available under GPL Version 3, and users are encouraged to fork and create their own customized versions of this application. If any fork becomes dominant or widely embraced by the community, please contact me (quill18@quill18.com) so I can include a link here. I don't personally intend to continue long-term development, and I would love to officially "bless" a community fork.

## Planned Features

While I don't plan to do long-term development on the project, I do intend to address these specific limitations:

* **Time Progression**: Currently lacking a proper time system. Plan is to divide gameplay into seasons (starting with Fall of the character's Junior year of High School at 16 years old), with characters aging up one year every 4 seasons. Less important memories would naturally fade during these transitions.

* **Life Stage Changes**: Planning to implement progression from High School (2 years/8 seasons) to either College or Adulthood, with appropriate memory aging and character roster updates.

* **Directed Stories**: In addition to random stories, add ability for players to request stories focused on specific traits, memories, or characters, with the option to guide development in particular directions (e.g., Romance-Development Stories, Skill-Development Stories, etc...)

## Installation

### Requirements

I'm not sure if these are strict requirements, but this is what I was developing on:
- Python 3.10+ ([Download](https://www.python.org/downloads/))
- MongoDB 8.0+ ([Download](https://www.mongodb.com/try/download/community))

In addition, you'll need your own, paid, OpenAI API Key ([Get One Here](https://platform.openai.com/api-keys)) Note that this application runs entirely on your local machine (except for API calls to OpenAI), and your API key and all other data are stored only on your computer. Usage costs seem extremely low.

### Setup Instructions

1. Clone the repository:
```
git clone https://github.com/quill18/LifeByMe.git
cd LifeByMe
```

2. Create and activate a virtual environment:

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```
Note: If you encounter permission issues, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open `http://127.0.0.1:5000/` in your web browser

You'll need to create an account and provide your OpenAI API key during registration. Again, this is stored entirely on your own computer.

## Support

Due to time constraints and my limited experience with Python (most of this code was generated by Claude 3.5 Sonnet), I unfortunately cannot provide extensive troubleshooting support. You're encouraged to fork the project and modify it to suit your needs!

## Author

Martin "quill18" Glaude
- Email: quill18@quill18.com
- Gaming Channel: [youtube.com/quill18](https://youtube.com/quill18)
- Programming Channel: [youtube.com/quill18creates](https://youtube.com/quill18creates)

## License

This project is licensed under GPL Version 3 - see the LICENSE file for details.
