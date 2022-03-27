import requests as requests
from flask import Flask, render_template, url_for, redirect, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, delete, insert, update
from flask_login import UserMixin
from flask_login import LoginManager
from flask_login import login_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_socketio import SocketIO, send, emit, join_room, leave_room


path = 'https://translator1.loca.lt/'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisIsASecretKey'
db = SQLAlchemy(app)

socketio = SocketIO(app, cors_allowed_origins="*")

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(30), nullable=False, unique=True)
    username = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    lang = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.id


class Chat(db.Model):
    __tablename__ = 'chat'
    id = db.Column(db.Integer, primary_key=True)
    chatname = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return '<Chat %r>' % self.id


class ChatToUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_chat = db.Column(db.Integer, ForeignKey('chat.id'))
    id_user = db.Column(db.Integer, ForeignKey('user.id'))

    def __repr__(self):
        return '<ChatToUser %r>' % self.id


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_sender = db.Column(db.Integer, ForeignKey('user.id'))
    id_chat = db.Column(db.Integer, ForeignKey('chat.id'))
    message_en = db.Column(db.Text, nullable=False)
    message_ru = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return '<Messages %r>' % self.id


# 1
@socketio.on('message')
def handleMessage(data):
    if data['room']:
        join_room(data['room'])
        chat_id = data['room'].split('/chat/')
        print("Chat Id: ", chat_id)
        if len(chat_id) >= 2 and data['username'] != 'Service message':
            chat_id = int(chat_id[-1])
            # Send to db

            msg = data['msg']
            msgs = [0] * 2
            if current_user.lang == 1:
                msgs[1] = msg

                temp = msg.replace('?', '&quest')
                req = requests.get(f'{path}translate/{temp}?src_lang=ru&trg_lang=en')
                translation = req.json()['translation']
                # msgs[i].append(translation[0])

                msgs[0] = translation[0]
            else:
                msgs[0] = msg

                temp = msg.replace('?', '&quest')
                req = requests.get(f'{path}translate/{temp}?src_lang=en&trg_lang=ru')
                translation = req.json()['translation']
                # msgs[i].append(translation[0])

                print(f'{path}translate/{temp}?src_lang=en&trg_lang=ru')

                msgs[1] = translation[0]
            now = datetime.utcnow()
            new_msg = Messages(id_sender=int(current_user.id), id_chat=chat_id, message_en=msgs[0], message_ru=msgs[1],
                               date=now)

            print('New message:', int(current_user.id), chat_id, msgs[0], msgs[1], now)

            # add the new user to the database
            db.session.add(new_msg)
            db.session.commit()

            msgs = [current_user.id, current_user.username,
                       {'EN': msgs[0], 'RU': msgs[1]}, now.strftime("%b %d, %Y, %X"),
                       'RU' if current_user.lang == 1 else 'EN']
            if current_user.lang == 1:
                temp = msgs[2]['RU'].replace('?', '&quest')
                temp = temp.replace(' ', '%20')

                msgs.append(f'{path}synthesize/{temp}?src_lang=ru')
            else:
                temp = msgs[2]['EN'].replace('?', '&quest')
                temp = temp.replace(' ', '%20')

                msgs.append(f'{path}synthesize/{temp}?src_lang=en')


            data['msgs'] = msgs
            print(f"Message: {data} CurrentUser: {current_user.id}, {current_user.username}")
            send(data, room=data['room'])
        else:
            if data['username'] != 'Service message':
                print(f"Message: {data} CurrentUser: {current_user.id}, {current_user.username}")
                send(data, room=data['room'])
    else:
        print(f"Broadcasted Message: {data} CurrentUser: {current_user.id}, {current_user.username}")
        send(data, broadcast=True)

    # message = ChatMessages(username=data['username'], msg=data['msg'])
    # db.session.add(message)
    # db.session.commit()


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def singin():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = True if request.form.get('remember_me') else False

        user = User.query.filter_by(email=email).first()

        # check if the user actually exists
        # take the user-supplied password, hash it, and compare it to the hashed password in the database
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))  # if the user doesn't exist or password is wrong, reload the page
        login_user(user, remember=remember_me)
        return redirect(url_for('index'))
    return render_template("login.html")


@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/register', methods=['POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        lang = request.form.get('language')

        if lang == 'russian':
            lang = 1
        else:
            lang = 0
        print(request.form, lang)

        user = User.query.filter_by(
            email=email).first()  # if this returns a user, then the email already exists in database

        if user:  # if a user is found, we want to redirect back to signup page so user can try again
            flash("User with such email already exist.")
            return redirect(url_for('signup'))

        # create a new user with the form data. Hash the password so the plaintext version isn't saved.
        new_user = User(email=email, username=username, password=generate_password_hash(password, method='sha256'),
                        lang=lang)

        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template("register.html")


