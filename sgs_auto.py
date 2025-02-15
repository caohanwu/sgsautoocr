import pyautogui
import time
import os
from PIL import Image, ImageEnhance
import paddleocr
import io
import numpy as np
import re
import random
import logging

class SanGuoShaAuto:
    def __init__(self, use_angle_cls=False, lang="ch", use_gpu=False) -> None:
        # 设置环境变量，控制PaddleOCR的日志输出等级为2，屏蔽INFO和WARNING
        os.environ["FLAGS_minloglevel"] = "2"
        logging.getLogger("ppocr").setLevel(logging.ERROR)
        # 初始化OCR引擎
        self.ocr = paddleocr.PaddleOCR(use_angle_cls=use_angle_cls, lang=lang, use_gpu=use_gpu)
        # pyautogui，开启故障安全功能
        pyautogui.FAILSAFE = True
        # 设置各个目录路径
        # 分别为低置信度（方便训练模型），当前位置，皮肤动态，声音图片，列表图片
        self.low_confidence_directory = r'G:\cao\sanguosha\autoSanGuoSha\sgs_pic\lowconfidence'
        self.current_directory = r'G:\cao\sanguosha\autoSanGuoSha\sgs_pic\location'
        self.skins_dynamic_directorys = r'G:\cao\sanguosha\autoSanGuoSha\sgs_pic\skins_dynamic'
        self.sound_pic = r'G:\cao\sanguosha\autoSanGuoSha\sgs_pic\sound.png'
        self.list_image = r'G:\cao\sanguosha\autoSanGuoSha\sgs_pic\img.png'
        self.dynamics_directorys = r'G:\cao\sanguosha\autoSanGuoSha\sgs_pic\skins_dynamic'

        # 初始化全局变量
        self.lists_location = None
        self.lists_num = None
        self.list_name = None
        self.skin_name = None

    # 在此处添加识别或者自动点击函数来处理游戏的自动化任务
    def locate_image_onscreen(self,image_path:str, confidence:float, region:tuple, all_mode: bool = False) -> list[list[float]]:
        """
        判断图片是否在屏幕上,最多判断三次
        :args:
            image_path: 图片路径
            confidence: 置信度
            region: 识别区域
            all_mode: 是否启用查找所有匹配的模式,查找多个，查找单个
        :returns
            返回中心坐标列表|空列表
        """
        max_retries = 3
        retry_count = 0
        coordinates = []
        while retry_count < max_retries:
            try:
                if all_mode:
                    locations = list(pyautogui.locateAllOnScreen(image_path, confidence =confidence, region =region, grayscale=True))
                else:
                    locations = [list(pyautogui.locateOnScreen(image_path, confidence=confidence, region=region))]

                if locations:
                    #后续需要点击，所以坐标需要改为中心点坐标
                    for i,loc in enumerate(locations):
                        s_x = loc[0] + loc[2] / 2
                        s_y = loc[1] + loc[3] / 2
                        if not coordinates or abs(s_x - coordinates[-1][0]) > 30 or abs(s_y - coordinates[-1][1]) > 30:
                            coordinates.append([s_x, s_y])
                    #print(f"识别到 {len(coordinates)} 个位置,分别为{coordinates}")
                    return coordinates
                else:
                    print(f"未找到图片，尝试第 {retry_count + 1} 次")
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(1)  # 等待1秒后重试
                    else:
                        print(f"达到最大重试次数，未找到图片{image_path}")
                        return []
            except pyautogui.ImageNotFoundException:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(0.5)  # 等待1秒后重试
                else:
                    print(f"达到最大重试次数，未找到图片{image_path}")
                    return []
            except pyautogui.FailSafeException:
                print("触发了故障安全功能，程序已停止。")
            except Exception as e:
                print(f"非预期错误！{str(e)}")
                print(f"未找到图片，尝试第 {retry_count + 1} 次")
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(1)  # 等待1秒后重试
                else:
                    print(f"非预期错误！达到最大重试次数，未找到图片{image_path}")

    def capture_and_ocr(self,x, y, width, height, image_path):
        """
        截取屏幕指定位置的图像，调整对比度，转换为NumPy数组，并进行OCR识别；
        保存低置信度的图片到固定文件中。最多尝试3次，只要识别到内容就返回。
        Args:
            x, y, width, height: 截图区域的坐标和尺寸
            image_path：保存低置信度的图片的路径
        Returns:
            返回识别的所有文本和置信度的列表，如果3次都未识别到则返回空列表
        """
        for _ in range(3):  # 最多尝试3次
            recognized_items = []
            try:
                screenshot = pyautogui.screenshot(region=(int(x), int(y), int(width), int(height)))
                # 将截图保存到内存中,转换为NumPy数组
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)
                img = Image.open(img_byte_arr)
                img_np = np.array(img)

                # OCR识别
                result = self.ocr.ocr(img_np)
                if result:
                    for item in result:
                        if item and len(item) > 0:
                            for line in item:
                                if len(line) > 1:
                                    text, confidence = line[1]
                                    recognized_items.append({"text": text, "confidence": confidence})

                                    # 如果置信度低于0.95，则保存图像
                                    if confidence < 0.95:
                                        random_num = random.randint(0, 99999)
                                        img_to_save = Image.fromarray(img_np)
                                        img_to_save.save(f"{image_path}/{confidence}_{random_num}.png")

                if recognized_items:
                    return recognized_items

            except pyautogui.FailSafeException:
                print("触发了故障安全功能，程序已停止。")
            except Exception as e:
                print(f"OCR 识别失败: {str(e)}")
                return []

        return []  # 如果三次都未识别到，返回空列表

    def current_location(self, current_image,next_image=None) -> int:
        """
        获取当前所处的位置，根据右上角的返回标签+其名称判断当前所在的位置。
        根据情况是否进行点击，如果点击后还要判断是否进入了目标页面。

        Args:
            current_image (str): 传入识别图片名称。
            next_image (str, optional): 点击后要继续判断的图片名称。

        Returns:
            int: 存在返回1，若点击后未进入指定页面则返回0。
        """
        # 设置不同图片的置信度和识别区域
        image_configs = {
            'list1': {'confidence': 0.9, 'region': (300, 230, 350, 80)},
            'hero2': {'confidence': 0.85, 'region': (300, 230, 350, 80)},
            'skin3': {'confidence': 0.8, 'region': (300, 230, 350, 80)},
            'sound4': {'confidence': 0.75, 'region': (1900, 340, 160, 790)},
            'skin5': {'confidence': 0.8, 'region': (2070, 1085, 130, 150)},
            'xq6': {'confidence': 0.8, 'region': (2065, 710, 160, 100)},
            'back': {'confidence': 0.9, 'region': (300, 230, 350, 80)}
        }

        # 获取当前图片的配置
        config = image_configs.get(current_image)
        full_path = os.path.join(self.current_directory, current_image + ".png")
        locations = self.locate_image_onscreen(full_path, config['confidence'], region=config['region'])

        if locations:  # 如果找到了坐标
            if next_image:
                # 检查点击后页面是否变成了目标页面
                pyautogui.click(locations[0][0], locations[0][1])  # 执行点击
                pyautogui.sleep(3)
                while True:
                    next_config = image_configs.get(next_image)
                    next_path = os.path.join(self.current_directory, next_image + ".png")
                    next_locations = self.locate_image_onscreen(next_path, next_config['confidence'],
                                                                region=next_config['region'])

                    # 如果找到了指定的目标页面
                    if next_locations:
                        return 1
                    else:
                        input(f"请将页面切换到 {next_image} 页面，按任意键继续...")

            return 1  # 找到了当前页面，且没有设置next_image
        return 0  # 如果未找到配置或坐标，返回0

    def recognize_lists_ocr(self) -> list[list[float]]:
        """识别右侧的列表栏数量和坐标，(循环三次*3，使得识别的数量超过11次）并对全局变量赋值"""
        while True:
            if self.current_location('list1') == 1:
                print("列表页面，查看列表的数量及其坐标..........")
                for _ in range(3):
                    list_results = self.locate_image_onscreen(self.list_image, 0.25, (2125, 390, 60, 815), True)
                    if list_results and len(list_results) > 11:
                        return list_results
                input("列表数量识别失败，请检查是否切换到列表页！")
            else:
                input("请将页面切换到列表页，然后按任意键继续...")

    def recognize_list_name(self) -> tuple:
        """查找固定区域的位置获得lists的名称信息，re解析具体的数字及其列表名称
        Returns:
            返回列表名称和列表中的武将数量
        """
        while True:
            if self.current_location('list1') == 1:
                print("列表页面，定位列表中央名称及其数量..........")
                list_ocr_results = self.capture_and_ocr(1110, 390, 390, 65, self.low_confidence_directory)
                if list_ocr_results and len(list_ocr_results) > 0:
                    # 只取第一个识别结果
                    first_result = list_ocr_results[0]
                    list_ocr_text = first_result['text']
                    list_ocr_confidence = first_result['confidence']

                    if list_ocr_confidence > 0.8 and list_ocr_text:
                        list_names = re.search(r'.+(?=\d+\/)', list_ocr_text)
                        list_num = re.search(r'(?<=\/).+', list_ocr_text)
                        if list_names and list_num:
                            list_names = list_names.group(0).strip()
                            list_num = int(list_num.group(0).strip())
                            print(f"当前列表名称：{list_names}，列表数量：{list_num}")
                            return list_names, list_num
            else:
                input("请将页面切换到列表页，然后按任意键继续...")

    def recognize_skin_name(self) -> tuple:
        """由声音图标的位置获得皮肤名称信息
        先定位出声音图标的位置，通过声音图标的位置获取到皮肤名称的位置
        声音图标的位置(1130, 360, 300, 60)
        皮肤图标的位置相对于声音图标的偏移量(310, 70/3) （数值测试过）
        Returns:
            返回皮肤名称及其置信度
        """
        while True:
            if self.current_location('skin3') == 1:
                print("皮肤页面，定位皮肤名称中..........")
                sound_pic_location = self.locate_image_onscreen(self.sound_pic, 0.8, (1130, 360, 300, 60))
                if sound_pic_location:
                    x, y = sound_pic_location[0][0], sound_pic_location[0][1]
                    # 截取并识别
                    skin_ocr = self.capture_and_ocr((x - 310), (y - 70 // 3), 310, 70, self.low_confidence_directory)
                    if skin_ocr:
                        skin_name = skin_ocr[0]['text']
                        skin_confidence = skin_ocr[0]['confidence']
                        return skin_name, skin_confidence

            else:
                input("请将页面切换到皮肤页，然后按任意键继续...")

    def recognize_skin_dynamics(self):
        """
        识别皮肤是否有动态皮肤，攻击动画，双形态，视频;并进行点击

        :return: 列表 [动态皮肤, 攻击动画, 双形态, 视频]
        每个元素为整数，1表示有，0表示没有
        """
        recognize_dynamics = [0, 0, 0, 0]  # 分别代表 [动态皮肤, 攻击动画, 双形态, 视频]

        # 为每个特征定义不同的识别区域
        recognition_regions = {
            'dynamics': (1455, 1025, 450, 125),
            'attack_animation': (847, 955, 150, 180),
            'dual_form': (1275, 1035, 190, 100),
            'video': (847, 955, 136, 180),
        }

        # 添加置信度
        features = [
            ('dynamics.png', 0, 'dynamics', 0.7),  # 动态皮肤
            ('attack_animation.png', 1, 'attack_animation', 0.7),  # 攻击动画
            ('dual_form.png', 2, 'dual_form', 0.8),  # 双形态
            ('video.png', 3, 'video', 0.8),  # 视频
        ]

        # 首先检测动态皮肤
        if self.current_location('skin3') == 1:
            dynamic_feature = features[0]
            image_path = os.path.join(self.dynamics_directorys, dynamic_feature[0])
            region = recognition_regions.get(dynamic_feature[2], (0, 0, 1920, 1080))
            print("检测动态皮肤中......")
            dynamics_location = self.locate_image_onscreen(image_path, dynamic_feature[3], region)
            if dynamics_location:
                recognize_dynamics[0] = 1
                pyautogui.click(dynamics_location[0][0], dynamics_location[0][1])
                pyautogui.sleep(5)

                # 检测攻击动画
                attack_feature = features[1]
                image_path = os.path.join(self.dynamics_directorys, attack_feature[0])
                region = recognition_regions.get(attack_feature[2], (0, 0, 1920, 1080))
                print("检测攻击动画中......")
                attack_location = self.locate_image_onscreen(image_path, attack_feature[3], region)
                if attack_location:
                    recognize_dynamics[1] = 1
                    pyautogui.click(attack_location[0][0], attack_location[0][1])
                    pyautogui.sleep(2)

                    # 检测双形态
                    dual_form_feature = features[2]
                    image_path = os.path.join(self.dynamics_directorys, dual_form_feature[0])
                    region = recognition_regions.get(dual_form_feature[2], (0, 0, 1920, 1080))
                    print("检测双形态中......")
                    dual_form_location = self.locate_image_onscreen(image_path, dual_form_feature[3], region)
                    if dual_form_location:
                        recognize_dynamics[2] = 1

                    # 检测视频
                    video_feature = features[3]
                    image_path = os.path.join(self.dynamics_directorys, video_feature[0])
                    region = recognition_regions.get(video_feature[2], (0, 0, 1920, 1080))
                    print("检测视频中......")
                    video_location = self.locate_image_onscreen(image_path, video_feature[3], region)
                    if video_location:
                        recognize_dynamics[3] = 1

            return recognize_dynamics
        else:
            input("请将页面切换到皮肤页，然后按任意键继续...")

    def recognize_dialogue(self):
        """识别固定区域中台词的文字，并返回识别结果；
        根据声音图标的位置判断选择区域位置；
        同时点击两次声音图标，使得代理能够获取到请求链接
        Returns:
            返回一个列表，每个元素为一个字典，包含武将名称和置信度
        """
        while True:
            if self.current_location('sound4') == 1:
                print(".........识别台词中...........")
                recognized_word = []
                sound_pic_locations = self.locate_image_onscreen(self.sound_pic, 0.75, (1900, 340, 160, 790), True)
                if sound_pic_locations:
                    for index, location in enumerate(sound_pic_locations):
                        x, y = location[0], location[1]
                        # 计算 height(因为台词的字数有可能会换行，所以需要根据上下音符的间隔计算高度,进而调整识别框的区域)
                        if index < len(sound_pic_locations) - 1:
                            next_y = sound_pic_locations[index + 1][1]
                            height = abs(next_y - y)
                        else:
                            height = 180
                        # 根据位置计算选择台词框的位置
                        width = 580
                        left_start = (x - width)
                        top_start = (y - 30)  #获取到坐标是中心点坐标，所以需要向上移动30像素
                        # 截取并识别
                        ocr_results = self.capture_and_ocr(left_start, top_start, width, height, self.low_confidence_directory)

                        if ocr_results:
                            for item in ocr_results:
                                print(
                                    f"位置 {index + 1} 坐标{(x, y)} 高度{height} 识别结果: {item['text']}, 置信度: {item['confidence']}")

                            # 点击两次声音图标,因为返回的是识别的起始点，所以要在x，y的基础上加入宽高的一半，使得点击中央位置
                            pyautogui.click(x,y,2,0.25)
                            pyautogui.sleep(2)
                            recognized_word.append(ocr_results)

                return recognized_word
            else:
                input("请将页面切换到台词页，然后按任意键继续...")

    def check_for_die(self,result):
        """
        检查台词里面是否有阵亡二字，如果有则不用滚动和去重
        :param result: 传入识别台词的结果
        :return:
        """
        for sublist in result:
            for item in sublist:
                if item['text'] == '阵亡':
                    if len(sublist) > 1:        # 防止仅仅存在阵亡二字，但是没阵亡台词
                        return True
        return False

    def remove_duplicates(self,results):
        """
        去重结果，因为台词太多，一个页面显示不全，需要下滑，但是有些声音图标会被检查两次；所以要去重
        第二次的结果会插入到第一次的结果中；
        从后往前查找重复，从前往后排序台词
        :param results:
        :return:
        """
        # 创建一个空集合用于存储已经见过的文本组合
        seen = set()
        # 创建一个新的结果列表用于存储无重复的数据
        unique_results = []

        # 从后向前遍历原始结果列表
        for sublist in reversed(results):
            # 取出子列表中的文本
            if sublist:
                text_pair = sublist[0]['text']
                # 如果这对文本还没有出现过，则从前往后添加到unique_results中，并将文本加入seen集合
                if text_pair not in seen:
                    seen.add(text_pair)
                    # 由于我们是从后向前遍历，所以需要在unique_results的前面插入元素
                    unique_results.insert(0, sublist)

        return unique_results

    def recognize_all_dialogue(self):
        """
        综合识别对话函数，检测死亡函数，去除重复对话函数，返回真正的对话文本
        :return:
        """
        all_dialogue = self.recognize_dialogue()
        if not self.check_for_die(all_dialogue):
            pyautogui.moveTo(2000,750)
            pyautogui.scroll(-1000)
            pyautogui.sleep(2)
            second_dialogue = self.recognize_dialogue()
            all_dialogue.extend(second_dialogue)
            # 若台词栏滚动过，切换皮肤的时候，后续皮肤的台词维持在滚动后的状态，所以需要反向滚动一次，使其回到原来的位置
            pyautogui.moveTo(2000, 750)
            pyautogui.scroll(1000)
            # 对all_dialogue进行去重处理
            all_dialogue = self.remove_duplicates(all_dialogue)

        return all_dialogue
# # 创建类实例
# sgs = SanGuoShaAuto()
#
# s1 = sgs.recognize_all_dialogue()
# print(s1)


