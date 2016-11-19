from flask import Flask, Response, request, redirect, url_for, render_template, flash
from werkzeug import secure_filename
import os, pygal, yaml, datetime, calendar, omdb, hashlib
from pygal.style import DarkSolarizedStyle
from collections import OrderedDict

UPLOAD_FOLDER = './static/'
ALLOWED_EXTENSIONS = set(['json','yml'])
m_list = {}
g_list = {}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def splash_page():
    '''Main page'''
    
    return render_template('splash_page.html')
    
@app.route('/add')
def add():
    '''Single viewing experience addition page'''
    return render_template('add.html')
    
@app.route('/adder',methods = ['POST','GET'])
def adder():
    ''' Form to add a single viewing experience to the global list '''
    if request.method == 'POST':
        #calls global variable g_list
        global g_list
        
        #assigns values to all the fields
        title = request.form['title']
        day = request.form['day']
        month = request.form['month']
        year = request.form['year']
        t_buff = request.form.getlist('Theater')
        if t_buff == 'yes':
            theater = 'y'
        else:
            theater = 'n'
        
        #check for valid calendar date
        if int(day) < 1 or int(day) > 31 or int(month) < 1 or int(month) > 12:
            flash('Invalid Date')
            return redirect(request.url)
        #check for movie title
        if title == '':
            flash('No Title')
            return redirect(request.url)
        #check for a valid calendar year
        if int(year) < datetime.MINYEAR or int(year) > datetime.MAXYEAR:
            flash('Invalid Year')
            return redirect(request.url)
        else:
            #creates unique hash for viewing experience from data fields
            #prevents duplicates when a user uploads an updated list
            m = hashlib.sha256(str.encode('{}{}{}{}{}'.format(title,day,month,year,theater)))
            
            #adds experience to global list at a key equal to the hash digest
            g_list[m.hexdigest()] = {'Title':str(title),'Day':int(day),'Month':int(month),'Year':int(year),'Theater?':theater}
            
            #dumps current global list to static file
            with open('./static/global_list.yml','w') as f:
                yaml.dump(g_list, f)
        
        #pushes user to the global stat page
        return redirect(url_for('global_stats'))
    
@app.route('/upload')
def upload():
    '''Page to upload a user's list'''
    return render_template('upload.html')
    
@app.route('/uploader',methods = ['POST','GET'])
def uploader():
    '''Handles POST request to grab uploaded files'''
    if request.method == 'POST':
        f = request.files['file']
        #secures the filename to prevent unsanitary data inputs
        filename = secure_filename(f.filename)
        
        #saves the file to the directory and redirects to the user stat page
        #for that data file
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('user_stats', filename=filename))

@app.route('/user_stats/<filename>')
def user_stats(filename):
    '''renders the user stats page'''
    #calls in the global variables for the user list
    #and the global list
    global m_list
    global g_list
    
    #loads both files into their respective dicts
    with open(filename) as file:
        m_list = yaml.load(file)
        
    with open('./static/global_list.yml','r') as exfile:
        g_list = yaml.load(exfile)
    
    #loop over each item in the user list
    for k,v in m_list.items():
        #generates unique hash for viewing experience based on the data fields
        h = hashlib.sha256(str.encode('{}{}{}{}{}'.format(v['Title'],v['Day'],v['Month'],v['Year'],v['Theater?'])))
        #checks if specific experience is in the global list
        if h.hexdigest() in g_list.keys():
            continue
        #if not in the global list, the experience is added to the pile
        else:
            g_list[h.hexdigest()] = v
            continue
    
    #dumps updated global list back to the static file
    with open('./static/global_list.yml','w') as exfile:
        yaml.dump(g_list, exfile)
    
    recent_posters = []
    #references IMDB using api to grab posters of 7 recently watched films
    for i in range(len(m_list) - 7, len(m_list)+1):
        t = omdb.title(m_list[str(i)]['Title'])
            
        if 'poster' in t.keys():
            recent_posters.append(t['poster'])
        else:
            pass
    
    #based on the price of tickets at Cineplex in Toronto
    #finds how much money has been spent since tracking started
    #and how much money could've been saved if it were Tuesday
    money_spent, money_saved = 0, 0
    for v in m_list.values():
        if v['Theater?'] == "y":
            #creates datetime object to refer to
            day = datetime.date(v['Year'],v['Month'],v['Day'])
            if day.weekday() == 1:
                money_spent += 8.10
                money_saved += 7.15
            else:
                money_spent += 15.25
    
    #instantiates global dict for how many times each genre is seen
    global genres
    genres = {}

    for v in m_list.values():
        #creates omdb object based on movie title
        movie = omdb.title(v['Title'])
        if 'genre' in movie.keys():
            #creates list of all genres movie can be considered to be
            movie_genres = movie['genre'].split(',')
            #increments each genre in the genre dict
            for genre in movie_genres:
                if genre not in genres:
                    genres[genre] = 1
                else:
                    genres[genre] += 1
    
    #renders the user stats page with graphs of the above analysis
    #giving them info about the movies they've seen
    return render_template('user_stats.html', posters=recent_posters, spent='{:.2f}'.format(money_spent), saved='{:.2f}'.format(money_saved),
                           fav_genre=max(genres, key=genres.get), worst_genre=min(genres, key=genres.get))
        