@login_required
@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def index():
    # print(session)
    if current_user.is_authenticated:
        chats = ChatToUser.query.filter_by(id_user=current_user.id).all()
        for i in range(len(chats)):
            chats[i] = Chat.query.filter_by(id=chats[i].id_chat).first()

        if request.method == 'GET' and len(request.args.to_dict())>0:
            print(request.args.to_dict())
            if 'EnglishButton' in request.args.to_dict():
                print('EN')
                user = User.query.filter_by(id=current_user.id).first()
                user.lang = 0
                db.session.commit()
            else:
                user = User.query.filter_by(id=current_user.id).first()
                user.lang = 1
                db.session.commit()
                print('RU')
            return redirect(url_for('index'))


        return render_template("index.html",
                               name=current_user.username + ' ' + ('EN' if current_user.lang == 0 else 'RU'), chats=chats)
        # return render_template("index.html", name=current_user.username)
    else:
        return render_template("index.html", name="Stranger")


@login_required
@app.route('/about')
def about():
    return render_template("about.html")
    # return name + " " + str(id)


@login_required
@app.route('/chat/<id>', methods=['GET'])
def chat(id):
    if request.method == 'GET' and len(request.args.to_dict()) > 0:
        print(request.args.to_dict())
        if 'EnglishButton' in request.args.to_dict():
            print('EN')
            user = User.query.filter_by(id=current_user.id).first()
            user.lang = 0
            db.session.commit()
        else:
            user = User.query.filter_by(id=current_user.id).first()
            user.lang = 1
            db.session.commit()
            print('RU')
        return redirect(url_for('chat', id=id))



    print(id)
    if current_user.is_authenticated:
        if ChatToUser.query.filter_by(id_user=current_user.id, id_chat=int(id)).first():
            print('Ok')
        else:
            # TODO: Say that you are not member of this chat
            print('Denied')
            return redirect(url_for('index'))

        # TODO: Check if you have access to this chat
        # TODO: Check if this chat exist

        chatName = 'SimpleChat'

        chats = ChatToUser.query.filter_by(id_user=current_user.id).all()
        for i in range(len(chats)):
            chats[i] = Chat.query.filter_by(id=chats[i].id_chat).first()
            if (int(id) == int(chats[i].id)):
                chatName = chats[i].chatname

        msgs = Messages.query.filter_by(id_chat=int(id)).all()
        for i in range(len(msgs)):
            msgs[i] = [msgs[i].id_sender, User.query.filter_by(id=msgs[i].id_sender).first().username,
                       {'EN': msgs[i].message_en, 'RU': msgs[i].message_ru}, msgs[i].date.strftime("%b %d, %Y, %X"),
                       'RU' if User.query.filter_by(id=msgs[i].id_sender).first().lang == 1 else 'EN']
            ##if (current_user.lang == 1 and msgs[i][4] == 'RU') or (current_user.lang == 0 and msgs[i][4] == 'EN'):
            ##msgs[i].append(msgs[i][2])
            ##else:
            # temp = msgs[i][2].replace('?', '&quest')
            # req = requests.get(f'{path}translate/{temp}?src_lang={"ru" if msgs[i][4]=="RU" else "en"}&trg_lang={"ru" if current_user.lang==1 else "en"}')
            # translation = req.json()['translation']
            # msgs[i].append(translation[0])

            ################msgs[i].append('Translated')

            # temp = msgs[i][2].replace('?', '&quest')
            # msgs[i].append(f'{path}translate/{temp}?src_lang={"ru" if msgs[i][4]=="RU" else "en"}&trg_lang={"ru" if current_user.lang==1 else "en"}')
            if current_user.lang == 1:
                temp = msgs[i][2]['RU'].replace('?', '&quest')
                temp = temp.replace(' ', '%20')

                # ru

                # msgs[i].append('{path}dummy_audio')
                msgs[i].append(f'{path}synthesize/{temp}?src_lang=ru')
            else:
                temp = msgs[i][2]['EN'].replace('?', '&quest')
                temp = temp.replace(' ', '%20')

                # en

                # msgs[i].append('{path}dummy_audio')
                msgs[i].append(f'{path}synthesize/{temp}?src_lang=en')

            # print(msgs[i])

        return render_template("chatPage.html", name=current_user.username + ' ' + ('EN' if current_user.lang == 0 else 'RU'),
                               chats=chats, chatId=id, chatName = chatName,msgs=msgs, my_link="{path}dummy_audio")
    else:
        return redirect(url_for("index"))


