import os

from flask import request
from flask_restful import Resource
import cv2
import numpy as np
from google.cloud import vision
from google.oauth2 import service_account
import re
from PIL import Image
import logging
from dotenv import load_dotenv

load_dotenv()

# 스케일링 요소 설정
scale_factor = 2
# 이미지 전처리 및 자르기
section_ratio = (0.0, 0.1, 0.7, 0.5)

GOOGLE_APPLICATION_CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
print(GOOGLE_APPLICATION_CREDENTIALS_PATH)

def get_vision_client():
    if GOOGLE_APPLICATION_CREDENTIALS_PATH and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS_PATH):
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS_PATH)
        print("경로 찾음")
        client = vision.ImageAnnotatorClient(credentials=credentials)
    else:
        print("경로 못찾음")
        client = vision.ImageAnnotatorClient()
    return client

class inOcr(Resource):
    def post(self):
        # 뷰에서 받은 이미지 데이터
        image_file = request.files.get('file')

        if image_file:
            logging.info('Received file: %s', image_file.filename)
            logging.info('File contents: %s', image_file.read())

            image_file.seek(0)  # Move file pointer back to start after reading
            image = Image.open(image_file.stream)
            image_np = np.array(image)

            processed_image = make_scan_image(image_np, section_ratio, scale_factor)

            # OCR 수행
            texts = detect_text(processed_image)

            pattern = r'^\d*\.\d+$'
            matched_texts = []
            for text in texts:
                if re.fullmatch(pattern, text):
                    # 실수로 변환
                    num = float(text)
                    # 100 이상이면 100을 빼고 저장
                    if num >= 140:
                        num -= 100
                    # 소수점 두 번째 자리에서 반올림
                    num = round(num, 2)
                    matched_texts.append(num)
            return matched_texts  # OCR 결과 리턴



def preprocess_image(image, scale_factor):
    # 흑백 이미지로 변환
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 노이즈 제거
    denoised_image = cv2.fastNlMeansDenoising(gray_image, None, 10, 7, 21)

    # 이미지 스케일링
    resized_image = cv2.resize(denoised_image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    return resized_image


def make_scan_image(image, section_ratio, scale_factor):
    # 이미지 전처리
    image = preprocess_image(image, scale_factor)

    # 이미지 자르기
    h, w = image.shape[:2]
    x, y, rw, rh = section_ratio
    section = (int(w * x), int(h * y), int(w * rw), int(h * rh))
    cropped = image[section[1]:section[1] + section[3], section[0]:section[0] + section[2]]

    return cropped


def detect_text(image):
    client = get_vision_client()
    # OpenCV 이미지를 임시 파일로 저장
    cv2.imwrite('temp.png', image)
    with open('temp.png', "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image, image_context={"language_hints": ["ko"]})
    texts = response.text_annotations
    print("Texts:")
    filtered_texts = []
    for text in texts:
        '''
        print(f'\n"{text.description}"')
        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]
        print("좌표: {}".format(",".join(vertices)))
        '''
        vertices = [(vertex.x, vertex.y) for vertex in text.bounding_poly.vertices]
        # 텍스트 블록의 너비와 높이 계산
        width = max(vertices, key=lambda x: x[0])[0] - min(vertices, key=lambda x: x[0])[0]
        height = max(vertices, key=lambda x: x[1])[1] - min(vertices, key=lambda x: x[1])[1]

        # 텍스트 블록의 너비와 높이를 기준으로 필터링
        '''
        if (150 <= vertices[0][0] <= 250) and (100 <= vertices[0][1] <= 340):
            filtered_texts.append((text.description, vertices[0][1]))
            print(f'\n"{text.description}"')
            print("좌표: {}".format(",".join(map(str, vertices))))
        '''
        if (150 <= vertices[0][0] <= 500) and (350 <= vertices[0][1] <= 600) and (30 < width and 10 < height):
            filtered_texts.append((text.description, vertices[0][1]))
            print(f'\n"{text.description}"')
            print("좌표: {}".format(",".join(map(str, vertices))))
        if (150 <= vertices[0][0] <= 500) and (600 <= vertices[0][1] <= 750) and (30 < width and 10 < height):
            filtered_texts.append((text.description, vertices[0][1]))
            print(f'\n"{text.description}"')
            print("좌표: {}".format(",".join(map(str, vertices))))


    # y 좌표가 낮은 순으로 정렬
    filtered_texts = sorted(filtered_texts, key=lambda x: x[1])
    # y 좌표 정보를 제거하고 텍스트만 남김
    filtered_texts = [text for text, _ in filtered_texts]
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )
    return filtered_texts  # 필터링된 텍스트 반환






