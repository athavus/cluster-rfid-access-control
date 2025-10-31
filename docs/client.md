# Raspberry Pi IoT Dashboard (Vue 3)

Interface web para monitorar e controlar dispositivos Raspberry Pi em rede local. Este componente exibe a lista de dispositivos, mostra detalhes do selecionado (CPU, memória, rede, etc.) e permite ligar/desligar um LED externo via GPIO, com atualização automática a cada 5 segundos.

- Framework: Vue 3 (Composition API)
- Estilos: Tailwind CSS
- Comunicação: serviços HTTP abstraídos em `services/raspberryApi.js`

---

## Funcionalidades

- Lista de dispositivos Raspberry disponíveis (raspberry_id)
- Painel de detalhes para o dispositivo selecionado:
  - Status do LED externo (ON/OFF) e último update
  - WiFi, memória, temperatura da CPU, %CPU, GPIO usados, SPI/I2C, USB e interfaces de rede
- Controle de LED externo:
  - Define o pino GPIO (BCM)
  - Define IP de destino (opcional; porta 8000 assumida se omitida)
  - Ações: Ligar/Desligar
- Estado de conectividade (Online/Offline)
- Indicador de carregamento (overlay) e toasts de erro
- Atualização automática dos dados a cada 5s
- Leitura de mensagens em tempo real com filtragem pelo dispositivo selecionado (API prevista; UI pronta para usar)

---

## Pré-requisitos

- Node.js 18+ (recomendado) e npm, yarn ou pnpm
- Backend/API que forneça os endpoints utilizados pelos serviços:
  - Lista e detalhes de dispositivos
  - Mensagens em tempo real (polling)
  - Ações de LED (ligar/desligar)
- Tailwind CSS configurado no projeto (ou substitua as classes por seu sistema de design)

---

## Como rodar

Este componente é um Single File Component (SFC) Vue. Abaixo um fluxo típico usando Vite:

1) Instale dependências
- npm install
- ou yarn
- ou pnpm install

2) Configure variáveis de ambiente (ex.: base da API)
Crie um arquivo `.env` na raiz do projeto, por exemplo:
VITE_API_BASE_URL=http://192.168.0.100:8000

3) Inicie em desenvolvimento
- npm run dev
- ou yarn dev
- ou pnpm dev

4) Build de produção
- npm run build
- npm run preview

Observação: os scripts exatos dependem do setup do seu projeto (Vite, Vue CLI, Nuxt, etc.). Ajuste conforme necessário.

---

## Integração do Componente

Use o componente diretamente em uma página ou layout:

```vue
<!-- App.vue -->
<template>
  <RaspberryControl />
</template>

<script setup>
import RaspberryControl from './components/RaspberryControl.vue'
</script>
```

---

## Contrato dos serviços de API (raspberryApi.js)

O componente espera três serviços exportados: `deviceService`, `ledService`, `realtimeService`. Abaixo uma implementação de referência (ajuste URLs conforme seu backend):

```js
// src/services/raspberryApi.js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000
})

export const deviceService = {
  // GET /devices -> [{ raspberry_id: "abc123" }, ...]
  async getAllDevices() {
    const { data } = await api.get('/devices')
    // Retorno esperado: array de objetos com pelo menos { raspberry_id }
    return data
  },

  // GET /devices/:id -> detalhes do dispositivo
  async getDevice(raspberryId) {
    const { data } = await api.get(`/devices/${encodeURIComponent(raspberryId)}`)
    /* Exemplo de retorno esperado:
      {
        raspberry_id: "abc123",
        led_external_status: true,          // boolean
        last_update: "2024-05-20T12:34:56Z",
        wifi_status: "wlan0: connected",
        mem_usage: "512MB / 1GB (50%)",
        cpu_temp: "48.2°C",
        cpu_percent: 13.7,
        gpio_used_count: 3,
        spi_buses: "spi0.0, spi0.1",
        i2c_buses: "i2c-1",
        usb_devices_count: 2,
        net_ifaces: ["lo", "eth0", "wlan0"] // Array obrigatório
      }
    */
    return data
  }
}

export const realtimeService = {
  // GET /realtime?limit=50 -> { data: [ ...mensagens... ] }
  async getData(limit = 50) {
    const { data } = await api.get('/realtime', { params: { limit } })
    /* Exemplo:
      {
        data: [
          { raspberry_id: "abc123", ts: "2024-05-20T12:34:56Z", event: "temp", value: 48.2 },
          ...
        ]
      }
    */
    return data
  }
}

export const ledService = {
  // POST /devices/:id/led/external/on
  async turnOn(type = 'external', raspberryId, pinBcm, targetHost) {
    await api.post(`/devices/${encodeURIComponent(raspberryId)}/led/${type}/on`, {
      pin: pinBcm,
      target_host: normalizeHostForApi(targetHost) // ex.: "192.168.0.50:8000"
    })
  },

  // POST /devices/:id/led/external/off
  async turnOff(type = 'external', raspberryId, pinBcm, targetHost) {
    await api.post(`/devices/${encodeURIComponent(raspberryId)}/led/${type}/off`, {
      pin: pinBcm,
      target_host: normalizeHostForApi(targetHost)
    })
  }
}

// Utilitário (mesma lógica da UI): remove espaços/;/, e aplica porta 8000 se ausente
function normalizeHostForApi(raw) {
  if (!raw) return null
  const cleaned = String(raw).trim().replace(/;|\s|,/g, '')
  if (!cleaned) return null
  if (/:\d+$/.test(cleaned)) return cleaned
  return `${cleaned}:8000`
}
```

