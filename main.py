import os
import webview

class API:

    def test_conection(self):
        return {
            "ok": True,
            "Message": 'Conexión Python > JavaScript Exitosa!'
        }

def getRoute_Front():
    dir_base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(dir_base, 'Frontend', 'index.html')

if __name__ == "__main__":

    api = API()

    route_html = getRoute_Front()

    window = webview.create_window(
        "Conversor PDF",
        route_html,
        js_api=api,
        width=1000,
        height=800,
        min_size=(800,600)
    )

    webview.start()


