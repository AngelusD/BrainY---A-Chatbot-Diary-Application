from models import User, Log, Conversation
from datetime import datetime, timedelta
from flask import Flask
from models import db
from main import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot_diary.db'
db.init_app(app)

def generate_summaries_for_all_users():
    with app.app_context():
        # Get current date and time
        now = datetime.now()
        # Check if it's 12 am
        if now.hour == 0:
            # Get all users
            users = User.query.all()
            for user in users:
                # Check if there was a conversation for the user today
                conversation = Conversation.query.filter(Conversation.timestamp >= now.date(), Conversation.user_id == user.id).first()
                if conversation:
                    # Check if a summary was generated for the user today
                    log = Log.query.filter(Log.timestamp >= now.date(), Log.user_id == user.id).first()
                    if not log:
                        # If not, generate the summary
                        end_conversation_and_generate_diary(user.id)

if __name__ == '__main__':
    generate_summaries_for_all_users()
