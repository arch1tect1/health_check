import datetime,logging, psutil, socket, smtplib, psutil, settings, response, requests
from contextlib import closing
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



HOSTNAME = socket.gethostname()

logging.basicConfig(filename='resources.log', level=logging.DEBUG)
current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
warning_msg = ''


def check_cpu(warning_msg):
    cpu_info = psutil.cpu_percent(interval=1)
    if cpu_info > settings.CPU_LIMIT:
        warning_msg += f"CPU is high - {cpu_info}%\n"
        print(f"CPU is hight ({cpu_info}). Please check the server!")
    return cpu_info, warning_msg


def check_ram(warning_msg):
    memory_info = psutil.virtual_memory().percent
    if memory_info > settings.MEMORY_LIMIT:
        warning_msg += f"RAM is high - {memory_info}%\n"
        print(f"RAM is high ({memory_info}%). Please check the server")
    return memory_info, warning_msg


def check_disk_space(warning_msg):
    disk_info = psutil.disk_usage("/")
    total_disk_free = int((disk_info.free / disk_info.total) * 100)
    if total_disk_free < settings.DISK_FREE_LIMIT:
        warning_msg += f"DISK SPACE is high - Free {total_disk_free}%\n"
        print(f"DISK SPACE is high ({total_disk_free}%). Please check the server")
    return total_disk_free, warning_msg


def check_ports():
    def check_open_ports(host, ports):
        open_ports = []
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        return open_ports

    for host in settings.HOSTS:
        open_ports = check_open_ports(host, settings.PORTS)
        if open_ports:
            print(f"{host} has the following open ports: {open_ports}")
    return open_ports


def is_service_active(service_name, not_working_service):
    try:
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if process.info['name'] == service_name:
                return not_working_service
        not_working_service += f"Service: {service_name} not working\n"
        return not_working_service
    except Exception as e:
        print(f"Error while checking the service: {service_name}: {e}")
        return not_working_service


def send_email(message_text):
    server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
    server.starttls()
    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    msg = MIMEMultipart()

    msg['From'] = settings.SMTP_USERNAME
    msg['To'] = settings.SUPPORT_EMAIL
    msg['Subject'] = 'SERVER - WARNING | Usage Too High!'

    msg.attach(MIMEText(message_text, 'plain'))
    server.sendmail(settings.SMTP_USERNAME, settings.SUPPORT_EMAIL, msg.as_string())

    server.quit()


internet_status = "Internet is active"

try:
    response = requests.get('http://google.com')
    if response.status_code == 200:
        print(internet_status)
except requests.ConnectionError:
    pass

if internet_status:
    print("Internet is active")
else:
    print("Internet is not active")




cpu_info, warning_msg = check_cpu(warning_msg)
print(f"CPU usage: {cpu_info}%")

memory_info, warning_msg = check_ram(warning_msg)
print(f"RAM usage: {memory_info}%")

disk_free_info, warning_msg = check_disk_space(warning_msg)
print(f"DISK usage: {disk_free_info}%")

open_ports = check_ports()

not_working_service = ''
for service in settings.SERVICE_LIST:
    not_working_service = is_service_active(service, not_working_service)  # Замените на имя службы Apache на вашей системе

warning_msg += not_working_service

message = f" {current_datetime} | CPU: {cpu_info}% | RAM: {memory_info}% | Disk: {disk_free_info}% | Open ports: {open_ports}"

if not warning_msg:
    logging.info(message)
else:
    logging.warning(message)
    send_email(f"Server: {HOSTNAME}\n{warning_msg}\nOpen port: {open_ports}\nSeverity: Warning\nTime: {current_datetime}\nInternet_status:{internet_status}")
