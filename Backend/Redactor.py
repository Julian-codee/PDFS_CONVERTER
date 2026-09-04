#!/usr/bin/env python3

import os
import re

import pymupdf
from PIL import Image

FORMATOS_PIL = {"png": "PNG", "jpg": "JPEG", "bmp": "BMP", "tiff": "TIFF"}

# Límites de DPI. Por debajo del mínimo la imagen queda inservible
# (bordes borrosos, texto ilegible); por encima del máximo, una sola página
# puede generar un mapa de bits de cientos de MB y agotar la memoria o
# tardar minutos en renderizarse.
DPI_MINIMO = 10
DPI_MAXIMO = 1200


class ErrorConversorPDF(Exception):
    """Clase base para todos los errores propios de este módulo."""


class ArchivoPDFInvalido(ErrorConversorPDF):
    """
    Se lanza cuando la ruta de entrada no corresponde a un archivo PDF
    utilizable (no existe, no es un archivo, o no es un .pdf).
    """


class DPIInvalido(ErrorConversorPDF):
    """
    Se lanza cuando el valor de DPI no es un número válido o está fuera
    del rango permitido (DPI_MINIMO..DPI_MAXIMO).
    """


class DimensionInvalida(ErrorConversorPDF):
    """
    Se lanza cuando ancho_maximo o alto_maximo no son válidos
    (deben ser números positivos, o None si no se quiere límite).
    """


class RangoPaginasInvalido(ErrorConversorPDF):
    """
    Se lanza cuando el texto de rango de páginas no se puede interpretar:
    caracteres no permitidos, rangos mal formados (ej. '5-2', '1-', '-3'),
    o páginas fuera del total de páginas del documento.
    """


def validar_archivo_pdf(ruta_pdf):

    if not ruta_pdf or not str(ruta_pdf).strip():
        raise ArchivoPDFInvalido("No se especificó ninguna ruta de archivo PDF.")

    if not os.path.exists(ruta_pdf):
        raise ArchivoPDFInvalido(
            f"El archivo no existe: '{ruta_pdf}'. Verifica la ruta e intenta de nuevo."
        )

    if not os.path.isfile(ruta_pdf):
        raise ArchivoPDFInvalido(
            f"La ruta indicada no es un archivo: '{ruta_pdf}'. "
            "Asegúrate de apuntar a un archivo .pdf, no a una carpeta."
        )

    if not ruta_pdf.lower().endswith(".pdf"):
        raise ArchivoPDFInvalido(
            f"El archivo no tiene extensión .pdf: '{ruta_pdf}'."
        )


def validar_dpi(dpi):

    try:
        dpi_numerico = float(dpi)
    except (TypeError, ValueError):
        raise DPIInvalido(f"El DPI debe ser un número. Se recibió: {dpi!r}")

    if dpi_numerico != dpi_numerico:  # comprobación de NaN sin depender de math
        raise DPIInvalido("El DPI no puede ser NaN (no es un número).")

    if dpi_numerico <= 0:
        raise DPIInvalido(
            f"El DPI no puede ser negativo ni cero (se recibió {dpi_numerico})."
        )

    if dpi_numerico < DPI_MINIMO:
        raise DPIInvalido(
            f"El DPI ({dpi_numerico}) es demasiado bajo: la imagen resultante "
            f"quedaría inservible. El mínimo permitido es {DPI_MINIMO} DPI."
        )

    if dpi_numerico > DPI_MAXIMO:
        raise DPIInvalido(
            f"El DPI ({dpi_numerico}) es demasiado alto: podría generar una "
            f"imagen extremadamente pesada y agotar la memoria del equipo. "
            f"El máximo permitido es {DPI_MAXIMO} DPI."
        )

    return int(round(dpi_numerico))


def validar_dimension_maxima(valor, nombre_parametro):

    if valor is None:
        return None

    try:
        valor_numerico = float(valor)
    except (TypeError, ValueError):
        raise DimensionInvalida(
            f"{nombre_parametro} debe ser un número entero positivo (o None "
            f"para no limitar). Se recibió: {valor!r}"
        )

    if valor_numerico <= 0:
        raise DimensionInvalida(
            f"{nombre_parametro} debe ser mayor que 0 (se recibió {valor_numerico})."
        )

    return int(round(valor_numerico))


