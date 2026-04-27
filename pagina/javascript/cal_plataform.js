    
    // Obtiene desde localStorage el nombre del maestro que fue seleccionado previamente
        const maestroSeleccionado = localStorage.getItem('maestroSeleccionado');

    // Muestra en pantalla el texto "Evaluando a: [maestro]"
    // Insertándolo dentro del elemento con id "Selectormestro"
        document.getElementById('Selectormestro').textContent = `Evaluando a: ${maestroSeleccionado}`;

        // Escucha el evento "submit" del formulario con id "calification"
        document.getElementById('calification').addEventListener('submit', function(event) {

        // Evita que el formulario recargue la página automáticamente
        event.preventDefault();

        // Obtiene la calificación seleccionada por el usuario
const exp = document.getElementById('explicationsTopics').value;
const act = document.getElementById('actitudinal').value;
const cls = document.getElementById('classActivity').value;
        // Si el usuario seleccionó una calificación...
        if (exp && act && cls) {

            // Guarda la calificación en localStorage
            localStorage.setItem('calification', JSON.stringify({ exp, act, cls}));

            // Redirige nuevamente a la pagina de gracias
            window.location.href = 'certificado.html';
        } else {

            // Si no seleccionó nada, muestra un mensaje de alerta
            alert('Por favor, selecciona una nota para cada casilla.');
        }
    });
