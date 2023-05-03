from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from models import db, User, Conversation, Log, Mood, Goal, Activity, Habit, Thought
from sqlalchemy import or_
from datetime import datetime, timedelta
from transformers import GPT2Tokenizer
import torch
import os
import openai
import re
import random
import requests


#sets an environment variable for the Tokenizers library to disable parallelism
os.environ["TOKENIZERS_PARALLELISM"] = "false"


diary_path = 'diaries'

#Flask App is created with a secret_key and is configured to use a SQLite database. SQLAlchemy is used to interact with the database.
app = Flask(__name__)
app.secret_key = "123456"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot_diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#all the defined models are created by calling db.create_all().
with app.app_context():
    db.create_all()


#6 routes for index, login, register, chat, view summary and past summaries

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Registration route
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return redirect(url_for('chat', user_id=user.id))
        else:
            error = "Invalid credentials. Please register if you don't have an account."
            return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
def chat(user_id):
    user = db.session.get(User, user_id)

    if request.method == 'POST':
        # Process user input and generate chatbot response
        message = request.json['message']
        response = generate_chatbot_response(user_id, message)
        return jsonify(response=response)
    return render_template('chat.html', user=user)


@app.route('/generate_summary/<int:user_id>', methods=['POST'])
def generate_summary(user_id):
    end_conversation_and_generate_diary(user_id)
    return jsonify({'status': 'success'})





@app.route("/summaries/<int:user_id>", methods=['GET'])
def view_summaries(user_id):
    user = db.session.get(User, user_id)
    
    if not user:
        return redirect(url_for("login"))  # Redirect to the login page if the user is not logged in

    # Fetch past summaries and key points from the database
    logs = Log.query.filter_by(user_id=user_id).all()
    user_id = user_id

    for log in logs:
        log.key_points = {
            "Habits": [habit.habit for habit in log.habits],
            "Activities": [activity.activity for activity in log.activities],
            "Goals": [goal.goal for goal in log.Goal],
            "Mood": [mood.mood for mood in log.moods],
            "Thoughts": [thought.thought for thought in log.thoughts]
        }

    # Render an HTML template to display the summaries and key points
    return render_template("summaries.html", logs=logs, user_id = user_id)



def get_current_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')





#the function that is called to generate responses for the user
def generate_chatbot_response(user_id, message):
    response = ""
    timestamp = get_current_timestamp()
    end_conversation = False

    #check if any conversation history exists between the bot and the user. If not, it creates a new Conversation object.
    #Otherwise, it updates the existing Conversation object with the message received from the user.
    conversation = Conversation.query.filter_by(user_id=user_id).first()
    if not conversation:
        conversation = Conversation(user_id=user_id, content=f"{timestamp} {user_id}: {message}\n", user_input_counter=1)
        db.session.add(conversation)
    else:
        if not conversation.content:
            conversation.content = f"{timestamp} {user_id}: {message}\n"
        else:
            conversation.content += f"{timestamp} {user_id}: {message}\n"
        
        # Increment user_input_counter each time a user sends a message
        conversation.user_input_counter += 1
        
        # generate a random question for the user based on previous conversations
        time_since_last_question = timestamp - conversation.last_question_timestamp if conversation.last_question_timestamp else timedelta(minutes=2)
        if random.random() < 0.3 and time_since_last_question > timedelta(minutes=2):
            random_question = get_random_keypoint_question(user_id)
            if random_question:
                # Generate a question using the OpenAI API based on the random key point
                response = openai.Completion.create(
                    engine="text-davinci-002", 
                    prompt=f"rephrase the following question for the user: {random_question}. In you question you should mention the date and the day of the week when that specific key point was recorded using the timestamp. Do not mention the timestamp itself",
                    temperature=0.6, 
                    max_tokens=60, 
                    n=1, 
                    stop=None
                ).choices[0].text.strip()
            
            # Update conversation with response
            conversation.content += f'{timestamp} BrainY: {response}\n'
            conversation.last_question_timestamp = timestamp  # Update timestamp of last question
            db.session.commit()
            return response

    db.session.commit()

    

    # Get entire conversation history
    conversation_lines = conversation.content.strip().split('\n')

    # Construct the chat history for both the user and the bot
    chat_history = ''
    for line in conversation_lines[-15:]:  # Limiting the conversation history to last 15 lines
        # Identify who is speaking in the chat, BrainY or the user, and format the line accordingly
        speaker, spoken = line.split(": ", 1)
        if speaker == str(user_id):
            chat_history += f'User: {spoken}\n'
        else:
            chat_history += f'BrainY: {spoken}\n'
    
    # Generate response 
    response = openai.Completion.create(
        engine="text-davinci-002", 
        prompt=chat_history + "User: " + message + "\nBrainY:",
        temperature=0.7, 
        max_tokens=100, 
        n=1, 
        stop=["User: ", "BrainY:"]
    ).choices[0].text.strip()
    
    # Update conversation with response          
    conversation.content += f'{timestamp} BrainY: {response}\n'
    db.session.commit()  
     
        
    return response