def _validar_numero_pagina(numero, total_paginas, contexto):
    """Verifica que un número de página sea >= 1 y <= total_paginas."""
    if numero < 1:
        raise RangoPaginasInvalido(
            f"Página inválida en '{contexto}': las páginas empiezan en 1, "
            f"no en {numero}."
        )
    if numero > total_paginas:
        raise RangoPaginasInvalido(
            f"La página {numero} (en '{contexto}') está fuera de rango: "
            f"el documento solo tiene {total_paginas} página(s)."
        )


def parsear_rango(texto, total_paginas):

    if total_paginas <= 0:
        return []

    texto_limpio = re.sub(r"\s+", "", texto or "")
    if not texto_limpio:
        return list(range(total_paginas))

    caracteres_permitidos = set("0123456789,-")
    caracteres_invalidos = sorted(set(texto_limpio) - caracteres_permitidos)
    if caracteres_invalidos:
        raise RangoPaginasInvalido(
            f"El rango de páginas '{texto}' contiene caracteres no permitidos: "
            f"{', '.join(repr(c) for c in caracteres_invalidos)}. "
            "Solo se permiten números, comas y guiones (ej: '1-3,7,10-15')."
        )

    paginas = set()

    for parte in texto_limpio.split(","):
        if parte == "":
            raise RangoPaginasInvalido(
                f"El rango de páginas '{texto}' tiene una sección vacía "
                "(revisa que no haya comas de más, como '1,,3' o una coma al final)."
            )

        if re.fullmatch(r"\d+", parte):
            numero = int(parte)
            _validar_numero_pagina(numero, total_paginas, parte)
            paginas.add(numero - 1)

        elif re.fullmatch(r"\d+-\d+", parte):
            inicio_str, fin_str = parte.split("-")
            inicio, fin = int(inicio_str), int(fin_str)
            if inicio > fin:
                raise RangoPaginasInvalido(
                    f"Rango inválido '{parte}': el inicio ({inicio}) es mayor "
                    f"que el fin ({fin}). ¿Quisiste decir '{fin}-{inicio}'?"
                )
            _validar_numero_pagina(inicio, total_paginas, parte)
            _validar_numero_pagina(fin, total_paginas, parte)
            for p in range(inicio, fin + 1):
                paginas.add(p - 1)

        else:
            raise RangoPaginasInvalido(
                f"No se entendió la sección '{parte}' del rango '{texto}'. "
                "Usa números sueltos ('5'), rangos ('1-5') o una combinación "
                "separada por comas ('1-3,7,10-15')."
            )

    return sorted(paginas)


def nombre_seguro(nombre):
    """Limpia un nombre de archivo para evitar caracteres problemáticos."""
    base = os.path.splitext(os.path.basename(nombre))[0]
    return re.sub(r"[^A-Za-z0-9_\-]", "_", base) or "documento"


def obtener_dimensiones_pagina(pagina, dpi):

    factor = dpi / 72
    ancho_px = round(pagina.rect.width * factor)
    alto_px = round(pagina.rect.height * factor)
    return ancho_px, alto_px


def calcular_tamano_redimensionado(ancho, alto, ancho_maximo=None, alto_maximo=None):

    if ancho <= 0 or alto <= 0:
        return ancho, alto

    factor = 1.0
    if ancho_maximo is not None and ancho > ancho_maximo:
        factor = min(factor, ancho_maximo / ancho)
    if alto_maximo is not None and alto > alto_maximo:
        factor = min(factor, alto_maximo / alto)

    if factor >= 1.0:
        return ancho, alto

    nuevo_ancho = max(1, round(ancho * factor))
    nuevo_alto = max(1, round(alto * factor))
    return nuevo_ancho, nuevo_alto


def redimensionar_manteniendo_proporcion(imagen, ancho_maximo=None, alto_maximo=None):
   
    nuevo_ancho, nuevo_alto = calcular_tamano_redimensionado(
        imagen.width, imagen.height, ancho_maximo, alto_maximo
    )
    if (nuevo_ancho, nuevo_alto) == imagen.size:
        return imagen
    return imagen.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)


def calcular_dpi_efectivo(ancho_px, alto_px, ancho_pagina_puntos, alto_pagina_puntos):

    pulgadas_ancho = ancho_pagina_puntos / 72
    pulgadas_alto = alto_pagina_puntos / 72

    dpi_x = ancho_px / pulgadas_ancho if pulgadas_ancho > 0 else ancho_px
    dpi_y = alto_px / pulgadas_alto if pulgadas_alto > 0 else alto_px

    return round(dpi_x), round(dpi_y)


