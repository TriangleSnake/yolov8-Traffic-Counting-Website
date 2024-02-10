from flask import *
import sys
import cv2
import json
import os
import subprocess
#import torch
app = Flask(__name__)
app.secret_key = 'secret_key'
ALLOWED_EXTENSIONS = set(['mov','mp4','avi'])
FILETYPE = "mp4"
FRAME_RATE = 5



def count(token):
    video_path = 'uploads/'+token+'/video'
    area_path = 'uploads/'+token+'/area.txt'
    output_path = 'uploads/'+token+'/output.' + FILETYPE
    result_path = 'uploads/'+token+'/result.txt'
    frame_path = 'uploads/'+token+'/frame.jpg'
    with open(area_path, 'r') as f:
        area = json.loads(f.read())
    #torch.cuda.set_device(1)
    
    while not os.path.exists(result_path):
        
        if os.path.exists(frame_path):
                frame = cv2.imread(frame_path)
        else :
                frame = cv2.imread("uploads/"+token+"/snapshot.png")
        try:
            ret,buffer = cv2.imencode(".jpg", frame)
        except:
            continue
        frame = buffer.tobytes()
        yield(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
    return "OK"
    
        

def check_step(token):# 0.影片還沒上傳 1.畫線階段 2.數車階段 3.結果階段
    import os
    if not is_vaild_token(token):
        return -1
    
    if os.path.exists('./uploads/'+token+'/result.txt'):
        return 3
    elif os.path.exists('./uploads/'+token+'/area.txt'):
        return 2
    elif os.path.exists('./uploads/'+token+'/snapshot.png'):
        return 1
    else:
        return 0

def is_vaild_token(token):
    with open('token.txt', 'r') as f:
        tokens = f.read().split('\n')
        if token in tokens:
            return True
        else:
            return False

def allowed_filetype(filename: str):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/uploads/<path:token>/snapshot.png')
def get_snapshot(token):
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    return send_file('./uploads/'+token+'/snapshot.png')


@app.route('/')
def index():
    session.clear()
    if request.args.get('token'):
        if is_vaild_token(request.args.get('token')):
            response = make_response(redirect(url_for('upload_page')))
            response.set_cookie('token', request.args.get('token'))
            return response
        else:
            return make_response('Wrong token', 403)
    return render_template('index.html')


@app.get('/upload')
def upload_page():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    if check_step(token) > 0:
        return redirect(url_for('draw'))
    return render_template('upload.html')


@app.post('/upload')
def upload():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    if check_step(token) > 0:
        return redirect(url_for('draw'))

    file = request.files['file']
    if file and allowed_filetype(file.filename):
        
        if not os.path.exists('./uploads/'+token):
            os.mkdir('./uploads/'+token)
        filepath = './uploads/'+request.cookies.get('token')+'/' + "video" #+file.filename.rsplit('.', 1)[1]
        file.save(filepath)
        video = cv2.VideoCapture(filepath)
        video.set(cv2.CAP_PROP_POS_MSEC, 5000)
        ret, frame = video.read()
        cv2.imwrite('./uploads/'+token+'/snapshot.png', frame)
        return make_response('OK', 200)
    return make_response('Bad Filetype', 400)

@app.route('/draw', methods=['GET', 'POST'])
def draw():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    
    if check_step(token) > 1:
        return redirect(url_for('result'))
    elif check_step(token) < 1:
        return redirect(url_for('upload_page'))

    if request.method == 'GET':
        return render_template('draw.html')
    elif request.method == 'POST':
        points = request.form['points']
        response = make_response(redirect(url_for('result')))
        with open('./uploads/'+token+'/area.txt', 'w') as f:
            f.write(points)
        return response



@app.route('/result')
def result():
    global sub_count
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    if check_step(token) < 2:
        return redirect(url_for('draw'))
    
    if check_step(token) > 2:
        return send_file('./uploads/'+token+'/output.mp4')    
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    if 'pid' in session:
        sub_count.kill()
    sub_count = subprocess.Popen(["python", "count.py", token])
    session['pid'] = sub_count.pid
    return make_response("<img src=/uploads/"+token+"/frame>", 200)

@app.route('/uploads/<path:token>/frame')
def output(token):
    return Response(count(token), mimetype='multipart/x-mixed-replace; boundary=frame')
if __name__ == '__main__':
    app.run("127.0.0.1",20000)