import urllib3
import postkid

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    postkid.PostKid().start()
except Exception as error:
    print("Error:", error)