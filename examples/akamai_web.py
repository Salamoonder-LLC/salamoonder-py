from salamoonder import Salamoonder

client = Salamoonder("YOUR_KEY_HERE")

URL = "https://www.ihg.com/hotels/us/en/reservation"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
PROXY = "http://user:pass@ip:port"

# Run once to grab the required data. 
data = client.akamai.fetch_and_extract(
    website_url=URL,
    user_agent=USER_AGENT,
    proxy=PROXY
)

if data:
    current_abck = data['abck']
    current_bmsz = data['bm_sz']
    RespData = ""
    
    for i in range(3):
        task_id = client.task.createTask(
            task_type="AkamaiWebSensorSolver",
            url=data['base_url'],
            abck=current_abck,
            bmsz=current_bmsz,
            script=data['script_data'],
            sensor_url=data['akamai_url'],
            user_agent=USER_AGENT,
            count=i,
            data=RespData
        )
        
        result = client.task.getTaskResult(task_id)
        payload = result['payload']
        RespData = result['data']
        
        
        cookie = client.akamai.post_sensor(
            akamai_url=data['akamai_url'],
            sensor_data=payload,
            user_agent=USER_AGENT,
            website_url=URL,
            proxy=PROXY
        )
        
        if cookie:
            print(f"Returned cookie _abck: {cookie['abck'][:50]}...")
            current_abck = cookie['abck']
            current_bmsz = cookie.get('bm_sz', current_bmsz)
        else:
            print(f"Failed to post sensor {i + 1}")
            break
