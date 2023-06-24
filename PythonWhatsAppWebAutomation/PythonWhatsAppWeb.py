# Whatsapp Web based Library - Web QR Code authentication should be done once to test.
import pywhatkit

def send_whatsapp_message_now(mobile_number: str, textmsg: str):
    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no = mobile_number, 
            message = textmsg,
            tab_close = True
        )
        print("Message Successfully Sent!")
    except Exception as e:
        print(str(e))

def send_whatsapp_message_scheduled(mobile_number: str, textmsg: str, hour: int, minute: int):
    try:
        pywhatkit.sendwhatmsg(
            phone_no = mobile_number, 
            message = textmsg,
            time_hour = hour,
            time_min = minute,
            tab_close = True
        )
        print("Message Successfully Sent!")
    except Exception as e:
        print(str(e))

def send_whatsapp_message_togroup_now(group_reference: str, textmsg: str):
    try:
        pywhatkit.sendwhatmsg_to_group_instantly(
            group_id = group_reference, 
            message = textmsg,
            tab_close = True
        )
        print("Message Successfully Sent!")
    except Exception as e:
        print(str(e))

def send_whatsapp_message_togroup_scheduled(group_reference: str, textmsg: str, hour: int, minute: int):
    try:
        pywhatkit.sendwhatmsg_to_group(
            group_id = group_reference, 
            message = textmsg,
            time_hour = hour,
            time_min = minute,
            tab_close = True
        )
        print("Message Successfully Sent!")
    except Exception as e:
        print(str(e))

def send_whatsapp_image(group_reference: str, image_path: str, textmsg: str):
    try:
        pywhatkit.sendwhats_image(
            receiver = group_reference,
            img_path =  image_path,
            tab_close = True
        )
        print("Image Successfully Sent!")
    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    # For 1 Person Instant Message
    send_whatsapp_message_now(mobile_number="+91xxxxxxxxxx",textmsg="Test Instant Message!")
    # For 1 Person Scheduled Message
    send_whatsapp_message_scheduled(mobile_number="+91xxxxxxxxxx",textmsg="Test Scheduled Message!",hour=13,minute=32)
    # For Group Instant Message - Get Group ID / Reference from Group Invite Link
    send_whatsapp_message_togroup_now(group_reference="LUUFCb6nqum1TXjRVumX5b",textmsg="Welcome to our Group!")
    # For Group Scheduled Message
    send_whatsapp_message_togroup_scheduled(group_reference="LUUFCb6nqum1TXjRVumX5b",textmsg="Welcome to our Group Scheduled Message!",hour=14,minute=12)
    # For Image
    send_whatsapp_image(group_reference="LUUFCb6nqum1TXjRVumX5b", image_path="C:\\TestAny.jpeg", textmsg="Welcome to Image Test!")
