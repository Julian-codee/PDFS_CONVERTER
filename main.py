from bottle import RouteError
import os
import webview
import pymupdf

from Backend.Redactor import (
    convertir_pdf_a_imagenes,
    validation_pdf,
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
            validation_pdf(route_pdf)

            # Obtenemos la informacion del documento y su conteo de paginas
            document = pymupdf.open(route_pdf)
            total_pages = document.page_count

            document.close()

            size_bytes = os.path.getsize(route_pdf)
            name = os.path.basename(route_pdf)

            # Hacemos el guardado del pdf seleccionado

            self.pdf_actual = route_pdf

            return{
                "ok": True,
                "name": name,
                "route": route_pdf,
                "pages": total_pages,
                "size": size_bytes
            }

        except ErrorConversorPDF as e:
            return {
                "ok": False,
                "error": str(e)
            }
        
        except Exception as e:
            return{
                "ok": False,
                "error": f"No se pudo Seleccionar el PDF: {e}"
            }

        #Obtenemos el Estado

        def get_state(self):

            return {
                "ok": True,
                "pdf_seleccionado": self.pdf_actual is not None
            }

        #Conversion del PDF

    def convertir_pdf(
        self,
        formato,
        dpi,
        rango
    ):
        try:

            # campo Para la comprobación del PDF

             if not self.pdf_actual:

                return {
                    "ok": False,
                    "error": "Primero debes seleccionar un PDF."
                }
            
            #Validacion del DPI

                try:

                    dpi = int(dpi)

                except (TypeError, ValueError):

                    return {
                    "ok": False,
                    "error": "El DPI debe ser un número entero."
                }

                if dpi < 10 or dpi > 1200:

                    return{
                        "ok": False,
                        "error": "EL DPI Debe estar entre 10 y 1200"
                    }

                #Validación del formato

                formato = str(formato).lower().split()

                format_acces = {
                    "png",
                    "jpg",
                    "bmp",
                    "tiff"
                }

                if formato not in format_acces:
                    
                    return{
                        "ok": False,
                        "error": "El Formato Seleccionado No es valido"
                    }

                # carpeta de salida Para el Archivo 

                folder = os.path.dirname(
                    self.pdf_actual
                )

                name_pdf = os.path.splitext(
                    os.path.basename(
                        self.pdf_actual
                    )
                )[0]

                folder_output = os.path.join(
                    folder,
                    f"{name_pdf}_Convertido"
                )

                        


            




        


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


