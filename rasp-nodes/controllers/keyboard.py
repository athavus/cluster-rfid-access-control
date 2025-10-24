import threading
from libs.keyboard import start_keyboard

kb = start_keyboard("/dev/input/event1")
kb.clear_buffer()

def teclado_thread():
    """
    ----------------------------------------------------------------------
    @brief Thread de escuta de teclado.

    Função executada em segundo plano para ouvir continuamente o teclado,
    ignorando os caracteres capturados (callback vazio).

    @return None
    ----------------------------------------------------------------------
    """
    kb.listen(lambda char: None)


def start_keyboard_listener():
    """
    ----------------------------------------------------------------------
    @brief Inicia o listener de teclado em uma thread separada.

    Cria e inicia uma thread daemon que executa a função teclado_thread(),
    permitindo que a leitura do teclado ocorra em paralelo ao restante do programa.

    @return None
    ----------------------------------------------------------------------
    """
    t = threading.Thread(target=teclado_thread, daemon=True)
    t.start()


def get_buffer():
    """
    ----------------------------------------------------------------------
    @brief Retorna o conteúdo atual do buffer do teclado.

    Fornece acesso ao texto digitado até o momento desde o último clear_buffer().

    @return Uma string contendo os caracteres digitados.
    ----------------------------------------------------------------------
    """
    return kb.get_buffer()


def clear_buffer():
    """
    ----------------------------------------------------------------------
    @brief Limpa o buffer do teclado.

    Remove todos os caracteres armazenados até o momento, reiniciando o estado do buffer.

    @return None
    ----------------------------------------------------------------------
    """
    kb.clear_buffer()
