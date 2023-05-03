# BrainY---A-Chatbot-Diary-Application
AI-powered personal diary companion. Engage in conversations to share your daily experiences, emotions, and thoughts. Receive insightful analysis and automatic diary entries based on your conversations.


## Features

* User registration and login
* Open-domain conversations with the chatbot
* Generation of a diary entry summarizing the conversation and highlighting key points
* Viewing past diary entries and summaries

## Local Setup

Follow the steps below to setup the application locally:

1. **Clone the repository**

   ```
   git clone https://github.com/AngelusD/BrainY---A-Chatbot-Diary-Application
   ```

2. **Create and activate a virtual environment**

   ```
   python3 -m venv env
   source env/bin/activate  # On Windows, use `env\Scripts\activate`
   ```

3. **Install the required packages**

   ```
   pip install -r requirements.txt
   ```

4. **Set environment variables**

   You need to set the following environment variables:

   `CHATBOT_DIARY_SECRET_KEY` - Set a secret key for your Flask app

   `OPENAI_API_KEY` - Obtain an API key from OpenAI

5. **Run the app**

   ```
   flask run
   ```
   
The app will be served at http://localhost:5000/. Access the web interface and start chatting with your AI assistant!

## Technologies Used

* Flask - Python web framework
* Flask-SQLAlchemy - ORM toolkit to interact with the database
* OpenAI GPT-3 - Used to generate responses for the chatbot and generate diary entries
* HTML, CSS, JavaScript - Frontend of the web app
