import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, stream_with_context
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, User, Chat, Message
import config

# Import our AI engine logic
from scraper import scrape_webpage, extract_text
from embedder import split_text_into_chunks, get_gemini_embeddings_model
from retriever import create_and_save_vector_store, search_vector_store, load_vector_store
from chatbot import get_gemini_llm, generate_answer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Initialize Database and Login Manager
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize AI Models once globally
embeddings_model = get_gemini_embeddings_model()
llm = get_gemini_llm()

# --- AUTHENTICATION ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html', is_register=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index'))
    return render_template('login.html', is_register=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- MAIN APP ROUTE ---

@app.route('/')
@login_required
def index():
    # Load the main chat interface
    return render_template('index.html', username=current_user.username)

# --- API ROUTES ---

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    chat_list = [{"id": c.id, "url": c.url, "created_at": c.created_at.isoformat()} for c in chats]
    return jsonify({"chats": chat_list})

@app.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
@login_required
def get_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at.asc()).all()
    msg_list = [{"role": m.role, "content": m.content} for m in messages]
    return jsonify({"messages": msg_list})

@app.route('/api/chat/new', methods=['POST'])
@login_required
def new_chat():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
        
    # 1. Create a new chat record in DB
    new_chat = Chat(user_id=current_user.id, url=url)
    db.session.add(new_chat)
    db.session.commit()
    
    # 2. Process the website using our AI engine
    soup = scrape_webpage(url)
    if not soup:
        db.session.delete(new_chat)
        db.session.commit()
        return jsonify({"error": "Failed to fetch or parse the website."}), 400
        
    text = extract_text(soup)
    if not text:
        db.session.delete(new_chat)
        db.session.commit()
        return jsonify({"error": "Website is empty or blocked scraping."}), 400
        
    chunks = split_text_into_chunks(text)
    
    # 3. Create FAISS cache specifically for this chat_id
    create_and_save_vector_store(chunks, embeddings_model, new_chat.id)
    
    return jsonify({"success": True, "chat_id": new_chat.id})

@app.route('/api/chat/<int:chat_id>/message', methods=['POST'])
@login_required
def send_message(chat_id):
    data = request.json
    user_message = data.get('message')
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
        
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    # 1. Fetch Chat History (last 6 messages so the LLM remembers context)
    recent_messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at.asc()).limit(6).all()
    chat_history_str = ""
    for m in recent_messages:
        role_name = "User" if m.role == "user" else "AI"
        chat_history_str += f"{role_name}: {m.content}\n\n"
        
    # 2. Save new user's message to DB
    msg_user = Message(chat_id=chat.id, role='user', content=user_message)
    db.session.add(msg_user)
    db.session.commit()
    
    # 3. Retrieve context from FAISS
    vector_store = load_vector_store(embeddings_model, chat.id)
    if not vector_store:
        return jsonify({"error": "Database not found for this chat."}), 404
        
    context = search_vector_store(vector_store, user_message)
    
    # 4. Generate Stream
    def generate():
        full_answer = ""
        # stream_with_context ensures we can still access the db inside this generator
        for chunk in generate_answer(user_message, context, chat_history_str, llm):
            full_answer += chunk
            # Yield Server-Sent Events (SSE) format
            # We replace newlines because SSE uses \n\n to delimit messages
            safe_chunk = chunk.replace('\n', '<br>')
            yield f"data: {safe_chunk}\n\n"
            
        # 5. After stream is finished, save the bot's full answer to DB
        msg_bot = Message(chat_id=chat.id, role='bot', content=full_answer)
        db.session.add(msg_bot)
        db.session.commit()
        
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Create sqlite database if it doesn't exist
    print("Starting Website RAG Web Server...")
    app.run(debug=True, port=5000)
