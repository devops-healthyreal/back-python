import requests
from surprise import SVD, Dataset, Reader, accuracy
from surprise.model_selection import train_test_split
import pandas as pd
from basic_fuc import db_conn, db_disconn, query_select
from flask_restful import Resource
from flask import request
import os

class recommendMate(Resource):
    def post(self):
        ID = request.json.get('ID')  # 클라이언트가 보낸 ID 받기
        n_top = 6

        ratings = self.dbconnect()
        reader = Reader(rating_scale=(0.5, 5))
        data = Dataset.load_from_df(ratings, reader)
        train, test = train_test_split(data, test_size=0.1, shuffle=False)

        model = SVD()
        model.fit(train)

        top_mates = self.recommend_mates(ID, n_top, data, model)
        print(top_mates)
        return {'recommendations': top_mates}

    def dbconnect(self):
        # 데이터베이스에 연결
        connection = db_conn()
        # 쿼리 실행
        query = 'SELECT * FROM MATE_LIST'
        ratings = query_select(connection, query)
        # 데이터베이스 연결 종료
        db_disconn(connection)
        # 결과를 데이터프레임으로 변환
        ratings_df = pd.DataFrame({
            "ID": [rating[2] for rating in ratings],
            "MATE_ID": [rating[3] for rating in ratings],
            "FAVORABLE_RATING": [rating[4] for rating in ratings],
        })
        return ratings_df

    def getUserMateProfile(self, id):
        base_url = os.getenv("AUTH_SERVER_URL", "http://localhost:4000").rstrip("/")
        url = f"{base_url}/comm/mate"
        try:
            resp = requests.get(url, params={"id": id}, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[getUserMateProfile] Request failed: {e}")
            return []

    def recommend_mates(self, ID, n_top, data, model):
        mate_ids = data.df['MATE_ID'].unique()
        rated_mates = data.df[data.df['ID'] == ID]['MATE_ID']
        unrated_mates = [mate for mate in mate_ids if mate not in rated_mates and mate != ID]

        predictions = [model.predict(ID, mate_id) for mate_id in unrated_mates]
        predictions.sort(key=lambda pred: pred.est, reverse=True)

        # 자신이 제외될 경우, 추가로 한 명 더 추천
        if len(predictions) < n_top:
            n_top = len(predictions)
        elif ID in unrated_mates:
            n_top += 1

        top_predictions = predictions[:n_top]

        returnVal = []
        for pred in top_predictions:
            tempProfile = self.getUserMateProfile(pred.iid)[0]
            print(tempProfile)
            returnVal.append({'mate_id': pred.iid,
                              'estimated_rating': pred.est,
                              'name': tempProfile['name'],
                              'fnum': tempProfile['fnum'],
                              'mnum': tempProfile['mnum'],
                              'snum': tempProfile['snum'],
                              'profilePath':tempProfile['profilePath']})
        return returnVal


