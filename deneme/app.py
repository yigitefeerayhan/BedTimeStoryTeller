from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import google.generativeai as genai
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()
API = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # flash mesajları için gerekli

# Veritabanı bağlantısı
def get_db_connection():
    conn = sqlite3.connect('stories.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ana sayfa
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Yeni bir hikaye oluşturmak için form
@app.route('/create_story', methods=['GET'])
def create_story_form():
    return render_template('create_story.html')

# Yeni bir hikaye oluşturmak için POST isteği
@app.route('/create_story', methods=['POST'])
def create_story():
    character_name = request.form['character_name']
    location = request.form['location']
    topic = request.form['topic']
    educational_content = request.form['educational_content']
    narrative_style = request.form['narrative_style']
    story_title = request.form['story_title']

    # Kullanıcıdan alınan girdileri kullanarak özel bir prompt oluşturma
    custom_prompt = f"Bir gün {character_name}, {location}'da bir maceraya atılır. {topic} üzerine bir hikaye anlatırken, {educational_content} hakkında bilgi verir. {narrative_style} anlatım şekliyle hikaye tamamlanır."

    # Google Generative AI kullanarak hikaye oluşturma
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(custom_prompt)
    print(response.text)

    story_content = response.text

    # Yapay zeka tarafından oluşturulan hikaye
    new_story = {
        "title": story_title,
        "content": story_content
    }

    # Hikayeyi veritabanına kaydet
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stories (title, content) VALUES (?, ?)
    ''', (new_story['title'], new_story['content']))
    conn.commit()
    conn.close()

    flash('Hikaye başarıyla oluşturuldu!', 'success')
    return redirect(url_for('get_stories'))

# Tüm hikayeleri getiren endpoint
@app.route('/stories', methods=['GET'])
def get_stories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories')
    stories = cursor.fetchall()
    conn.close()
    return render_template('stories.html', stories=stories)

# Hikaye silme işlemi öncesi onaylama ekranı
@app.route('/confirm_delete/<int:story_id>', methods=['GET'])
def confirm_delete(story_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM stories WHERE id = ?', (story_id,))
    story = cursor.fetchone()
    conn.close()
    return render_template('confirm_delete.html', story=story)

# Hikaye silme işlemi
@app.route('/delete_story/<int:story_id>', methods=['DELETE'])
def delete_story(story_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM stories WHERE id = ?', (story_id,))
    conn.commit()
    conn.close()
    return jsonify({'result': 'success'})

if __name__ == '__main__':
    app.run(port=8080, debug=True)
