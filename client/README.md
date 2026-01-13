# Virtus Dashboard - Client

[Vue 3](https://vuejs.org/) + [TypeScript](https://www.typescriptlang.org/) + [Vite](https://vitejs.dev/)

Este é o frontend administrativo para o sistema **Raspberry Gate**. Ele fornece uma interface visual para monitorar o status das placas Raspberry Pi, gerenciar tags RFID e controlar dispositivos conectados (LEDs, relés).

## Funcionalidades

*   **Dashboard em Tempo Real**: Visualize CPU, RAM, Temperatura e Status Wifi de cada nó.
*   **Controle de Hardware**: Interface para ligar/desligar LEDs e acionar atuadores manualmente.
*   **Gestão RFID**:
    *   Log de leituras recentes.
    *   Cadastro de novas tags (associação de UID a nomes).
    *   Exportação de histórico de acessos (CSV).
*   **Diagnóstico**: Visualização de logs e status da rede.

## Tecnologias

*   **Framework**: Vue 3 (Composition API, Script Setup)
*   **Build Tool**: Vite
*   **Linguagem**: TypeScript
*   **Estilização**: TailwindCSS (ou CSS Modules - verificar setup)
*   **Comunicação**: Axios (REST API para o Backend)

## Como rodar

Certifique-se de que o **Server** esteja rodando (padrão: `http://localhost:8000`).

1.  Instale as dependências:
    ```bash
    npm install
    ```

2.  Inicie o servidor de desenvolvimento:
    ```bash
    npm run dev
    ```

3.  Acesse no navegador:
    ```text
    http://localhost:5173
    ```

## Configuração

O cliente tenta se conectar automaticamente ao backend.
*   A configuração da API está em `src/services/raspberryApi.js`.
*   Por padrão, ele busca o backend no mesmo IP que o cliente, na porta `:8000`.
