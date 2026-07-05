dict = [
        {"username": "1025657849", "password": "MJAVIERA", "redirect": "/seleccionatuprofesor"},
        {"username": "1025657456", "password": "MJAVIERA", "redirect": "/seleccionatuprofesor"},
        {"username": "1020113554", "password": "MJAVIERA", "redirect": "/seleccionatuprofesor"},
        {"username": "fabioman", "password": "MJAVIERA", "redirect": "/configuracion"}
]

def verificar_usuario(username, password):
    for user in dict:
        if user["username"] == username and user["password"] == password:
            return user["redirect"]
    return None