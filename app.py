from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from groq import Groq
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')

# Iniciar la base de datos
db = SQLAlchemy(app)
# Iniciar el cliente de Groq
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

df = pd.read_excel('Data.xlsx')
data = df.to_string(index=False)


class InteraccionChatbot(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	pregunta = db.Column(db.Text, nullable=False) 
	respuesta = db.Column(db.Text, nullable=False)
	fecha = db.Column(db.DateTime, default=datetime.utcnow)

class MensajeContacto(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nombre = db.Column(db.String(100), nullable=False) 
	correo = db.Column(db.String(120), nullable=False) 
	mensaje = db.Column(db.Text, nullable=False)
	fecha = db.Column(db.DateTime, default=datetime.utcnow)


@app.before_request
def init_db():
	db.create_all()


def guardar_interaccion(pregunta, respuesta):
	nueva_interaccion = InteraccionChatbot(pregunta=pregunta, respuesta=respuesta)
	db.session.add(nueva_interaccion)
	db.session.commit()

def consultar_csv(pregunta, data):
    # 1. Definir el rol de asistente de la IA
    # 2. Especificar al asistente que solo debe limitarse a la data que le demos
    # 3. Detalles de la data 
    # 4. Restricciones del idioma y como debe respodner
    prompt = (
        'Eres un asistente experto en museos de Ecuador.'
        'Te proporcionaré detalles específicos del museo de la Casa de la Cultura, y tu tarea es responder únicamente las preguntas que te haré basándote solo en la información. No incluya información adicional que no esté presente en los datos proporcionados.'
        'La información incluye: nombre, dirección, teléfono, región, provincia, ciudad, tipo de museo, costo, horario de atención, descripción, detalles de 3 obras del museo'
        'Responde solo en español de una forma consica, precisa y amable. Aquí esta la información\n'
        f'{data}\n'
    )
    completion = client.chat.completions.create(
    model="llama3-70b-8192",
    messages=[
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": pregunta
        }
    ],
    temperature=1,
    max_tokens=1024,
    top_p=1,
    stream=True,
    stop=None,
	) 
        
    respuesta = ""
    for chunk in completion: 
        respuesta += chunk.choices[0].delta.content or ""
    return respuesta


@app.route('/about')
def about():
	return render_template('about.html')
@app.route('/contact')
def contact():
	return render_template('contact.html')

@app.route("/")
@app.route("/index")
def index():
	return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
	# Cuantas obras hay
	pregunta_usuario = request.form["message"]
	print(pregunta_usuario)
	respuesta = consultar_csv(pregunta_usuario, data)
	# Guardar la interacción del chatbot en la base de datos
	guardar_interaccion(pregunta_usuario, respuesta)
	return jsonify({"response": respuesta})


@app.route('/send_message')
def send_message():
	name = request.form['name']
	email = request.form['email']
	message = request.form['message']

	nuevo_mensaje = MensajeContacto(name, email, message)
	db.session.add(nuevo_mensaje)
	db.session.commit()
	return redirect(url_for('contact'))



if __name__ == '__main__':
	app.run(debug=True)