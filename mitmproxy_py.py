from mitmproxy import ctx, http
import mitmproxy.http
import re
import base64

class Counter:
    def __init__(self):
        # 1x1像素的透明PNG图片的base64编码
        self.transparent_pixel = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )

        # 篡改目标URL
        self.target_urls = {
            "https://web.sanguosha.com/x/pc/res/assets/animate/pray/SF_eff_qifu_gonggao1.png": "replace",
            "https://web.sanguosha.com/x/pc/res/assets/animate/pray/SF_eff_qifu_gonggao2.png": "replace",
            "https://web.sanguosha.com/x/pc/res/assets/animate/pray/SF_eff_qifu_gonggao3.png": "replace"
        }

        # 正则表达式匹配包含URL(分别是动态皮肤，语音文件，静态皮肤)的请求
        self.resource_pattern = re.compile(
            r'https:\/\/web\.sanguosha\.com\/x\/pc\/res\/assets\/runtime\/(?:general\/big\/dynamic\/|voice\/skin\/|general\/big\/static\/)'
        )

    def request(self, flow: mitmproxy.http.HTTPFlow):
        try:

            if (flow.request.host == 'web.sanguosha.com'
                    and re.search(self.resource_pattern, flow.request.url)):
                print(flow.request.url)

            if flow.request.pretty_url in self.target_urls:
                action = self.target_urls[flow.request.pretty_url]

                if action == "replace":
                    # 返回1x1透明图片
                    flow.response = http.Response.make(
                        200,
                        self.transparent_pixel,
                        {"Content-Type": "image/png"}
                    )
        except:
            pass


addons = [Counter()]
