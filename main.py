import os
import webview
import pymupdf

from Backend.Redactor import (
    convertir_pdf_a_imagenes,
    validar_archivo_pdf,
    ErrorConversorPDF
)

class API:

    def __init__(self):
        self.window = None
        self.pdf_actual = None

## Seleccion del PDF

    def selection_pdf(self):

        try:
            
            archivos = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                allow_multiple=False,
                file_types=(
                    "Archivos PDF (*.pdf)",
                    "*.pdf"
                )
            )

            # El usuario cancelo 
            if not archivos:
                return{
                    "Ok ":False,
                    "Cancelado ":True
                }

            route_pdf = archivos[0]

            # Validación dentro del backend


        

# pyrefly: ignore [parse-error]
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


