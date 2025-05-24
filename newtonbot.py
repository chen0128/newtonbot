import requests
from fake_useragent import UserAgent
from tabulate import tabulate

# 读取 session token
with open('data.txt', 'r') as f:
    session_tokens = [line.strip() for line in f if line.strip()]

# 读取代理列表
with open('proxy.txt', 'r') as f:
    proxies_list = [line.strip() for line in f]

ua = UserAgent()
post_url = 'https://www.magicnewton.com/portal/api/userQuests'
quest_id = "f56c760b-2186-40cb-9cbc-3af4a3dc20e2"

def get_desktop_user_agent():
    while True:
        ua_str = ua.chrome
        if "Windows" in ua_str or "Macintosh" in ua_str:
            return ua_str

def get_proxy_ip(proxy_addr):
    try:
        response = requests.get(
            "https://httpbin.org/ip",
            proxies={"http": proxy_addr, "https": proxy_addr},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("origin", "未知IP")
        else:
            return f"状态码: {response.status_code}"
    except Exception:
        return "连接失败"

def get_total_credits(session_token, user_agent_str, proxies=None):
    headers = {
        'User-Agent': user_agent_str,
        'Accept': 'application/json'
    }
    cookies = {
        '__Secure-next-auth.session-token': session_token
    }
    try:
        response = requests.get(
            'https://www.magicnewton.com/portal/api/userQuests',
            headers=headers,
            cookies=cookies,
            proxies=proxies,
            timeout=15
        )
        if response.status_code == 200:
            total = sum(q.get('credits', 0) for q in response.json().get('data', []))
            return total
        else:
            return None
    except Exception:
        return None

results = []

for idx, session_token in enumerate(session_tokens, 1):
    print(f"[{idx}] 正在处理 Session Token: {session_token[:8]}...")

    proxy_addr = proxies_list[idx - 1] if idx - 1 < len(proxies_list) else ''
    proxies = None
    ip_info = "直连"

    if proxy_addr:
        proxies = {
            "http": proxy_addr,
            "https": proxy_addr,
        }
        ip_info = get_proxy_ip(proxy_addr)
    else:
        ip_info = get_proxy_ip(None)

    print(f"[{idx}] 使用出口 IP: {ip_info}")

    user_agent_str = get_desktop_user_agent()

    cookies = {
        '__Secure-next-auth.session-token': session_token
    }

    headers = {
        'User-Agent': user_agent_str,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    post_data = {
        "questId": quest_id,
        "metadata": {}
    }

    try:
        post_response = requests.post(
            post_url,
            headers=headers,
            cookies=cookies,
            json=post_data,
            proxies=proxies,
            timeout=15
        )
        result = post_response.json()
    except Exception as e:
        print(f"[{idx}] ❌ 请求失败，错误：{str(e)}")
        results.append([idx, session_token[:8] + "...", "请求失败或非JSON", "-", "-", ip_info])
        continue

    message = result.get('message', '')
    if post_response.status_code == 200 or message == "Quest already completed.":
        credits = result.get('data', {}).get('credits', '-')
        total_credits = get_total_credits(session_token, user_agent_str, proxies=proxies)
        total_credits_display = total_credits if total_credits is not None else "-"
        print(f"[{idx}] ✅ 任务完成: {message}，获得积分: {credits}，总积分: {total_credits_display}")
        results.append([idx, session_token[:8] + "...", message, credits, total_credits_display, ip_info])
    else:
        print(f"[{idx}] ⚠️ 任务失败，状态码: {post_response.status_code}")
        results.append([idx, session_token[:8] + "...", f"任务失败({post_response.status_code})", "-", "-", ip_info])

# 打印整张表格
headers = ["序号", "Session Token (前8位)", "任务消息", "本次积分", "总积分", "出口 IP"]
print("\n📋 全部任务完成，结果如下：\n")
print(tabulate(results, headers=headers, tablefmt="grid", stralign="center"))
