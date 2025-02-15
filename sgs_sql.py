import pymysql.cursors


class DBHelper:
    def __init__(self, host='localhost', user='root', password='root', database='sanguosha', charset='utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection = None
        self.connect()  # 初始化时自动连接数据库

    def connect(self):
        """初始化数据库连接"""
        if self.connection is None or not self.connection.open:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor
            )

    def insert_data(self, table_name, data,is_insert=False):
        """
        插入数据到指定表中
        :param is_insert: 默认不传输
        :param table_name: 表名
        :param data: 字典格式，键为字段名，值为插入的值
        """
        # 获取字段名和值
        if is_insert:
            columns = ', '.join(data.keys())
            values = ', '.join(['%s'] * len(data))
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

            try:
                with self.connection.cursor() as cursor:
                    print(cursor.mogrify(sql, list(data.values())))
                    cursor.execute(sql, list(data.values()))
                self.commit()  # 提交事务
            except Exception as e:
                print(f"插入数据时出错: {e}")
                self.connection.rollback()  # 回滚事务

    def execute_query(self, sql, params=None):
        """执行SQL查询，返回列表字典[{'HeroID': 1}, {'HeroID': 2}, {'HeroID': 3}]"""
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
        return result

    def check_data(self,mode,column_name:list,table_name):
        """
        返回column_name的值
        result = check_data(['name', 'age'], 'users', 'list')

        :param column_name:列名列表，多个列名用逗号分隔
        :param table_name: 表名
        :param mode: 根据模式返回 0代表个数，1单列返回单个列表的所有值，2两列返回单个列表的两列值
        """
        sql = f"SELECT {', '.join(column_name)} FROM {table_name}"
        result = self.execute_query(sql)
        if mode == 0:
            return len(result)
        elif mode == 1:
            result = [x[column_name[0]] for x in result]
        elif mode == 2:
            result = [(x[column_name[0]], x[column_name[1]]) for x in result]
        return result

    def check_id(self,list_data:tuple) -> dict:
        """传入识别的list_data（list_data[0]是列表名，list_data[1]是列表中英雄数量）
        通过查询来判断当前列表处于那种模式,返回listid的id和heroid的列表和skinid的最大id

        1.新增的列表，list_data[0]不在ListName中，新增listid，heroid，skinid
        2.新增的英雄 ，list_data[0]在ListName中，但是list_data[1]和heros表中对应列表名的heroid数量不相等，新增heroid，skinid
        3.新增的皮肤，list_data[0]在ListName中，list_data[1]和heros表中对应列表名的heroid数量相等，只需要新增skinid

        """
        sql_list_data = self.check_data(2,['ListName','ListNum'],'lists')
        sql_list_data_name = [x[0] for x in sql_list_data]

        if list_data[0] not in sql_list_data_name:
            print(f"{list_data}新增列表，全部新增")
            listid = len(sql_list_data) + 1
            heroid = self.check_data(0,['HeroID'],'heros') + 1
            heroid = [heroid + i for i in range(list_data[1])]
            skinid = self.check_data(0,['SkinID'],'skins') + 1
            result = {'listid':listid,'heroid':heroid,'skinid':skinid,'is_add_list':True,'is_add_hero':True}
            return result
        else:
            list_sql = f"select ListID from lists where ListName = '{list_data[0]}'"
            sql_list_data = self.execute_query(list_sql)
            sql_list_data = [x['ListID'] for x in sql_list_data][0]
            hero_sql = f"select HeroID from heros where ListID = {sql_list_data}"
            sql_hero_data = self.execute_query(hero_sql)
            sql_hero_data = [x['HeroID'] for x in sql_hero_data]
            sql_hero_data_num = len(sql_hero_data)

            if list_data[1] == sql_hero_data_num:
                print(f"{list_data}仅仅判断是否新增皮肤")
                listid = sql_list_data
                heroid = sql_hero_data
                skinid = self.check_data(0, ['SkinID'], 'skins') + 1
                result = {'listid': listid, 'heroid': heroid, 'skinid': skinid,'is_add_list':False,'is_add_hero':False}
                return result
            else:
                print(f"{list_data}新增英雄")
                listid = sql_list_data
                # 数据库中<<对应的列表中英雄的数量和识别的数量之差>+<最大的heroid +1 为起始heroid>>为新增的heroid列表组合,+数据库中已有的heroid
                # 新增的起始heroid
                new_heroid = self.check_data(0, ['HeroID'], 'heros') + 1
                # 新增的heroid数量
                new_heroid_num = list_data[1]-sql_hero_data_num
                new_heroid = [new_heroid + i for i in range(new_heroid_num)]
                hero_id = sql_hero_data + new_heroid
                skin_id = self.check_data(0, ['SkinID'], 'skins') + 1
                result = {'listid': listid, 'heroid': hero_id, 'skinid': skin_id,'is_add_list':False,'is_add_hero':True}
                return result




    def commit(self):
        """提交事务"""
        self.connection.commit()

    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()
            self.connection = None

    def __enter__(self):
        """支持上下文管理"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """在上下文结束时关闭连接"""
        self.close()




# 使用示例
if __name__ == "__main__":
    # 模块加载时自动初始化数据库连接
    db_helper = DBHelper()
    list_data = ('主',10)
    s1 = db_helper.check_id(list_data)
    print(s1)
    listid, hero_id, skin_id, is_add_list, is_add_hero = (s1[key] for key in
                                                          ['listid', 'heroid', 'skinid', 'is_add_list', 'is_add_hero'])
    print(listid, hero_id, skin_id, is_add_list, is_add_hero)
    sql_skin_data = db_helper.check_data(1, ['SkinName'], 'skins')
    print(sql_skin_data)
    if '经典形象*刘备' in sql_skin_data:
        print('存在')


    # 示例1: 插入数据到heros表
    # data_to_insert = {
    #     'ListID': '1',
    #     'ListName': 'zhao',
    #     'ListNum': '1'
    # }
    # db_helper.insert_data('lists', data_to_insert)

    # # 示例2: 查询heros表结构
    # sql = """SELECT column_name, data_type, is_nullable, column_key
    #          FROM INFORMATION_SCHEMA.COLUMNS
    #          WHERE table_schema = %s AND table_name = %s"""
    # result = db_helper.execute_query(sql, ('sanguosha', 'heros'))
    # print(f"查询结果: {result}")
    # # lists_check_sql = """SELECT ListName FROM lists"""
    # # heros_check_sql = """SELECT HeroID FROM heros"""
    # # skins_check_sql = """SELECT SkinName FROM skins"""
    # # result = db_helper.execute_query(lists_check_sql)
    # # result1 = db_helper.execute_query(heros_check_sql)
    # # result2 = db_helper.execute_query(skins_check_sql)
    # # print(result,result1,result2)
    # s1 = db_helper.check_data(2,['ListName','ListNum'],'lists')
    # s2 = db_helper.check_data(1,['HeroID'], 'heros')
    # s3 = db_helper.check_data(1,['SkinName'], 'skins')
    # print(s1,s2,s3)
    # # print(len(s3))
    # # print(type(s1))
    # # s4 = [(x['ListName'],x['ListNum']) for x in s1]
    # # s5 = [x['ListName'] for x in s1]
    # # print(s3)
    # # sql_skin_data = [x['SkinName'] for x in s3]
    # # print(sql_skin_data)
    # # if ('主', 3) in s4:
    # #     print('ok')
    # # if '主' in s5:
    # #     print('ok')
    # #     print(s5)
    # # print(len(s3))
    # # print(db_helper.check_id('主', 'ListID', 'ListName', 'lists'))
    # # print(db_helper.check_id('11', 'ListNum', 'ListID', 'lists'))
    # # print(db_helper.check_id('11', 'HeroID', 'ListID', 'heros'))
    # # print(db_helper.check_id('3', 'SkinID', 'HeroID', 'skins'))

