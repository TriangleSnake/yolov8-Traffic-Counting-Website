from flask import *

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(['mov','mp4','avi'])


def check_step(token):# 0.影片還沒上傳 1.畫線階段 2.數車階段 3.上傳YouTube階段 
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
        import os
        if not os.path.exists('./uploads/'+token):
            os.mkdir('./uploads/'+token)
        filepath = './uploads/'+request.cookies.get('token')+'/' + "video."+file.filename.rsplit('.', 1)[1]
        file.save(filepath)
        import cv2
        video = cv2.VideoCapture(filepath)
        video.set(cv2.CAP_PROP_POS_MSEC, 5000)
        ret, frame = video.read()
        cv2.imwrite('./uploads/'+token+'/snapshot.png', frame)
        return make_response('OK', 200)

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
        response.set_cookie('area', points)
        '''
        開畫分析
        '''
        return response

@app.route('/result')
def result():
    token = request.cookies.get('token')
    if not is_vaild_token(token):
        return make_response('Forbidden', 403)
    points = request.cookies.get('area')
    with open('./uploads/'+token+'/area.txt', 'w') as f:
        f.write(points)

    return make_response('Success! We\'re processing your video...', 200)



if __name__ == '__main__':
    app.run(debug=True)