def convertir_pdf_a_imagenes(
    ruta_pdf,
    carpeta_salida,
    formato="png",
    dpi=200,
    rango_texto="",
    ancho_maximo=None,
    alto_maximo=None,
):

    validar_archivo_pdf(ruta_pdf)
    dpi = validar_dpi(dpi)
    ancho_maximo = validar_dimension_maxima(ancho_maximo, "ancho_maximo")
    alto_maximo = validar_dimension_maxima(alto_maximo, "alto_maximo")

    formato = formato.lower()
    if formato not in FORMATOS_PIL:
        raise ValueError(f"Formato no soportado: {formato}")

    os.makedirs(carpeta_salida, exist_ok=True)

    zoom = dpi / 72
    matriz = pymupdf.Matrix(zoom, zoom)
    nombre_base = nombre_seguro(ruta_pdf)

    resultados = []

    documento = pymupdf.open(ruta_pdf)
    try:
        total_paginas = documento.page_count
        indices = parsear_rango(rango_texto, total_paginas)

        for indice in indices:
            pagina = documento.load_page(indice)

            # 1) Dimensiones esperadas ANTES de renderizar (informativo y
            #    útil para decidir si hará falta redimensionar después).
            dimensiones_render = obtener_dimensiones_pagina(pagina, dpi)

            pix = pagina.get_pixmap(matrix=matriz, alpha=False)
            imagen = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            # 2) Redimensionamiento posterior, manteniendo proporción,
            #    respetando ancho_maximo y alto_maximo.
            imagen = redimensionar_manteniendo_proporcion(
                imagen, ancho_maximo, alto_maximo
            )

            # 3) DPI efectivo: si no hubo redimensionamiento, es igual al
            #    DPI pedido. Si sí lo hubo, se recalcula para que el
            #    metadato refleje el tamaño físico real de impresión.
            dpi_efectivo = calcular_dpi_efectivo(
                imagen.width, imagen.height, pagina.rect.width, pagina.rect.height
            )

            nombre_archivo = f"{nombre_base}_pag{indice + 1}.{formato}"
            ruta_salida = os.path.join(carpeta_salida, nombre_archivo)

            kwargs = {"quality": 92} if formato == "jpg" else {}
            kwargs["dpi"] = dpi_efectivo
            imagen.save(ruta_salida, format=FORMATOS_PIL[formato], **kwargs)

            resultados.append(
                {
                    "ruta": ruta_salida,
                    "pagina": indice + 1,
                    "dimensiones_render": dimensiones_render,
                    "dimensiones_finales": imagen.size,
                    "dpi_metadata": dpi_efectivo,
                }
            )
    finally:
        documento.close()

    return resultados


if __name__ == "__main__":
    # Ejemplo de uso directo por consola:
    #   python conversor_pdf.py mi_archivo.pdf salida png 300 "" 3000 4000
    import sys

    if len(sys.argv) < 2:
        print(
            "Uso: python conversor_pdf.py <archivo.pdf> [carpeta_salida] "
            "[formato] [dpi] [rango] [ancho_maximo] [alto_maximo]"
        )
        sys.exit(1)

    pdf = sys.argv[1]
    salida = sys.argv[2] if len(sys.argv) > 2 else "salida"
    fmt = sys.argv[3] if len(sys.argv) > 3 else "png"
    dpi_arg = sys.argv[4] if len(sys.argv) > 4 else 200
    rango_arg = sys.argv[5] if len(sys.argv) > 5 else ""
    ancho_max_arg = sys.argv[6] if len(sys.argv) > 6 else None
    alto_max_arg = sys.argv[7] if len(sys.argv) > 7 else None

    try:
        generadas = convertir_pdf_a_imagenes(
            pdf, salida, fmt, dpi_arg, rango_arg, ancho_max_arg, alto_max_arg
        )
    except ErrorConversorPDF as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Se generaron {len(generadas)} imagen(es):")
    for r in generadas:
        ancho_final, alto_final = r["dimensiones_finales"]
        dpi_x, dpi_y = r["dpi_metadata"]
        print(
            f"  - {r['ruta']}  ({ancho_final}x{alto_final} px, "
            f"metadato {dpi_x}x{dpi_y} DPI)"
        )