@login_required
@app.route('/chat/<id>', methods=['POST'])
def account(id):
    if request.method == 'POST':
        if current_user.is_authenticated:
            if ChatToUser.query.filter_by(id_user=current_user.id, id_chat=int(id)).first():
                print('Ok')
            else:
                # TODO: Say that you are not member of this chat
                print('Denied')
                return redirect(url_for('index'))
            # TODO: Check if you have access to this chat
            # TODO: Check if this chat exist

            msg = request.form.get('msg')
            msgs = [0] * 2
            if current_user.lang == 1:
                msgs[1] = msg

                temp = msg.replace('?', '&quest')
                req = requests.get(f'{path}translate/{temp}?src_lang=ru&trg_lang=en')
                translation = req.json()['translation']
                # msgs[i].append(translation[0])

                msgs[0] = translation[0]
            else:
                msgs[0] = msg

                temp = msg.replace('?', '&quest')
                req = requests.get(f'{path}translate/{temp}?src_lang=en&trg_lang=ru')
                translation = req.json()['translation']
                # msgs[i].append(translation[0])

                print(f'{path}translate/{temp}?src_lang=en&trg_lang=ru')

                msgs[1] = translation[0]  # TODO: Поменять на запрос
            now = datetime.utcnow()
            new_msg = Messages(id_sender=int(current_user.id), id_chat=int(id), message_en=msgs[0], message_ru=msgs[1],
                               date=now)

            print('New message:', int(current_user.id), int(id), msgs[0], msgs[1], now)

            # add the new user to the database
            db.session.add(new_msg)
            db.session.commit()

            return redirect(url_for('chat', id=id))
        else:
            return render_template("index.html", name="Stranger")


# @app.route('/test')
# def chatPage():
#    return render_template('chatPage.html')


@app.route('/addToChat/<chatId>')
def showFriends(chatId):
    ans = [current_user.id]
    if chatId!='new':
        ans = [i.id_user for i in ChatToUser.query.filter_by(id_chat=int(chatId)).order_by(ChatToUser.id).all()]
        print(ans)
        # TODO: ADMIN! [0]


    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('friends.html', name=current_user.username, friends=User.query.order_by(User.id).all(),
                           inThisChat=ans,
                           user=current_user)


@login_required
@app.route('/addToChat/<chatId>', methods=['POST', 'GET'])
def addToChat(chatId):
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    if chatId != 'new':
        if Chat.query.filter_by(id=int(chatId)).first():
            if ChatToUser.query.filter_by(id_chat=int(chatId), id_user=current_user.id).first():
                # ok
                print('You can go.')
            else:
                # TODO: Show that he don't have access
                print("Denied")
                return redirect(url_for("index"))
        else:
            # TODO: Show that there are no chat like that
            print("Not yet")
            return redirect(url_for("index"))
    # Проверяем есть ли чат с таким id (Если нет кикай отсюда)
    # Если есть: Проверяем может ли такой пользователь добавить (есть ли он в чате)
    #if request.method == :
    #    print(request.args.to_dict())
    #    if 'EnglishButton' in request.args.to_dict():
    #        print('EN')
    #    else:
    #        print('RU')
    #    return redirect(url_for('index'))


    if request.method == 'POST':
        print(request.form.to_dict())
        friends = request.form.to_dict()

        if 'LeaveButton' in friends:
            temp = ChatToUser.query.filter_by(id_chat=chatId, id_user=current_user.id)
            print(temp, 1 if temp else 0)
            if temp:
                temp.delete()
                db.session.commit()
            return redirect(url_for("index"))

        if friends['name'] != '' and chatId!='new':
            temp = Chat.query.filter_by(id=chatId).first()
            temp.chatname = friends['name']
            db.session.commit()

        if friends['name'] == '':
            s = current_user.username
            for i in friends:
                if i != 'name' and int(i) != current_user.id:
                    s += User.query.filter_by(id=int(i)).first().username
            friends['name'] = s

        print("Name of chat is: " + friends['name'])

        if chatId == 'new':
            new_chat = Chat(chatname=friends['name'])
            db.session.add(new_chat)
            db.session.commit()
            chatId = new_chat.id


        print(chatId)


        previous_friends = [i.id_user for i in ChatToUser.query.filter_by(id_chat=int(chatId)).order_by(ChatToUser.id).all()]

        for i in previous_friends:
            if (int(i)!=current_user.id):
                if str(i) not in friends:
                    print(i, " was deleted") # TODO: BOT socket + db пишет что удалили
                    ChatToUser.query.filter_by(id_chat=int(chatId), id_user=int(i)).delete();
                    db.session.commit();

        for i in friends:
            if (i != 'name'):
                if ChatToUser.query.filter_by(id_chat=chatId, id_user=int(i)).first():
                    print(i + " Already in this chat")
                else:
                    print(i + " Added") # TODO: BOT socket + db пишет что добавили
                    c_t_u = ChatToUser(id_chat=chatId, id_user=int(i))
                    db.session.add(c_t_u)
                    db.session.commit()
            else:
                if ChatToUser.query.filter_by(id_chat=chatId, id_user=current_user.id).first():
                    print(str(current_user.id) + " Already in this chat")
                else:
                    print(str(current_user.id) + " Added") # TODO: BOT socket + db пишет что добавили
                    c_t_u = ChatToUser(id_chat=chatId, id_user=current_user.id)
                    db.session.add(c_t_u)
                    db.session.commit()
        return redirect('/chat/' + str(chatId))
    return render_template('friends.html', friends=User.query.order_by(User.id).all(), user=current_user)


if __name__ == '__main__':
    socketio.run(app, debug=True)
    # app.run(debug=True)
