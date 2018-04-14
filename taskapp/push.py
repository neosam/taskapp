from apns import APNs, Frame, Payload
from .models import IosPush

apns = APNs(use_sandbox=True, cert_file='keys/cert.pem', key_file='keys/key.pem')

def push(user, message):
	for push in IosPush.objects.filter(user=user):
		token = push.device_id
		payload = Payload(alert=message, sound="default")
		apns.gateway_server.send_notification(token, payload)

