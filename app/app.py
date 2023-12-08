from flask import Flask, request, render_template, Response, redirect, url_for, send_file
from flask_wtf import FlaskForm
from wtforms import FileField
from werkzeug.utils import secure_filename
import os
import io
import cv2
from cvzone.PoseModule import PoseDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'


class UploadForm(FlaskForm):
    video = FileField('動画ファイル')


def generate_frames(filename):
    cap = cv2.VideoCapture(filename)
    detector = PoseDetector()

    while True:
        success, img = cap.read()
        if not success:
            break
        img = detector.findPose(img)

        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def motion_caputure(filename):
    cap = cv2.VideoCapture(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    detector = PoseDetector()
    posList = []
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    center = int(width / 2)
    nose_postion = 335

    while True:
        success, img = cap.read()
        if not success:
            break
        img = detector.findPose(img)
        lmList, bboxInfo = detector.findPosition(img)

        if bboxInfo:
            lmString = ''
            for lm in lmList:
                lmString += f'{round((lm[0] - center) / nose_postion, 2)},{round((img.shape[0]-lm[1]) / nose_postion, 2)},{round(lm[2] / 4 / nose_postion, 2)},'
            posList.append(lmString)

    return '\n'.join(map(str, posList)) + '\n'


@app.route('/video_feed/<filename>')
def video_feed(filename):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return Response(generate_frames(video_path), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        video_file = form.video.data
        if video_file:
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_path)
            if 'video_feed' in request.form:
                return redirect(url_for('video_feed', filename=filename))
            elif 'motion_capture' in request.form:
                motion_data = motion_caputure(filename)
                os.remove(video_path)
                return send_file(
                    io.BytesIO(motion_data.encode('utf-8')),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name='motion.csv'
                )

    return render_template('index.html', form=form)


if __name__ == '__main__':
    app.run()
