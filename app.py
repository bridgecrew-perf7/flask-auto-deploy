import os, shutil
import subprocess
import re
import shutil
import operator
from flask import Flask, render_template, request, url_for, redirect, flash, make_response
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = "^%huYtFd90;90jjj"

current_folder="/home/psantamaria/www/public/"
public_key="/home/psantamaria/.ssh/id_rsa"
prod_server='psantamaria@www.olfeo.com:/home/psantamaria/'
public_dir = os.getcwd() + "/public/"
archive_dir = os.getcwd() + "/archives/"

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route("/upload", methods=['POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        fully_filename = secure_filename(f.filename)
        print(fully_filename)
        extention = fully_filename.split('.')[1]
        if extention == 'zip':
            filter_filename = 'new' + '.zip'
            f.save(public_dir + filter_filename) 
            check = checking(filename=filter_filename)
            if check:
                good = sendToProd(filename=filter_filename) 
                if good:
                    flash("Les fichiers ont bien été remplacés")
                else:
                    flash("Il y a eu un problème lors de l'envoie de fichier")
                deleting()
                return redirect(url_for("index"))
            else:
                deleting()
                flash('Veuilliez comprésser le contenu du dossier contenant la plateforme Paligo')
                return redirect(url_for("index"))
            
        else:
            flash('Le fichier doit etre un .zip')
            return redirect(url_for("index"))
    else:
         return redirect(url_for("index"))

@app.route('/archives')
def archive():
    dl = os.listdir(archive_dir)
    dl.sort()
    dl.reverse()
    dl_src = ['/archives/{}'.format(i) for i in dl]
    
    return render_template('archive.html', dl=dl, dl_src=dl_src)

@app.route('/archives/<name>')
def download(name):
    (file_basename, server_path) = name, archive_dir + name
    response = make_response()
    response.headers['Content-Description'] = 'File Transfer'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename=%s' % file_basename
    response.headers['X-Accel-Redirect'] = server_path # nginx: http://wiki.nginx.org/NginxXSendfile

    return response

#check if zip infra is correct      
def checking(filename):
    unzip = " unzip -l ./public/new.zip  | awk {'print $4'} | grep ^index.html"
    sucess = subprocess.call(unzip, shell=True)
    if sucess == 0:
        return True
    else: 
        return False

def deleting():
    list_dir = os.listdir(public_dir)
    for f in list_dir:
        file_path = os.path.join(public_dir, f)
        if os.path.isfile(file_path):
            archiving(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def archiving(file_path):
    if file_path.split('.')[1] != 'zip':
        os.unlink(file_path)
    else:
        shutil.move(file_path, 'archives/' + datetime.today().strftime('%Y-%m-%d-%H:%M') + ".zip")
    
#send file to prod server
def sendToProd(filename):
    bash = 'rsync -av '+ current_folder + filename + ' -e "ssh -i '+ public_key + '" ' + prod_server
    subprocess.call(bash, shell=True)
    cmd = [
        'ssh psantamaria@www.olfeo.com tar czvf ./archive/$(date +%Y%m%d_%H%M%S).tar.gz ./www/*',
        'ssh psantamaria@www.olfeo.com sudo rm -r www/*',
        'ssh psantamaria@www.olfeo.com unzip new -d /home/psantamaria/www/',
        'ssh psantamaria@www.olfeo.com sudo rm -r new.zip',
        'ssh psantamaria@www.olfeo.com sudo service apache2 restart',
    ]
    for i in cmd:
        check = subprocess.call(i, shell=True)
        if check != 0:
            return False
    return True

if __name__ == '__main__':
    app.run(debug=True)
