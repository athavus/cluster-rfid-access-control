from controllers.keyboard import start_keyboard_listener
from system.app import run_system

def main():
    # Inicia o listener de teclado
    start_keyboard_listener()

    # Executa o sistema principal
    run_system()

if __name__ == "__main__":
    main()