Dicas importantes:
- `net_ifaces` deve ser um array para evitar erros no `.join(', ')`.
- `cpu_percent` pode ser número ou string; a UI normaliza para 1 casa decimal.
- `led_external_status` deve ser booleano para refletir ON/OFF corretamente.

---

## Como a UI funciona (fluxo)

- Ao montar:
  - Busca todos os dispositivos
  - Seleciona o primeiro por padrão (se houver)
  - Carrega detalhes do selecionado
  - Busca mensagens em tempo real
  - Inicia um timer para atualizar detalhes e realtime a cada 5s
- Ao clicar em um dispositivo:
  - Atualiza `selectedDeviceId` e busca detalhes
- Ao clicar “Ligar/Desligar”:
  - Chama `ledService.turnOn/turnOff` com:
    - tipo: 'external'
    - raspberry_id selecionado
    - pino GPIO (BCM) escolhido
    - targetHost (opcional; se vazio, backend decide o alvo padrão)
  - Recarrega os detalhes do dispositivo
- Indicadores e estados:
  - “Online/Offline” reflete sucesso/erro nas chamadas
  - Overlay de loading é exibido durante operações
  - Toast de erro aparece no canto inferior direito

---

## Opções e personalizações

- Intervalo de atualização: padrão 5000 ms
  - Ajuste em `setInterval(..., 5000)` no `onMounted`
- Pino padrão do LED externo: 17
  - Controlado por `externalLedPin` no `setup()`
- Porta padrão do target host: 8000
  - Implementada por `normalizeHost`/`normalizeHostForApi`
- Validação do IP:
  - A UI remove espaços, vírgulas e ponto-e-vírgulas
  - Você pode estender a validação (IPv4/IPv6) conforme sua necessidade

---

## Observações de segurança

- O campo “IP do dispositivo alvo” é enviado ao backend. Valide e sanitize também no servidor.
- Se expuser o painel fora da rede local, atente-se para CORS, autenticação e autorização.
- Evite permitir SSRF (Server-Side Request Forgery) em rotas que recebem `target_host`.

---

## Testando sem backend (mock simples)

```js
// src/services/raspberryApi.js (mock)
const wait = (ms) => new Promise(r => setTimeout(r, ms))
const MOCK_ID = 'rpi-001'

export const deviceService = {
  async getAllDevices() {
    await wait(300)
    return [{ raspberry_id: MOCK_ID }]
  },
  async getDevice(id) {
    await wait(300)
    return {
      raspberry_id: id,
      led_external_status: Math.random() > 0.5,
      last_update: new Date().toISOString(),
      wifi_status: 'wlan0: connected',
      mem_usage: '512MB / 1GB (50%)',
      cpu_temp: '47.8°C',
      cpu_percent: +(Math.random() * 40).toFixed(1),
      gpio_used_count: 3,
      spi_buses: 'spi0.0, spi0.1',
      i2c_buses: 'i2c-1',
      usb_devices_count: 2,
      net_ifaces: ['lo', 'eth0', 'wlan0']
    }
  }
}

export const realtimeService = {
  async getData(limit = 50) {
    await wait(200)
    return {
      data: Array.from({ length: limit }, (_, i) => ({
        raspberry_id: MOCK_ID,
        ts: new Date(Date.now() - i * 1000).toISOString(),
        event: 'cpu',
        value: +(Math.random() * 100).toFixed(1)
      }))
    }
  }
}

export const ledService = {
  async turnOn() { await wait(200) },
  async turnOff() { await wait(200) }
}
```

---

## Troubleshooting

- “Erro ao buscar dispositivos/detalhes/realtime”:
  - Verifique `VITE_API_BASE_URL` e conectividade com o backend
  - Cheque CORS no backend
- LED não liga/desliga:
  - Confirme o pino BCM correto (ex.: LED no pino físico 11 = BCM 17)
  - Confirme o `targetHost` (ex.: 192.168.0.50) e se a porta padrão 8000 é a correta no seu backend
  - Verifique permissões e configuração de GPIO no Raspberry
- `net_ifaces.join is not a function`:
  - Garanta que a API retorne `net_ifaces` como array (ex.: `["lo","eth0"]`)


---

## 📄 Licença

Você pode licenciar este código conforme as necessidades do seu projeto (ex.: MIT). Substitua esta seção pela licença de sua preferência.