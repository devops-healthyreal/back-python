import warnings

warnings.filterwarnings('ignore')
import numpy as np
import cv2
from scipy.ndimage import zoom
from flask_restful import Resource, reqparse
from werkzeug.datastructures import FileStorage
from tensorflow.keras.models import load_model
import os

# 모델 로드
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'face.h5')

model = load_model(MODEL_PATH)


class FaceEmotion(Resource):
    def post(self):
        # 파일 업로드를 처리하기 위한 파서 생성
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files')
        args = parser.parse_args()

        # 업로드된 파일을 읽음
        file = args['file']
        if file is None:
            return {'error': 'No file provided'}, 400

        file_path = os.path.join(os.getcwd(), 'temp.png')
        file.save(file_path)

        # 예측
        face = cv2.imread(file_path)
        gray, detected_faces, coord = self.detect_face(face)
        face_zoom = self.extract_face_features(gray, detected_faces, coord)
        if not face_zoom:
            return {'error': 'Face detection failed'}, 400
        input_data = np.reshape(face_zoom[0].flatten(), (1, 48, 48, 1))
        output_data = model.predict(input_data)
        result = np.argmax(output_data)

        # 결과 출력
        emotions = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        return {'emotion': emotions[result]}

    def detect_face(self, frame):
        shape_x = 48
        shape_y = 48
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_faces = face_cascade.detectMultiScale(gray,
                                                       scaleFactor=1.1,
                                                       minNeighbors=6,
                                                       minSize=(shape_x, shape_y),
                                                       flags=cv2.CASCADE_SCALE_IMAGE
                                                       )
        coord = []
        for x, y, w, h in detected_faces:
            if w > 100:
                sub_img = frame[y:y + h, x:x + w]
                coord.append([x, y, w, h])
        return gray, detected_faces, coord

    def extract_face_features(self, gray, detected_faces, coord, offset_coefficients=(0.075, 0.05)):
        shape_x = 48
        shape_y = 48
        new_face = []
        for det in detected_faces:
            x, y, w, h = det
            horizontal_offset = np.int64(np.floor(offset_coefficients[0] * w))
            vertical_offset = np.int64(np.floor(offset_coefficients[1] * h))
            extracted_face = gray[y + vertical_offset:y + h, x + horizontal_offset:x - horizontal_offset + w]
            new_extracted_face = zoom(extracted_face,
                                      (shape_x / extracted_face.shape[0], shape_y / extracted_face.shape[1]))
            new_extracted_face = new_extracted_face.astype(np.float32)
            new_extracted_face /= float(new_extracted_face.max())
            new_face.append(new_extracted_face)
        return new_face
