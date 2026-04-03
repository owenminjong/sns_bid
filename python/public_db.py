# 서버 데이터베이스 접속 정보
#server_ip = 'localhost'
#server_ip = '222.236.XX.XXX'
#server_db = 'sns_bid'
#server_user = 'bidman'
#server_pass = 'tndsbdtoa20@$'

server_ip = '127.0.0.1'
server_db = 'sns_bid'
server_user = 'root'
server_pass = '0000'

def db_conn():
    mydb = pymysql.connect(host=server_ip, port=3306, db=server_db,
                           user=server_user, passwd=server_pass, charset='utf8', autocommit=True)
    return mydb.cursor()

def db_check():
    try:
        if db_cursor.connection:
            print('DB Connection')
            return
        else:
            print('DB DisConnection')
            db_cursor = db_conn(1)

    except Exception as e:
        return str(e)

def sql_result(sql):
    db_cursor.execute(sql)
    columns = db_cursor.description
    result = []
    for value in db_cursor.fetchall():
        tmp = {}
        for (index, column) in enumerate(value):
            tmp[columns[index][0]] = column
        result.append(tmp)

    mydb.commit()
    return result    
