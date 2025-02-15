from queue_main2 import MitmCommandRunner
from multiprocessing import Process, Queue,Event
from sgs_auto import SanGuoShaAuto
from sgs_sql import DBHelper
import pyautogui
import json

if __name__ == '__main__':
    # 创建队列用于进程间通信,等待同步直到mitmproxy启动完成
    run = MitmCommandRunner()
    event = Event()
    q = Queue()
    cmd_process = Process(target=run.run_command, args=(q,event))
    cmd_process.start()
    event.wait()
    print("mitmproxy启动完成")
    print("注意浏览器清空缓存，切换到8080代理")
    print("27寸显示器2k分辨率，缩放125%")
    # 创建数据库连接
    sgs_sql = DBHelper()
    This_ALL_lists_name = []
    listid = 0
    heroid = 0
    skinid = 0

    sgs = SanGuoShaAuto()
    # 滑动右侧列表栏的次数，最多为6次，当前测试1次
    for _ in range(1):
        # 识别右侧列表栏中的列表图标个数及其位置
        lists_ocr = sgs.recognize_lists_ocr()
        for list_location in lists_ocr:
            # 点击右侧列表栏中的列表图标
            pyautogui.click(list_location[0], list_location[1])
            pyautogui.sleep(5)
            listid += 1
            # 识别列表名称及其当前列表中的数量
            list_name = sgs.recognize_list_name()
            if list_name[0] in This_ALL_lists_name:
                #旨在跳过重复列表，因为是通过滚轮轮动列表，在最下面的时候存在错误，使得列表被识别两次
                continue
            else:
                This_ALL_lists_name.append(list_name[0])
                list_num = list_name[1]
                print(f"当前列表名称：{list_name[0]},列表数量：{list_num},当前列表id：{listid}")
                # 传输列表名字及其数量到数据库list表中
                sgs_sql.insert_data('lists', {'ListID': listid, 'ListName': list_name[0], 'ListNum': list_num})
                for hero_num in range(list_num):
                    # 计算每个英雄在列表中的位置，初始位置为745，505，间隔x295，y330，每一行为5个英雄
                    # 每个列表最多三行，一个屏幕中即可点击完成，所以一个列表不需要分页
                    hero_x = 745 + (hero_num % 5) * 295
                    hero_y = 505 + (hero_num // 5) * 330
                    heroid += 1
                    sgs_sql.insert_data('heros', {'HeroID': heroid, 'ListID': listid})
                    # 执行点击英雄
                    pyautogui.click(hero_x, hero_y)
                    pyautogui.sleep(5)
                    sgs.current_location("skin5","skin3")

                    # 进入皮肤页面
                    skins_name = []
                    skin_num = 0
                    # 进行初次点击，使得皮肤位置回正（错误位置曹仁）
                    pyautogui.click(480, 400)
                    while True:

                        skin_name = sgs.recognize_skin_name()
                        if skins_name and skin_name[0] in skins_name:
                            break
                        else:
                            skins_name.append(skin_name[0])
                            print(f"当前英雄id为：{heroid},皮肤id为：{skinid}")
                            # 传输皮肤名称及其置信度到数据库skins表中
                            skinurl = run.read_queue(q)
                            skinurl = json.dumps(skinurl)
                            sgs_sql.insert_data('skins', {'SkinID': skinid, 'HeroID': heroid,'SkinName': skin_name[0],'SkinName_Confidence': skin_name[1], 'SkinUrl': skinurl})
                            # 识别皮肤动态数据
                            skin_dynamics = sgs.recognize_skin_dynamics()
                            dynamicsUrl = run.read_queue(q)
                            dynamicsUrl = json.dumps(dynamicsUrl)
                            # 传输皮肤动态数据到数据库skins_dynamic表中
                            sgs_sql.insert_data('skins_dynamics',{'SkinID': skinid, 'HeroID': heroid,'dynamics': skin_dynamics[0],'attack_animation': skin_dynamics[1],'dual_form': skin_dynamics[2],'video': skin_dynamics[3],'dynamicsUrl': dynamicsUrl})

                            # 识别对话
                            # 进入对话框
                            sgs.current_location("xq6","sound4")
                            skin_dialogue = sgs.recognize_all_dialogue()
                            skin_dialogue = json.dumps(skin_dialogue, ensure_ascii=False)
                            dialogueUrl = run.read_queue(q)
                            dialogueUrl = json.dumps(dialogueUrl)
                            # 传输对话到数据库dialogue表中
                            sgs_sql.insert_data('voices',{'SkinID': skinid, 'Url': dialogueUrl,'Dialogue': skin_dialogue})
                            # 返回皮肤页面
                            sgs.current_location("back", "skin3")
                            if skin_num < 4:
                                skin_num += 1
                            else:
                                pyautogui.moveTo(480, 1060)
                                pyautogui.scroll(-230)
                                pyautogui.sleep(1)
                            skinid += 1
                            pyautogui.click(480, 400 + skin_num * 165)
                            pyautogui.sleep(2)

                    # 返回英雄介绍页面
                    sgs.current_location("back", "hero2")
                    # 返回列表页面
                    sgs.current_location("back", "list1")



