from tkinter.tix import Form

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import re

# connect for database postgresql

app = Flask(__name__)
CORS(app, resources={r"/e-mail-api": {"origins": "*"}, r"/users": {"origins": "*"}, r"/user/*": {"origins": "*"}, r"/submit_form/*": {"origins": "*"},}, methods=["OPTIONS", "POST", "GET", "DELETE"])
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://myuser:mypassword@localhost:5432/mydatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# create database email and contact

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(500), nullable=False)


# class UserRegistration(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(120), nullable=False)
#     password = db.Column(db.String(120), nullable=False)


# Валидация данных с front
def is_valid_email(email):
    email_regex = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    return bool(re.match(email_regex, email)) and "@" in email and "." in email


def is_valid_number(number):
    number_regex = re.compile(r"^\d+$")
    return bool(re.match(number_regex, str(number))) and "0" in str(number)


def is_valid_name(name):
    return isinstance(name, str)


def is_valid_message(message):
    return isinstance(message, str) and len(message) >= 20


@app.route('/e-mail-api', methods=['POST'])
def receive_email():
    try:
        data = request.get_json()
        email_address = data.get('email', '')

        if not email_address:
            return jsonify({'success': False, 'message': 'Email address is required'}), 400

        if not is_valid_email(email_address):
            return jsonify({'success': False, 'message': 'Invalid email address'}), 400

        existing_email = Email.query.filter_by(email=email_address).first()
        if existing_email:
            return jsonify({'success': False, 'message': f'{email_address}, такой адрес уже используется!'}), 400

        new_email = Email(email=email_address)
        db.session.add(new_email)
        db.session.commit()

        print(f'user_email: {email_address}')

        return jsonify({'success': True, 'message': 'Email received and saved successfully'})
    except IntegrityError as e:
        db.session.rollback()
        print(f'Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    except Exception as e:
        db.session.rollback()
        print(f'Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Error processing email'}), 500


@app.route('/users', methods=['GET'])
def get_users():
    try:
        users = Email.query.all()
        user_data = [{'id': user.id, 'email': user.email} for user in users]
        return jsonify(user_data)
    except Exception as e:
        print(f'Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Error getting user data'}), 500


@app.route('/user/<int:user_id>', methods=['OPTIONS', 'DELETE'])
def delete_user(user_id):
    try:
        if request.method == 'OPTIONS':
            return jsonify({'success': True, 'message': 'Options request successful'})

        user = Email.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'success': True, 'message': f'User with id {user_id} deleted successfully'})
        else:
            return jsonify({'success': False, 'message': f'User with id {user_id} not found'}), 404
    except Exception as e:
        db.session.rollback()
        print(f'Error: {str(e)}')
        return jsonify({'success': False, 'message': 'Error deleting user'}), 500


@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        data = request.get_json()
        print(f"Received data: {data}")

        name = data.get('name', '')
        email = data.get('email', '')
        phone = data.get('phone', '')
        message = data.get('message', '')

        # Проверка обязательных полей
        if not name or not email or not phone or not message:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400

        # Проверка данных которые к нам приходят
        if not is_valid_name(name):
            return jsonify({'success': False, 'message': 'Invalid name'}), 400

        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Invalid email address'}), 400

        if not is_valid_number(phone):
            return jsonify({'success': False, 'message': 'Invalid phone number'}), 400

        if not is_valid_message(message):
            return jsonify({'success': False, 'message': 'Invalid message (should be at least 20 characters)'}), 400

        # Создание нового контакта
        new_contact = Contact(name=name, email=email, phone=phone, message=message)
        db.session.add(new_contact)
        db.session.commit()

        print(f'Contact saved: {new_contact}')

        return jsonify({'status': 'success'})
    except Exception as e:
        print(f'Error: {str(e)}')
        return jsonify({'status': 'error', 'message': 'Error processing form data'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=False)