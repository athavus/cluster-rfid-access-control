from evdev import InputDevice, categorize, ecodes
import threading

class Keyboard:
    def __init__(self, device_path):
        """
        ----------------------------------------------------------------------
        @brief Construtor da classe Keyboard.
        
        Inicializa o dispositivo de entrada, variáveis de controle para teclas especiais
        (CapsLock, ESC) e o mapeamento de teclas normais e com Shift.

        @param device_path: Caminho do dispositivo de teclado (ex: "/dev/input/event0").
        ----------------------------------------------------------------------
        """
        self.dev = InputDevice(device_path)
        self.caps_lock = False
        self.shift_pressed = False
        self.buffer = []
        self.lock = threading.Lock()

        # Mapa de teclas 
        self.keycode_map = {
            'KEY_A': 'a', 'KEY_B': 'b', 'KEY_C': 'c', 'KEY_D': 'd',
            'KEY_E': 'e', 'KEY_F': 'f', 'KEY_G': 'g', 'KEY_H': 'h',
            'KEY_I': 'i', 'KEY_J': 'j', 'KEY_K': 'k', 'KEY_L': 'l',
            'KEY_M': 'm', 'KEY_N': 'n', 'KEY_O': 'o', 'KEY_P': 'p',
            'KEY_Q': 'q', 'KEY_R': 'r', 'KEY_S': 's', 'KEY_T': 't',
            'KEY_U': 'u', 'KEY_V': 'v', 'KEY_W': 'w', 'KEY_X': 'x',
            'KEY_Y': 'y', 'KEY_Z': 'z',
            'KEY_SPACE': ' ',
            'KEY_1': '1','KEY_2': '2','KEY_3': '3','KEY_4': '4','KEY_5': '5',
            'KEY_6': '6','KEY_7': '7','KEY_8': '8','KEY_9': '9','KEY_0': '0',
            'KEY_MINUS': '-', 'KEY_EQUAL': '=', 'KEY_COMMA': ',', 'KEY_DOT': '.',
            'KEY_SLASH': '/', 'KEY_SEMICOLON': ';', 'KEY_APOSTROPHE': "'",
            'KEY_LEFTBRACE': '[', 'KEY_RIGHTBRACE': ']', 'KEY_BACKSLASH': '\\'
        }

        # Mapa de teclas modificadas por Shift
        self.shift_map = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
            '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
            '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
            ';': ':', "'": '"', ',': '<', '.': '>', '/': '?'
        }

    def process_key(self, key):
        """
        ----------------------------------------------------------------------
        @brief Processa um evento de tecla e atualiza o buffer interno.

        Trata teclas especiais (CapsLock, Shift, Backspace, Enter, ESC, setas)
        e converte códigos de teclas em caracteres ASCII correspondentes.

        @param key: Evento de tecla categorizado (objeto retornado por categorize()).

        @return O caractere processado (se houver), ou None se nenhuma tecla útil foi registrada.
        ----------------------------------------------------------------------
        """
        with self.lock:
            # Caps Lock
            if key.keycode == 'KEY_CAPSLOCK' and key.keystate == key.key_down:
                self.caps_lock = not self.caps_lock

            # Shift
            elif key.keycode in ['KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT']:
                if key.keystate == key.key_down:
                    self.shift_pressed = True
                elif key.keystate == key.key_up:
                    self.shift_pressed = False

            # Backspace
            elif key.keycode == 'KEY_BACKSPACE' and key.keystate == key.key_down:
                if self.buffer:
                    self.buffer.pop()

            # ESC
            elif key.keycode == 'KEY_ESC' and key.keystate == key.key_down:
                self.buffer.append('\x1b')  # ESC ASCII

            # Setas
            elif key.keycode == 'KEY_UP' and key.keystate == key.key_down:
                self.buffer.append('\x1b[A')  # seta cima
            elif key.keycode == 'KEY_DOWN' and key.keystate == key.key_down:
                self.buffer.append('\x1b[B')  # seta baixo

            # Enter
            elif key.keycode in ['KEY_ENTER', 'KEY_KPENTER'] and key.keystate == key.key_down:
                self.buffer.append('\r')

            # Caracteres normais
            elif key.keystate == key.key_down:
                if key.keycode in self.keycode_map:
                    char = self.keycode_map[key.keycode]

                    # Aplica CapsLock e Shift
                    if char.isalpha():
                        if self.caps_lock ^ self.shift_pressed:  # XOR
                            char = char.upper()
                        else:
                            char = char.lower()
                    else:
                        if self.shift_pressed and char in self.shift_map:
                            char = self.shift_map[char]

                    self.buffer.append(char)
                    return char
        return None

    def keyboard_loop(self):
        """
        ----------------------------------------------------------------------
        @brief Loop contínuo que lê eventos do dispositivo e processa teclas.

        Essa função bloqueia o thread e deve ser usada em uma thread separada.
        Lê os eventos do teclado e envia cada evento de tecla para process_key().

        @return None
        ----------------------------------------------------------------------
        """
        for event in self.dev.read_loop():
            if event.type == ecodes.EV_KEY:
                key = categorize(event)
                self.process_key(key)

    def start(self):
        """
        ----------------------------------------------------------------------
        @brief Inicia o monitoramento do teclado em um thread separado.

        Cria e inicia uma thread daemon para o método keyboard_loop().

        @return None
        ----------------------------------------------------------------------
        """
        t = threading.Thread(target=self.keyboard_loop, daemon=True)
        t.start()

    def get_buffer(self):
        """
        ----------------------------------------------------------------------
        @brief Retorna o conteúdo atual do buffer de entrada.

        @return Uma string com todos os caracteres digitados até o momento.
        ----------------------------------------------------------------------
        """
        with self.lock:
            return "".join(self.buffer)

    def clear_buffer(self):
        """
        ----------------------------------------------------------------------
        @brief Limpa o buffer de entrada.

        Remove todos os caracteres armazenados.

        @return None
        ----------------------------------------------------------------------
        """
        with self.lock:
            self.buffer.clear()

    def listen(self, callback):
        """
        ----------------------------------------------------------------------
        @brief Escuta continuamente o buffer chamando uma função callback para cada novo caractere.

        Essa função compara o buffer anterior com o atual e chama a função callback
        passada pelo usuário a cada novo caractere recebido.

        @param callback: Função que será chamada com um argumento (caractere recebido).

        @return None
        ----------------------------------------------------------------------
        """
        try:
            ultimo_buffer = ""
            while True:
                buf = self.get_buffer()
                if len(buf) > len(ultimo_buffer):
                    novos = buf[len(ultimo_buffer):]
                    for c in novos:
                        callback(c)
                    ultimo_buffer = buf
        except KeyboardInterrupt:
            print("\nKeyboard listening interrompido pelo usuário.")


def start_keyboard(device_path):
    """
    ----------------------------------------------------------------------
    @brief Função de conveniência para inicializar o teclado.

    Cria uma instância de Keyboard, inicia a leitura de eventos
    e retorna o objeto para controle externo.

    @param device_path: Caminho do dispositivo de teclado (ex: "/dev/input/event0").

    @return Instância de Keyboard pronta para uso.
    ----------------------------------------------------------------------
    """
    kb = Keyboard(device_path)
    kb.start()
    return kb
