

// Escucha el evento "submit" del formulario con id "Selectormestro"
    document.getElementById('Selectormestro').addEventListener('submit', function(event) {

        // Evita que el formulario recargue la página automáticamente
        event.preventDefault();

        // Obtiene el valor seleccionado del elemento con id "maestro"
        const maestro = document.getElementById('maestro').value;

        // Si el usuario seleccionó un maestro...
        if (maestro) {

            // Guarda el maestro elegido en el almacenamiento local del navegador
            localStorage.setItem('maestroSeleccionado', maestro);

            // Redirige a la siguiente página
            window.location.href = '../HTML/calification_plataform.html';
        } else {

            // Si no seleccionó nada, muestra un mensaje de alerta
            alert('Por favor, selecciona un maestro');
        }
    });

