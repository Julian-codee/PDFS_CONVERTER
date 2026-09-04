const boton = document.getElementById("btnProbar");
const estado = document.getElementById("estado");


boton.addEventListener("click", async () => {

    try {

        const response =
            await window.pywebview.api.test_conection();

        console.log(response);

        if (response.ok) {

            estado.textContent =
                response.Message;

        }

    } catch (error) {

        console.error(error);

        estado.textContent =
            "Error de comunicación con Python.";

    }

});