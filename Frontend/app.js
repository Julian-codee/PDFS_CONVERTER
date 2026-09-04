const boton = document.getElementById("btnProbar");
const estado = document.getElementById("estado");


boton.addEventListener("click", async () => {

    try {

        const respuesta =
            await window.pywebview.api.test_conection();

        console.log(respuesta);

        if (respuesta.ok) {

            estado.textContent =
                respuesta.Message;

        }

    } catch (error) {

        console.error(error);

        estado.textContent =
            "Error de comunicación con Python.";

    }

});