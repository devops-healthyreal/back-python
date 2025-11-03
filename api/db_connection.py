import os
try:
    import MySQLdb
except ImportError:
    # MySQLdb가 없는 경우 PyMySQL 사용 (Apple Silicon 등)
    import pymysql
    pymysql.install_as_MySQLdb()
    import MySQLdb

def connect_to_db():
    # 데이터베이스 연결 설정
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    database = os.getenv("DB_NAME", "healthyreal")
    port = int(os.getenv("DB_PORT", "3306"))

    connection = MySQLdb.connect(
        user=user,
        passwd=password,
        host=host,
        db=database,
        port=port,
        charset="utf8mb4",
        use_unicode=True,
    )


    # 연결 확인
    if connection:
        print("데이터베이스에 성공적으로 연결되었습니다.")

    # 연결 반환
    return connection