#function that generates a random question for the user based on previous interaction
def get_random_keypoint_question(user_id):
    # Get all logs of the user
    logs = Log.query.filter_by(user_id=user_id).all()

    if not logs:
        return None

    # Collect all key points from all logs of the user
    key_points = []
    for log in logs:
        if hasattr(log, 'activities'):
            key_points.extend([(activity, log.timestamp) for activity in log.activities if activity.activity])
        if hasattr(log, 'habits'):
            key_points.extend([(habit, log.timestamp) for habit in log.habits if habit.habit])
        if hasattr(log, 'goals'):
            key_points.extend([(goal, log.timestamp) for goal in log.goals if goal.goal])
        if hasattr(log, 'moods'):
            key_points.extend([(mood, log.timestamp) for mood in log.moods if mood.mood])
        if hasattr(log, 'thoughts'):
            key_points.extend([(thought, log.timestamp) for thought in log.thoughts if thought.thought])

    if not key_points:
        return None

    # Select a random key point
    key_point, timestamp = random.choice(key_points)

    # Calculate day of the week from timestamp
    day_of_week = timestamp.strftime("%A")  
    date_string = timestamp.strftime("%d/%m/%Y")  

    # Generate a question based on the type of key point
    if isinstance(key_point, Activity):
        return f"On {day_of_week} {date_string}, you engaged in the activity '{key_point.activity}'. How did it impact your day?"
    elif isinstance(key_point, Habit):
        return f"On {day_of_week} {date_string}, you mentioned the habit '{key_point.habit}'. How is it affecting your daily routine?"
    elif isinstance(key_point, Goal):
        return f"On {day_of_week} {date_string}, you set the goal '{key_point.goal}'. How is your progress with it?"
    elif isinstance(key_point, Mood):
        return f"On {day_of_week} {date_string}, you were feeling '{key_point.mood}'. How did this mood influence your day?"
    elif isinstance(key_point, Thought):
        return f"On {day_of_week} {date_string}, you had the thought '{key_point.thought}'. Could you elaborate more on this?"




#function for when the user press generate diary
def end_conversation_and_generate_diary(user_id):
    conversation = Conversation.query.filter_by(user_id=user_id).first()
    if not conversation:
        return

    diary_entry = conversation.content
    summary, key_points = generate_diary_summary(diary_entry)
    save_diary_summary_and_key_points(user_id, summary, key_points)

    # Store the summary and key points in the session
    session['summary'] = summary
    session['key_points'] = key_points

    conversation.content = ""
    db.session.commit()

    return redirect(url_for('diary', user_id=user_id))



#function to call the API to generate the summary based on the conversation
def generate_diary_summary(conversation_content):
    summary = ""

    

    summary_prompt = (f"You are an AI that will analyze a conversation between a user and a chatbot. After analyzing the conversation, you will write a text that resembles a user's diary entry, written in first person, summarizing their day, including any specific events, feelings, or activities they mentioned, and their reactions to them. Then, create a list with habits, activities, goals, mood, and thoughts, based on the information extracted from the conversation. Each category in the list should include as many relevant details as possible from the conversation, each represented by a phrase of up to 3 words. If a category has no corresponding information, generate an empty list for that category. It is very important to correctly reflect the user's inputs and not make assumptions. Prioritize including as much relevant information as possible in the summary and key points, even if it means making the response longer. Use the following format:"
                 f"\n\nSummary of my day: 'text'"
                 f"\nKey points: ' \"Habits\": [],"
                 f"\"Activities\": [],"
                 f"\"Goals\": [],"
                 f"\"Mood\": [],"
                 f"\"Thoughts\": []'\n\n"
                 f"Here is a small example to guide you:"
                 f"\n\nConversation:"
                 f"\nUser: I had a great day today. I went for a walk and spent time with my family."
                 f"\nAI: Summary of my day: Today was fantastic. I enjoyed a refreshing walk and spent quality time with my loved ones."
                 f"\nKey points: \"Habits\": [],"
                 f"\"Activities\": [Walk, family time],"
                 f"\"Goals\": [],"
                 f"\"Mood\": [Great],"
                 f"\"Thoughts\": []'\n\n"
                 f"Please analyze the following conversation between a user and a chatbot and generate a response accordingly:"
                 f"\n\n{conversation_content}\n\n")


  
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=summary_prompt,
        max_tokens=300,
        n=1,
        stop=None,
        temperature=0.5,
    )

    generated_response = response.choices[0].text.strip()


    print("Generated response:", generated_response)
    


    # Extract summary and key points from the generated response
    summary, key_points = extract_summary(generated_response), extract_key_points(generated_response)
    print("Generated summary:", summary)

    print("Generated key points:", key_points)

    return summary, key_points


