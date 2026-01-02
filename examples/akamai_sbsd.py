from salamoonder import Salamoonder

client = Salamoonder("YOUR_KEY_HERE")

URL = "https://bol.com/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
PROXY = "http://user:pass@ip:port"

extract_data = client.akamai_sbsd.fetch_and_extract(
    website_url=URL,
    user_agent=USER_AGENT,
    proxy=PROXY
)

if extract_data:
    base_url = extract_data['base_url']
    cookie = extract_data['cookie_value']
    sbsd_url = extract_data['sbsd_url']
    script_data = extract_data['script_data']

    task_id = client.task.createTask(
        task_type="AkamaiSBSDSolver",
        url=base_url,
        cookie=cookie,
        sbsd_url=sbsd_url,
        script=script_data
    )
    
    result = client.task.getTaskResult(task_id)

    cookie = client.akamai_sbsd.post_sbsd(
        sbsd_payload=result['payload'],
        post_url=sbsd_url,
        user_agent=result['user-agent'],
        website_url=URL,
        proxy=PROXY
    )

    if cookie:
        print(cookie)
