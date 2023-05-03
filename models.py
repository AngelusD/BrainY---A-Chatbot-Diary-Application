from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import aliased
from sqlalchemy import and_




db = SQLAlchemy()


# User model has columns for id, username, and password_hash. 
# It also has a relationship field logs to the Log table, which is defined as a one-to-many relationship.

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    logs = db.relationship('Log', back_populates='user', lazy=True)  

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Conversation model has columns for id, user_id, content, last_input, user_input_counter, and last_question_timestamp. 
# It also has a relationships field logs, which is defined as a one-to-many relationship with the Log table.

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    logs = db.relationship('Log', back_populates='conversation', lazy=True)
    last_input = db.Column(db.Text, nullable=True)
    user_input_counter = db.Column(db.Integer, default=0)  
    last_question_timestamp =db.Column(db.DateTime, nullable=True)

    
    


# Log model has columns for id, conversation_id, summary, timestamp, and user_id. It also has relationships fields user and conversation. 
# The user relationship is defined as a many-to-one relationship with the User table, 
# while the conversation relationship is defined as a many-to-one relationship with the Conversation table.

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    summary = db.Column(db.Text, nullable=True)  
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", back_populates="logs")  

    conversation = db.relationship("Conversation", back_populates="logs")



# Habit, Activity, Goal, Mood, and Thought models define four additional tables with the following columns respectively:
# id, log_id, and habit; id, log_id, and activity; id, log_id, and goal; id, log_id, and mood; id, log_id, and thought. 
# They all have a log relationship field which refers back to the instance of the Log on which they were added.

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('log.id'), nullable=False)  # Add log_id
    habit = db.Column(db.Text, nullable=False)
    log = db.relationship("Log", backref=db.backref("habits"))
    

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('log.id'), nullable=False)
    activity = db.Column(db.Text, nullable=False)
    log = db.relationship("Log", backref=db.backref("activities"))

    

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('log.id'), nullable=False)  # Add log_id
    goal = db.Column(db.Text, nullable=False)
    log = db.relationship("Log", backref=db.backref("Goal"))
    

class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('log.id'), nullable=False)  # Add log_id
    mood = db.Column(db.String(80), nullable=False)
    log = db.relationship("Log", backref=db.backref("moods"))
    

class Thought(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    log_id = db.Column(db.Integer, db.ForeignKey('log.id'), nullable=False)  # Add log_id
    thought = db.Column(db.Text, nullable=False)
    log = db.relationship("Log", backref=db.backref('thoughts'))
    



