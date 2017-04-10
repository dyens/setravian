from config import ID_APP
from config import USER_ID
from config import LOGIN_VK
from config import PASSWORD_VK
import vk

session = vk.AuthSession(app_id=ID_APP,
                         user_login=LOGIN_VK,
                         user_password=PASSWORD_VK,
                         scope='messages')
api = vk.API(session)

def send_message(message):
    api.messages.send(user_id=USER_ID, message=message)