#extract the summary part from the API response
def extract_summary(generated_response):
    pattern = r"Summary(?: of my day)?:\s*(.*?)(\n|$)"
    match = re.search(pattern, generated_response)

    if match:
        summary = match.group(1)
    else:
        summary = "Summary generation failed due to invalid input."

    return summary



#extract the key points from the API response
def extract_key_points(generated_response):
    pattern = r"Key points:\s*\"Habits\":\s*(\[.*?\]|\{.*?\}|.*?),\s*\"Activities\":\s*(\[.*?\]|\{.*?\}|.*?),\s*\"Goals\":\s*(\[.*?\]|\{.*?\}|.*?),\s*\"Mood\":\s*(\[.*?\]|\{.*?\}|.*?),\s*\"Thoughts\":\s*(\[.*?\]|\{.*?\}|.*?)\s*$"
    match = re.search(pattern, generated_response, re.MULTILINE | re.DOTALL)

    if match:
        habits, activities, goals, mood, thoughts = match.groups()

        key_points = {
            "Habits": re.findall(r'\[(.*?)\]', habits)[0].split(', ') if habits.startswith('[') else [],
            "Activities": re.findall(r'\[(.*?)\]', activities)[0].split(', ') if activities.startswith('[') else [],
            "Goals": re.findall(r'\[(.*?)\]', goals)[0].split(', ') if goals.startswith('[') else [],
            "Mood": re.findall(r'\[(.*?)\]', mood)[0].split(', ') if mood.startswith('[') else [],
            "Thoughts": re.findall(r'\[(.*?)\]', thoughts)[0].split(', ') if thoughts.startswith('[') else [],
        }
    else:
        key_points = {
            "Habits": [],
            "Activities": [],
            "Goals": [],
            "Mood": [],
            "Thoughts": []
        }

    return key_points



# Save the summary and key points to the database
def save_diary_summary_and_key_points(user_id, summary, key_points):
    
    user = db.session.get(User, user_id)


    conversation = Conversation.query.filter_by(user_id=user_id).first()
    if not conversation:
        return

    # Create a new log entry with the summary
    log = Log(conversation_id=conversation.id, summary=summary, user_id=user_id)


    db.session.add(log)
    db.session.commit()

    for category, items in key_points.items():
        for item in items:
            if category == "Habits":
                habit = Habit(log_id=log.id, habit=item)
                db.session.add(habit)
            elif category == "Activities":
                activity = Activity(log_id=log.id, activity=item)
                db.session.add(activity)
            elif category == "Goals":
                goal = Goal(log_id=log.id, goal=item)
                db.session.add(goal)
            elif category == "Mood":
                mood = Mood(log_id=log.id, mood=item)
                db.session.add(mood)
            elif category == "Thoughts":
                thought = Thought(log_id=log.id, thought=item)
                db.session.add(thought)

    db.session.commit()


#modify the summary for the dedicated page
def create_diary_html(summary, key_points):
    diary_html = f"""
    <h2>Summary</h2>
    <p>{summary}</p>
    <h2>Key Points</h2>
    <ul>
    """
    for category, items in key_points.items():
        diary_html += f"<li><strong>{category}</strong>: {', '.join([str(item) for item in items])}</li>"
    diary_html += "</ul>"
    return diary_html



def save_diary_html(user_id, diary_html):
    if not os.path.exists(diary_path):
        os.makedirs(diary_path)

    diary_file = os.path.join(diary_path, f"{user_id}.html")

    with open(diary_file, "w") as f:
        f.write(diary_html)



@app.route('/diary/<int:user_id>', methods=['GET'])
def diary(user_id):
    summary = session.get('summary')
    key_points = session.get('key_points')

    if summary is None or key_points is None:
        user = db.session.get(User, user_id)

        conversation = Conversation.query.filter_by(user_id=user_id).first()
        if not conversation:
            return "No conversation found for this user"

        log = Log.query.filter_by(conversation_id=conversation.id).order_by(Log.timestamp.desc()).first()
        if not log:
            return "No diary summary found for this user"

        summary = log.summary

        key_points = {
            "Habits": [habit.habit for habit in log.habits],
            "Activities": [activity.activity for activity in log.activities],
            "Goals": [goal.goal for goal in log.goals],
            "Mood": [mood.mood for mood in log.moods],
            "Thoughts": [thought.thought for thought in log.thoughts],
        }

    return render_template('diary.html', summary=summary, key_points=key_points, user_id=user_id)


@app.route("/logout")
def logout():
    session.pop("user_id", None)  # Remove the user from the session
    return redirect(url_for("login"))  # Redirect to the login page




if __name__ == '__main__':
    app.run(debug=True)