from flask import Flask, Response, send_from_directory, request, redirect, url_for, render_template, flash
from werkzeug import secure_filename
import pygal, yaml, os, datetime, calendar, omdb, random
from pygal.style import DarkSolarizedStyle

UPLOAD_FOLDER = './static/'
ALLOWED_EXTENSIONS = set(['json','yaml'])
global m_list

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def splash_page():
    '''Main login page'''
    
    return render_template('splash.html')
    
@app.route('/add')
def add():
    return render_template('add.html')
    
@app.route('/upload')
def upload():
    return render_template('upload.html')
    
@app.route('/uploader',methods = ['POST','GET'])
def uploader():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('user_stats', filename=filename))

@app.route('/user_stats/<filename>')
def user_stats(filename):
    global m_list
    with open(filename) as file:
        m_list = yaml.load(file)
    
    recent_posters = []
    for i in range(len(m_list) - 7, len(m_list)+1):
        t = omdb.title(m_list[str(i)]['Title'])
        if 'poster' in t.keys():
            recent_posters.append(t['poster'])
        else:
            pass
    
    random.shuffle(recent_posters)
        
    money_spent, money_saved = 0, 0
    for v in m_list.values():
        if v['Theater?'] == "y":
            day = datetime.date(v['Year'],v['Month'],v['Day'])
            if day.weekday() == 'Tuesday':
                money_spent += 8.10
            else:
                money_spent += 15.25
                money_saved += 7.15
    
    global genres
    genres = {}
    for v in m_list.values():
        m = omdb.title(v['Title'])
        if 'genre' in m.keys():
            m_genres = m['genre'].split(',')
            for g in m_genres:
                if g not in genres:
                    genres[g] = 1
                else:
                    genres[g] += 1
    
    return render_template('user_stats.html', posters=recent_posters, spent=money_spent, saved=money_saved,
                           fav_genre=max(genres, key=genres.get), worst_genre=min(genres, key=genres.get))
        
@app.route('/global_stats')
def global_stats():
    '''Global Stats Page'''
    
    return render_template('global_stats.html')
    
@app.route('/global_theater_graph/')
def global_theater_graph():
    pie_chart = pygal.Pie(width=400, height=300, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    pie_chart.title = '% of movies seen at home'
    pie_chart.add('At home', 39.7)
    pie_chart.add('At the theaters', 60.3)
    return Response(response=pie_chart.render(), content_type='image/svg+xml')
    
@app.route('/user_theater_graph/')
def user_theater_graph():
    in_theater = 0
    for v in m_list.values():
        if v['Theater?'] == 'y':
            in_theater += 1
    
    pie_chart = pygal.Pie(width=500, height=300, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    pie_chart.title = 'Percentage of movies seen at home'
    pie_chart.add('At home', len(m_list) - in_theater)
    pie_chart.add('At the theaters', in_theater)
    return Response(response=pie_chart.render(), content_type='image/svg+xml')

@app.route('/user_weekday_graph/')
def user_weekday_graph():
    days = {'Monday':0,'Tuesday':0,'Wednesday':0,'Thursday':0,'Friday':0,'Saturday':0,'Sunday':0}
    for v in m_list.values():
        day = datetime.date(v['Year'],v['Month'],v['Day'])
        days[calendar.day_name[day.weekday()]] += 1
    
    l = pygal.Bar(width=500, height=300, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    l.title = 'Movies seen per day of week'
    l.x_labels = days.keys()
    l.add('Weekdays', days.values())
    return Response(response=l.render(), content_type='image/svg+xml')

@app.route('/user_genre_graph/')
def user_genre_graph():    
    p = pygal.Pie(width=500, height=300, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    p.title = 'Movies seen split by genre'
    for k,v in genres.items():
        p.add(k,v)
    return Response(response=p.render(), content_type='image/svg+xml')
    
if __name__ == '__main__':
    app.run(debug=True)