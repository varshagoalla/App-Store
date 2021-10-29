from flask import Flask, render_template,request,session,redirect,flash
import psycopg2
import os,sys

con = psycopg2.connect(
    host = "10.17.5.99",
    database = "group_42",
    user = "group_42",
    password = "2kfmkmgkmmdCe",
    port = 5432
)
cur = con.cursor()

app = Flask(__name__)
app.secret_key=os.urandom(30)


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/userhome')
def userhome():
    if 'user_id' in session:
        cur.execute("""select * from app_id_name""")
        l = cur.fetchall()
        return render_template('userhome.html',apps_list = l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/developerhome')
def developerhome():
    if 'dev_id' in session:
        cur.execute("""select ai.app_id,ai.app_name from (select app_id from developed where developer_id='{}') as a,app_id_name as ai
        where a.app_id=ai.app_id""".format(session["dev_id"]))
        l=cur.fetchall()
        return render_template('developerhome.html',apps_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')


@app.route('/signup_result',methods=['POST'])
def signup_result():
    username=request.form.get('username')
    name=request.form.get('name')
    emailid=request.form.get('emailid')
    password=request.form.get('password')
    try:
        cur.execute("savepoint my_save_point")
        cur.execute("""INSERT INTO users (id,name,username,password,emailid) VALUES (DEFAULT,$${}$$,$${}$$,$${}$$,$${}$$);""".format(name,username,password,emailid))
    except:
        flash("Registration failed.")
        cur.execute("""rollback to savepoint my_save_point""")
        return redirect('/signup')
    else:
        con.commit()
        cur.execute("""select * from users where username = $${}$$ and password = $${}$$""".format(username,password))
        users=cur.fetchall()
        session['user_id']=users[0][0]
        flash("Signed Up. Login Successfull!!")
        return redirect('/userhome')

@app.route('/login_result',methods=['POST'])
def login_result():
    username=request.form.get('username')
    password=request.form.get('password')
    identity=request.form.get('identity')
    if identity=='user':
        cur.execute("""select * from users where username = $${}$$ and password = $${}$$""".format(username,password))
        users = cur.fetchall()
        if len(users)==1:
            session['user_id']=users[0][0]
            flash("Login Successfull!!")
            return redirect('/userhome')
    else:
        cur.execute("""select * from developer where username = $${}$$ and password = $${}$$""".format(username,password))
        users = cur.fetchall()
        if len(users)==1:
            session['dev_id']=users[0][0]
            flash("Login Successfull!!")
            return redirect('/developerhome')
    return redirect('/')

@app.route('/filter')
def filter():
     return render_template('filter.html')

def array_literal(s):
    out = '{'
    for i in range(len(s)-1):
        out+=s[i]
        out+=','
    out+=s[len(s)-1]
    out+='}'
    return out 



@app.route('/filterdone',methods=['POST'])
def filterdone():
    if 'user_id' in session:
        version=array_literal(request.form.getlist('F/P'))
        category=array_literal(request.form.getlist('category'))
        sort=request.form.get('sort')
        if sort=="ratings":
            cur.execute("""select a.app_id,a.app_name,c.name,a.free_paid,a.rating
            from (select app_id,app_name,category_id,rating,free_paid
            from app
            where free_paid=ANY('{}') and rating!='NaN'
            order by rating desc,app_name asc) as a
            join (select * from category where name=ANY($${}$$)) as c on c.id=a.category_id""".format(version,category))
        elif sort=="Asc":
            cur.execute("""select a.app_id,a.app_name,c.name,a.free_paid,a.rating
            from (select app_id,app_name,category_id,rating,free_paid
            from app
            where free_paid=ANY('{}') and rating!='NaN'
            order by app_name asc,rating desc) as a
            join (select * from category where name=ANY($${}$$)) as c on c.id=a.category_id""".format(version,category))
        else:
            cur.execute("""select a.app_id,a.app_name,c.name,a.free_paid,a.rating
            from (select app_id,app_name,category_id,rating,free_paid
            from app
            where free_paid=ANY('{}') and rating!='NaN'
            order by app_name desc,rating desc) as a
            join (select * from category where name=ANY($${}$$)) as c on c.id=a.category_id""".format(version,category))
        return  render_template('filterdone.html',apps_list=cur.fetchall())
    else:
        flash("Session Expired!!")
        return redirect('/')    

@app.route('/profile')
def profile():
    if 'user_id' in session:
        s=session['user_id']
        cur.execute("""select * from users where users.id='{}'""".format(s))
        l=cur.fetchall()
        return render_template('profile.html',input_name=l[0][1],input_uname=l[0][2],input_emailid=l[0][4])
    else:
        flash("Session Expired!!")
        return redirect('/')
    
@app.route('/developerprofile')
def developerprofile():
    if 'dev_id' in session:
        cur.execute("""select * from developer where id='{}'""".format(session['dev_id']))
        l=cur.fetchall()
        return render_template('developerprofile.html',input_name=l[0][1],input_uname=l[0][2],input_emailid=l[0][4])
    else:
        flash("Session Expired!!")
        return redirect('/')
@app.route('/apppage/<id>')
def apppage(id):
    if 'user_id' in session:
        cur.execute("""select a.app_name,a.rating,a.reviews,a.size,a.installs,a.free_paid,a.price,a.genres,a.last_updated,
a.current_ver,a.android_ver,c.name,cr.content_rating
from (select * from app where app.app_id='{}') as a,category as c,contentrating as cr
where a.category_id=c.id and a.contentrating_id=cr.id""".format(id))
        l=cur.fetchall()
        cur.execute("""select * from installed where user_id='{}' and app_id='{}'""".format(session['user_id'],id))
        k = len(cur.fetchall())
        cur.execute("""select u.username,r.review from (select user_id,review from review where app_id='{}') as r,
        (select id,username from user_id_name) as u where r.user_id=u.id""".format(id))
        r=cur.fetchall()
        cur.execute("""select * from review where user_id='{}' and app_id='{}'""".format(session['user_id'],id))
        p=len(cur.fetchall())
        return render_template('apppage.html',name=l[0][0],rating=l[0][1],reviews=l[0][2],size=l[0][3],installs=l[0][4],free_paid=l[0][5],price=l[0][6],genres=l[0][7],last_updated=l[0][8],current_ver=l[0][9],android_ver=l[0][10],category=l[0][11],content_rating=l[0][12],id=id,installed=k,review=r,check=p)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/installed')
def installed():
    if 'user_id' in session:
        cur.execute("""select a.app_id,a.app_name from (select app_id from installed where user_id='{}') as i,app_id_name as a where i.app_id=a.app_id""".format(session['user_id']))
        l=cur.fetchall()
        return render_template('user_apps.html',apps_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/uninstalled')
def uninstalled():
    if 'user_id' in session:
        cur.execute("""select a.app_id,a.app_name from (select app_id from uninstalled where user_id='{}') as i,app_id_name as a where i.app_id=a.app_id""".format(session['user_id']))
        l=cur.fetchall()
        return render_template('user_apps.html',apps_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/searchhistory')
def searchhistory():
    if 'user_id' in session:
        cur.execute("""select history from search_history where user_id='{}' order by id desc""".format(session['user_id']))
        l=cur.fetchall()
        return render_template('searchhistory.html',s_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/editprofile',methods=['POST'])
def editprofile():
    name=request.form.get('n_name')
    username=request.form.get('n_username')
    password=request.form.get('n_password')
    emailid=request.form.get('n_emailid')
    if 'user_id' in session:
        try:
            cur.execute("savepoint my_save_point")
            cur.execute("""UPDATE users SET username = $${}$$, name=$${}$$,password=$${}$$,emailid=$${}$$ where id='{}'""".format(username,name,password,emailid,session['user_id']))
        except:
            cur.execute("""rollback to savepoint my_save_point""")
            flash("Username/EmailID exists or Spaces are used. Edit failed")
        else:
            con.commit()
            flash("Profile Edited!!")
        return redirect('/profile')
    elif 'dev_id' in session:
        try:
            cur.execute("savepoint my_save_point")
            cur.execute("""UPDATE developer SET username = $${}$$, name=$${}$$,password=$${}$$,emailid=$${}$$ where id='{}'""".format(username,name,password,emailid,session['dev_id']))
        except:
            cur.execute("""rollback to savepoint my_save_point""")
            flash("Username/EmailID exists or Spaces are used. Edit failed")
        else:
            con.commit()
            flash("Profile Edited!!")
        return redirect('/developerprofile')
    else:
        flash("Session Expired!!")
        return redirect('/')
    
@app.route('/install/<id>')
def install(id):
     #insert into installed
     #delete from uninstalled
    if 'user_id' in session:
        try:
            cur.execute("""INSERT INTO installed (user_id,app_id)
            VALUES ('{}','{}')""".format(session['user_id'],id))
            cur.execute("""DELETE FROM uninstalled where user_id='{}' and app_id='{}'""".format(session['user_id'],id))
            con.commit()
        except:
            print("It was not there in uninstalled")        
        return redirect('/apppage/'+id)
    else:
        flash("Session Expired!!")
        return redirect('/')
@app.route('/uninstall/<id>')
def uninstall(id):
    if 'user_id' in session:
        try:
            cur.execute("""INSERT INTO uninstalled (user_id,app_id)
            VALUES ('{}','{}')""".format(session['user_id'],id))
            cur.execute("""DELETE FROM installed where user_id='{}' and app_id='{}'""".format(session['user_id'],id))
            con.commit()
        except:
            print("")        
        return redirect('/apppage/'+id)        
    else:
        flash("Session Expired!!")
        return redirect('/')
@app.route('/search',methods=['POST'])
def search():
    if 'user_id' in session:
        name=request.form.get('search')
        cur.execute("""select * from app_id_name where app_name=$${}$$""".format(name))
        l=cur.fetchall()
        cur.execute("""INSERT INTO search_history (id,user_id,history)
        VALUES (DEFAULT,'{}',$${}$$)""".format(session['user_id'],name))
        con.commit()
        return render_template('/user_apps.html',apps_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/writereview/<id>',methods=['POST'])
def writereview(id):
    if 'user_id' in session:
        review=request.form.get('review')
        cur.execute("""INSERT INTO review (user_id,app_id,review)
        VALUES ('{}','{}',$${}$$)""".format(session['user_id'],id,review))
        con.commit()
        return redirect('/apppage/'+id)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/myreviews')
def myreviews():
    if 'user_id' in session:
        cur.execute("""select a.app_name,r.review from (select app_id,review from review where user_id='{}') as r,app_id_name as a where a.app_id=r.app_id""".format(session['user_id']))
        l=cur.fetchall()
        return render_template('myreviews.html',review=l)
    else:
        fflash("Session Expired!!")
        return redirect('/')

@app.route('/upload')
def upload():
    return render_template('upload.html')

def category(a):
    cur.execute("""select id from category where name=$${}$$""".format(a))
    l=cur.fetchall()
    return l[0][0]

@app.route('/upload_result',methods=['POST'])
def upload_result():
    if 'dev_id' in session:
        app_name=request.form.get('app_name')
        size=request.form.get('size')
        free_paid=request.form.get('f/p')
        price=request.form.get('price')
        genres=request.form.get('genres')
        category_id=category(request.form.get('category'))
        last_up=request.form.get('last_updated')
        curr_ver=request.form.get('current_ver')
        and_ver=request.form.get('android_ver')
        cr=request.form.get('cr')
        rating='NaN'
        reviews="Data Unavailable"
        installs="Data Unavailble"
        cur.execute("""select app_id from app_id_name where app_name='{}'""".format(app_name))
        l=cur.fetchall()
        if len(l)==0:
            cur.execute("""INSERT INTO app (app_id,app_name,category_id,rating,reviews,size,installs,free_paid,price,
            contentrating_id,genres,last_updated,current_ver,android_ver) VALUES (DEFAULT,'{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}',
            '{}','{}')""".format(app_name,category_id,rating,reviews,size,installs,free_paid,price,
            cr,genres,last_up,curr_ver,and_ver))
            cur.execute("""select app_id from app_id_name where app_name='{}'""".format(app_name))
            l=cur.fetchall()
            m=l[0][0]
            print(m)
            cur.execute("""INSERT INTO developed (developer_id,app_id)  VALUES ('{}','{}')""".format(session['dev_id'],m))
            con.commit()
        else:
            flash("An app is already present with this name. Choose another name")
            return redirect('/upload')
        return redirect('/developerhome')
    else:
        flash("Session Expired!")
        return redirect('/')
@app.route('/developerapppage/<id>')
def developerapppage(id):
    if 'dev_id' in session:
        cur.execute("""select a.app_name,a.rating,a.reviews,a.size,a.installs,a.free_paid,a.price,a.genres,a.last_updated,
a.current_ver,a.android_ver,c.name,cr.content_rating
from (select * from app where app.app_id='{}') as a,category as c,contentrating as cr
where a.category_id=c.id and a.contentrating_id=cr.id""".format(id))
        l=cur.fetchall()
        cur.execute("""select u.username,r.review from (select user_id,review from review where app_id='{}') as r,
        (select id,username from user_id_name) as u where r.user_id=u.id""".format(id))
        r=cur.fetchall()
        return render_template('developerapppage.html',name=l[0][0],rating=l[0][1],reviews=l[0][2],size=l[0][3],installs=l[0][4],free_paid=l[0][5],price=l[0][6],genres=l[0][7],last_updated=l[0][8],current_ver=l[0][9],android_ver=l[0][10],category=l[0][11],content_rating=l[0][12],id=id,review=r)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/appusers/<id>')
def appusers(id):
    if 'dev_id' in session:
        cur.execute("""select ui.username from (select user_id from installed where app_id='{}') as u,user_id_name as ui
        where ui.id=u.user_id""".format(id))
        l=cur.fetchall()
        return render_template('appusers.html',user_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/suggestions')
def suggestions():
    if 'dev_id' in session:
        cur.execute("""select ai.app_id,ai.app_name from (select a.app_id from (select distinct i.app_id from (select distinct i.user_id
        from (select app_id from developed where developer_id='{}') as da join installed as i on i.app_id=da.app_id) as u
        join installed as i on i.user_id=u.user_id) as a,(select ARRAY_AGG(app_id) as arr from developed where developer_id='{}') as da
        where a.app_id!=all(da.arr)) as a,app_id_name as ai where a.app_id=ai.app_id""".format(session['dev_id'],session['dev_id']))
        l=cur.fetchall()
        return render_template('suggestions.html',apps_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/delete/<id>')
def delete(id):
    if 'dev_id' in session:
        cur.execute("""DELETE FROM app where app_id='{}'""".format(id))      
        con.commit()
        return redirect('/developerhome')
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/logout')
def logout():
    if 'dev_id' in session:
        session.pop('dev_id')
        flash("Logged Out!!")
    elif 'user_id' in session:
        session.pop('user_id')
        flash("Logged Out!!")
    else:
        flash("Session Expired!!")
    return redirect('/')

@app.route('/usersuggestions')
def usersuggestions():
    if 'user_id' in session:
        s=session['user_id']
        cur.execute("""select ai.app_id,ai.app_name from (select a.app_id
        from (select distinct i.app_id
        from (select distinct i.user_id 
        from (select app_id from installed where user_id='{}') as a,installed as i
        where i.app_id=a.app_id and i.user_id!='{}') as u
        join installed as i on i.user_id=u.user_id) as a,(select ARRAY_AGG(app_id) as arr from installed where user_id='{}') as ua
        where a.app_id!=all(ua.arr)) as a, app_id_name as ai
        where a.app_id=ai.app_id""".format(s,s,s))
        l=cur.fetchall()
        return render_template('usersuggestions.html',apps_list=l)
    else:
        flash("Session Expired!!")
        return redirect('/')

@app.route('/deleteaccount')
def deleteaccount():
    if 'user_id' in session:
        s=session['user_id']
        cur.execute("""DELETE from users where users.id='{}'""".format(s))
        con.commit()
        flash("Account Deleted")
    else:
        flash("Session Expired")
        return redirect('/')

@app.route('/add/<id>',methods=['POST'])
def add(id):
    if 'dev_id' in session:
        username=request.form.get('username')
        cur.execute("""select id from developer where username=$${}$$""".format(username))
        l=cur.fetchall()
        if len(l)==0:
            flash("Invalid Username")
        else:
            id_2=l[0][0]
            cur.execute("""select * from developed where developer_id='{}' and app_id='{}'""".format(id_2,id))
            l=cur.fetchall()
            if len(l)==0:
                cur.execute("""INSERT INTO developed (developer_id,app_id)
                VALUES ('{}','{}');""".format(id_2,id))
            else:
                flash("Already a co-developer")
        return redirect('/developerapppage/'+id)            
    else:
        flash("Session Expired")
        return redirect('/')
    
if __name__ == "__main__":
    app.run(host="localhost", port=5042, debug=True)



