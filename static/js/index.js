const users = [
        { username: "1025657849", password: "MJAVIERA", redirect: "/seleccionatuprofesor" },
        { username: "1025657456", password: "MJAVIERA", redirect: "/seleccionatuprofesor" },
        { username: "1020113554", password: "MJAVIERA", redirect: "/seleccionatuprofesor" },
        { username: "fabioman", password: "MJAVIERA", redirect: "/configuracion" },
]
    function login(event) {
        event.preventDefault();
        const user = document.getElementById("username").value;
        const pass = document.getElementById("password").value;

        const found = users.find(u => u.username === user && u.password === pass);

    if (found) {
            window.location.href = found.redirect;
        } 
        else {
        alert("Usuario o contraseña incorrectos.");
        }
    }