@app.route('/global_stats')
def global_stats():
    '''renders the global stats page'''
    global g_list
    
    #loads the global list from the static file
    with open('./static/global_list.yml','r') as exfile:
        g_list = yaml.load(exfile)
     
    #iterates through each experience in the global list
    profit = 0
    loss_home,loss_tues = 0,0
    for k,v in g_list.items():
        #checks if movie was seen at theater
        if g_list[k]['Theater?'] == "y":
            day = datetime.date(v['Year'],v['Month'],v['Day'])
            #if on a tuesday, adds 8.10 to profits and 7.15 to promotion loss
            if day.weekday() == 1:
                profit += 8.10
                loss_tues += 7.15
            else:
                profit += 15.25
        else:
            #since movie was seen at home, represents a loss of revenue to
            #theater
            loss_home += 15.25
    
    #renders the global stats page with graphs of the above analysis
    #giving visualized info about global trends
    return render_template('global_stats.html', profit='{:.2f}'.format(profit),
                           loss_tues='{:.2f}'.format(loss_tues),
                            loss_home='{:.2f}'.format(loss_home), total_loss='{:.2f}'.format(loss_home+loss_tues))
    
@app.route('/global_theater_graph/')
def global_theater_graph():
    '''pie chart of global trend towards streaming vs. going out to theater'''
    
    #loop to check how many unique experiences were at a movie theater
    in_theater = 0
    for v in g_list.values():
        if v['Theater?'] == 'y':
            in_theater += 1
    
    #declares pygal pie chart object
    pie_chart = pygal.Pie(width=1000, height=500, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    
    pie_chart.title = 'Percentage of movies seen at home'
    #adds catagories, finds math for home viewings by subtracting in_theater
    #from the total number of experiences
    pie_chart.add('At home', len(g_list) - in_theater)
    pie_chart.add('At the theaters', in_theater)
    
    #returns chart to the render_template that requested it
    return Response(response=pie_chart.render(), content_type='image/svg+xml')

@app.route('/global_weekday_graph/')
def global_weekday_graph():
    '''bar graph of global trend for movies seen on certain days of the week'''
    
    #declares an ordered dict of days and sets their viewings to int value of 0
    days = OrderedDict.fromkeys(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    for d in days.keys():
        days[d] = 0
    
    #increments a day when an experience for that weekday is registered
    for v in g_list.values():
        day = datetime.date(v['Year'],v['Month'],v['Day'])
        days[calendar.day_name[day.weekday()]] += 1
    
    #declares pygal bar graph object
    l = pygal.Bar(width=1000, height=500, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    l.title = 'Movies seen per day of week'
    #sets x-axis labels as equal to the keys of the ordered dict
    #and adds the values in the same order
    l.x_labels = days.keys()
    l.add('Weekdays', days.values())
    
    #returns graph to the render_template that requested it
    return Response(response=l.render(), content_type='image/svg+xml')
    
@app.route('/user_theater_graph/')
def user_theater_graph():
    '''pie chart of user's habit for streaming vs. going out to theater'''
    
    #loop to check how many unique experiences were at a movie theater
    in_theater = 0
    for v in m_list.values():
        if v['Theater?'] == 'y':
            in_theater += 1
            
    #declares pygal pie chart object
    pie_chart = pygal.Pie(width=1000, height=500, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    pie_chart.title = 'Percentage of movies seen at home'
    
    #adds catagories, finds math for home viewings by subtracting in_theater
    #from the total number of experiences
    pie_chart.add('At home', len(m_list) - in_theater)
    pie_chart.add('At the theaters', in_theater)
    
    #returns chart to the render_template that requested it
    return Response(response=pie_chart.render(), content_type='image/svg+xml')

@app.route('/user_weekday_graph/')
def user_weekday_graph():
    '''bar graph of user's habit for watching movies on certain weekdays'''
    
    #declares an ordered dict of days and sets their viewings to int value of 0
    days = OrderedDict.fromkeys(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
    for d in days.keys():
        days[d] = 0
    
    #increments a day when an experience for that weekday is registered
    for v in m_list.values():
        day = datetime.date(v['Year'],v['Month'],v['Day'])
        days[calendar.day_name[day.weekday()]] += 1
    
    #declares pygal bar graph object
    l = pygal.Bar(width=1000, height=500, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    l.title = 'Movies seen per day of week'
    #sets x-axis labels as equal to the keys of the ordered dict
    #and adds the values in the same order
    l.x_labels = days.keys()
    l.add('Weekdays', days.values())
    
    #returns graph to the render_template that requested it
    return Response(response=l.render(), content_type='image/svg+xml')

@app.route('/user_genre_graph/')
def user_genre_graph():    
    '''pie chart for what subset of movies the user sees are which genre'''
    
    #declares pygal pie chart object
    p = pygal.Pie(width=1000, height=500, 
                          explicit_size=True, 
                          style=DarkSolarizedStyle, 
                          disable_xml_declaration=True)
    p.title = 'Movies seen split by genre'
    #adds an entry to the pie chart for each genre in the genre list
    for k,v in genres.items():
        p.add(k,v)
        
    #returns chart to the render_template that requested it
    return Response(response=p.render(), content_type='image/svg+xml')
    
if __name__ == '__main__':
    app.secret_key = '[INSERTSUPERSECRETKEYHERE]'
    app.run()