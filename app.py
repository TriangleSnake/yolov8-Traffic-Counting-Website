from flask import *
import cv2
import json
import os
import counting
import threading
import ffmpeg
import shutil
import time
#import torch
app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['mov','mp4','avi'])
FILETYPE = "mp4"
FRAME_RATE = 5
app.secret_key = "secret key"
prev_frame = ""

def check_step(token):# 0.影片還沒上傳 1.畫線階段 2.數車階段 3.結果階段
    if not is_vaild_token(token):
        return -1
    if os.path.exists('./uploads/' + token + '/result.txt'):
        return 4
    elif os.path.exists('./uploads/'+token+'/output.mp4'):
        return 3
    elif os.path.exists('./uploads/'+token+'/area.txt'):
        return 2
    elif os.path.exists('./uploads/'+token+'/snapshot.jpg'):
        return 1
    else:
        return 0

def compress_video(token):
    input_file = './uploads/'+token+'/video'
    output_file = './uploads/'+token+'/video(compressed).mp4'
    input_file = ffmpeg.input(input_file)
    input_file = input_file.filter('scale', f"iw*{0.5}", f"ih*{0.5}")
    output_file = input_file.output(output_file, vcodec='libx264',crf=30,preset='ultrafast',r=15)
    output_file.run()
    with open("./uploads/"+token+"/compressed.txt","w") as f:
        f.write("OK")

def count(token):
    global prev_frame
    video_path = 'uploads/'+token+'/video'
    area_path = 'uploads/'+token+'/area.txt'
    output_path = 'uploads/'+token+'/output.' + FILETYPE
    result_path = 'uploads/'+token+'/result.txt'
    frame_path = 'uploads/'+token+'/frame.jpg'
    with open(area_path, 'r') as f:
        area = json.loads(f.read())
    #torch.cuda.set_device(1)
    
    while not os.path.exists(result_path):
        try:
            frame = cv2.imread(frame_path)
            cv2.putText(frame,"Processing...",(0,300),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2,cv2.LINE_AA)
            cv2.putText(frame,"DO NOT CLOSE THE PAGE...",(0,350),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2,cv2.LINE_AA)
            
            ret,buffer = cv2.imencode(".jpg", frame)
            prev_frame = buffer
        except:
            buffer = prev_frame
        frame = buffer.tobytes()
        time.sleep(0.1)
        print("sending...")
        yield(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    frame = cv2.imread(frame_path)
    cv2.putText(frame,"DONE!",(0,300),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2,cv2.LINE_AA)
    cv2.putText(frame,"Click to Download Output Video",(0,350),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),2,cv2.LINE_AA)
    ret,buffer =cv2.imencode(".jpg",frame)
    frame = buffer.tobytes()
    while 1:
        yield(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    
        



def is_vaild_token(token):
    with open('token.txt', 'r') as f:
        tokens = f.read().split('\n')
        if token in tokens:
            return True
        else:
            return False

def allowed_filetype(filename: str):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/uploads/<path:token>/snapshot.jpg')
def get_snapshot(token):
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    return send_file('./uploads/'+token+'/snapshot.jpg')


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
    return render_template('upload.html')

@app.post('/upload')
def upload():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    file = request.files['file']
    if file and allowed_filetype(file.filename.lower()):
        if os.path.exists('./uploads/'+token):
            shutil.rmtree('./uploads/'+token+'/')
        os.mkdir('./uploads/'+token)
        filepath = './uploads/'+ token +'/' + "video" #+file.filename.rsplit('.', 1)[1]
        file.save(filepath)
        threading.Thread(target=compress_video,args=(token,)).start()
        return redirect(url_for('compressing'))
    return make_response('Bad Filetype', 400)

@app.get('/compressing')
def compressing():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    
    if not os.path.exists('./uploads/'+token+'/compressed.txt'):
        return make_response('<br>Compressing</br><script>setTimeout("location.reload();",5000)</script>', 200)

    filepath = './uploads/'+ token +'/' + "video(compressed).mp4"
    video = cv2.VideoCapture(filepath)
    video.set(cv2.CAP_PROP_POS_MSEC, 5000)
    ret, frame = video.read()
    cv2.imwrite('./uploads/'+token+'/snapshot.jpg', frame)
    return redirect(url_for('draw'))

@app.route('/draw', methods=['GET', 'POST'])
def draw():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    if os.path.exists('./uploads/'+token+'/video(compressed).mp4'):
        os.remove('./uploads/'+token+'/video')
        os.rename('./uploads/'+token+'/video(compressed).mp4','./uploads/'+token+'/video')
    try:
        os.remove('./uploads/'+token+'/output.mp4')
        os.remove('./uploads/'+token+'/result.txt')
    except:
        pass
    if check_step(token) < 1:
        return redirect(url_for('upload_page'))

    if request.method == 'GET':
        return render_template('draw.html')
    elif request.method == 'POST':
        
        points = request.form['points']
        response = make_response(redirect(url_for('result')))
        with open('./uploads/'+token+'/area.txt', 'w') as f:
            f.write(points)
        try:
            os.remove("./uploads/"+token+'/result.txt')
        except:
            pass
        return response



@app.route('/result')
def result():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    if check_step(token) < 2:
        return redirect(url_for('draw'))
    '''
    elif check_step(token) == 4:
        return send_file('./uploads/'+token+'/output.mp4',as_attachment=True)    
    '''
    if check_step(token)  < 3:
        threading.Thread(target=counting.run,args=(token,)).start()
    
    #subprocess.Popen(["python", "count.py", token])
    return make_response("<img src=/uploads/"+token+f"/frame><br><button onclick=\"location.href='/uploads/{token}/output.mp4'\">運算完成後點我下載</button>", 200)

@app.route('/uploads/<path:token>/frame')
def output(token):
    global prev_frame
    prev_frame = cv2.imread('uploads/'+token+'/snapshot.jpg')
    ret, prev_frame = cv2.imencode(".jpg",prev_frame)
    return Response(count(token), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/uploads/<path:token>/output.mp4')
def send_video(token):
    if not is_vaild_token(token):
        return make_response('Hacker!!!',403)
    return send_file('./uploads/'+token+'/output.mp4',as_attachment=True,download_name="test")

if __name__ == '__main__':
    #app.run("127.0.0.1",20000)
    app.run("0.0.0.0",20000)