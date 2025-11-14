<template>
    <div class="min-h-screen bg-gray-50">
        <DashboardHeader
            :is-online="isOnline"
            @refresh="fetchAllData"
            @export-db="downloadDb"
        />

        <main
            class="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-4 gap-6"
        >
            <DeviceSelector
                :devices="devices"
                :selected-device-id="selectedDeviceId"
                @select-device="selectDevice"
            />

            <DeviceDetails
                :device-details="selectedDeviceDetails"
                :device-id="selectedDeviceId"
                :external-led-pin="externalLedPin"
                :target-host="targetHost"
                :loading="loading"
                :show-rfid-banner="showRfidBanner"
                @update:externalLedPin="externalLedPin = $event"
                @update:targetHost="targetHost = $event"
                @toggle-led="toggleLED"
            />

            <LoadingOverlay :loading="loading" />
            <ErrorBanner :error="error" @dismiss="error = null" />
            <RfidBanner
                :show="showRfidBanner"
                :uid="lastRfidUid"
                :tag-name="lastRfidTagName"
                @close="closeRfidBanner"
            />
            <RfidNameModal
                :show="showNameModal"
                :uid="lastRfidUid"
                :countdown="modalCountdown"
                @submit="submitTagName"
                @cancel="closeNameModal"
            />
        </main>
    </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import {
    deviceService,
    ledService,
    realtimeService,
    rfidService,
    exportService,
} from "../services/raspberryApi.js";
import DashboardHeader from "./DashboardHeader.vue";
import DeviceSelector from "./DeviceSelector.vue";
import DeviceDetails from "./DeviceDetails.vue";
import LoadingOverlay from "./LoadingOverlay.vue";
import ErrorBanner from "./ErrorBanner.vue";
import RfidBanner from "./RfidBanner.vue";
import RfidNameModal from "./RfidNameModal.vue";

export default {
    name: "RaspberryControl",
    components: {
        DashboardHeader,
        DeviceSelector,
        DeviceDetails,
        LoadingOverlay,
        ErrorBanner,
        RfidBanner,
        RfidNameModal,
    },
    setup() {
        const loading = ref(false);
        const error = ref(null);
        const isOnline = ref(true);

        const devices = ref([]);
        const selectedDeviceId = ref(null);
        const selectedDeviceDetails = ref(null);
        const realtimeMessages = ref([]);
        const externalLedPin = ref(17);
        const targetHost = ref("");
        const lastRfidUid = ref(null);
        const lastRfidTagName = ref(null);
        const lastRfidDisplay = ref("");
        const lastRfidTimestamp = ref(null);
        const showRfidBanner = ref(false);
        const showNameModal = ref(false);
        const modalCountdown = ref(15);
        let modalTimer = null;
        let bannerTimer = null;
        const detectionCooldownMs = 3000;
        const lastHandledAt = ref(0);

        // 🛡️ SISTEMA DE TRIPLA PROTEÇÃO RFID
        const isRfidInitialized = ref(false); // Flag de inicialização
        const lastSeenUid = ref(null); // Controle de UID duplicado
        let rfidInitTimeout = null;

        let refreshTimer = null;
        const lastRealtimeTs = ref(0);

        const fetchDevices = async () => {
            try {
                const data = await deviceService.getAllDevices();
                devices.value = data;
                if (!selectedDeviceId.value && data.length > 0) {
                    selectedDeviceId.value = data[0].raspberry_id;
                }
            } catch (err) {
                error.value = "Erro ao buscar dispositivos.";
                isOnline.value = false;
            }
        };

        const fetchDeviceDetails = async (id) => {
            if (!id) return;
            try {
                const details = await deviceService.getDevice(id);
                console.log(details);
                selectedDeviceDetails.value = details;
                isOnline.value = true;
            } catch {
                error.value = "Erro ao buscar detalhes do dispositivo.";
                selectedDeviceDetails.value = null;
                isOnline.value = false;
            }
        };

        const fetchRealtimeMessages = async () => {
            try {
                const data = await realtimeService.getData(50);
                realtimeMessages.value = data.data || [];
                isOnline.value = true;
            } catch {
                error.value = "Erro ao buscar mensagens em tempo real.";
                isOnline.value = false;
            }
        };

        const fetchAllData = async () => {
            loading.value = true;
            error.value = null;
            try {
                await fetchDevices();
                if (selectedDeviceId.value) {
                    await fetchDeviceDetails(selectedDeviceId.value);
                }
                await fetchRealtimeMessages();
                isOnline.value = true;
            } catch {
                error.value = "Erro ao carregar dados da API.";
                isOnline.value = false;
            }
            loading.value = false;
        };

        const pollLastRfid = async () => {
            if (!isRfidInitialized.value) {
                return;
            }

            if (!selectedDeviceId.value) return;

            try {
                const data = await rfidService.getLastRead(
                    selectedDeviceId.value,
                );
                if (!data.exists) return;

                if (data.timestamp) {
                    const readTime = new Date(data.timestamp);
                    const now = new Date();
                    const diffSeconds = (now - readTime) / 1000;

                    // Ignora leituras antigas (mais de 5 segundos)
                    if (diffSeconds > 5) {
                        console.log(
                            `⏰ Leitura RFID ignorada (${diffSeconds.toFixed(1)}s atrás)`,
                        );
                        return;
                    }
                }

                const ts = new Date(data.timestamp).getTime();

                if (lastRfidTimestamp.value && ts <= lastRfidTimestamp.value)
                    return;

                const now = Date.now();

                // Cooldown para evitar duplicatas durante modal aberto
                if (
                    showNameModal.value &&
                    data.uid === lastRfidUid.value &&
                    now - lastHandledAt.value < detectionCooldownMs
                ) {
                    return;
                }

                console.log("Nova tag RFID detectada:", data.uid);

                lastSeenUid.value = data.uid;
                lastHandledAt.value = now;
                lastRfidUid.value = data.uid;
                lastRfidTagName.value = data.tag_name || null;
                lastRfidDisplay.value =
                    data.tag_name && data.tag_name !== "<Sem nome>"
                        ? `Olá ${data.tag_name} (UID ${data.uid})`
                        : `RFID detectado: UID ${data.uid}`;
                lastRfidTimestamp.value = ts;

                showRfidBanner.value = true;

                // Aumentar o tempo de exibição do banner para 8 segundos
                if (bannerTimer) clearTimeout(bannerTimer);
                bannerTimer = setTimeout(() => {
                    showRfidBanner.value = false;
                }, 8000);

                // Abre modal de nomeação se tag não tiver nome
                if (
                    (!data.tag_name || data.tag_name === "<Sem nome>") &&
                    !showNameModal.value
                ) {
                    openNameModal();
                }
            } catch (err) {
                // Erro silencioso no polling
                console.error("Erro no polling RFID:", err);
            }
        };

        const openNameModal = () => {
            showNameModal.value = true;
            modalCountdown.value = 15;
            if (modalTimer) clearInterval(modalTimer);
            modalTimer = setInterval(() => {
                modalCountdown.value -= 1;
                if (modalCountdown.value <= 0) {
                    closeNameModal();
                }
            }, 1000);
        };

        const closeNameModal = () => {
            showNameModal.value = false;
            if (modalTimer) {
                clearInterval(modalTimer);
                modalTimer = null;
            }
        };

        const closeRfidBanner = () => {
            showRfidBanner.value = false;
            if (bannerTimer) {
                clearTimeout(bannerTimer);
                bannerTimer = null;
            }
        };

        const submitTagName = async (tagName) => {
            if (!lastRfidUid.value || !tagName) return;
            try {
                await rfidService.nameTag(
                    lastRfidUid.value,
                    tagName,
                    selectedDeviceId.value,
                );
                lastRfidTagName.value = tagName; // Atualiza localmente
                closeNameModal();
            } catch (e) {
                console.error(e);
            }
        };

        const downloadDb = async () => {
            try {
                const blob = await exportService.downloadDatabaseZip();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "raspberry_db_export.zip";
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            } catch (e) {
                console.error(e);
                error.value = "Falha ao exportar banco";
            }
        };

        const selectDevice = async (id) => {
            if (id === selectedDeviceId.value) return;
            selectedDeviceId.value = id;
            externalLedPin.value = 17;

            // Reseta o controle de UIDs ao trocar de dispositivo
            lastSeenUid.value = null;
            lastRfidTimestamp.value = null;

            loading.value = true;
            error.value = null;
            await fetchDeviceDetails(id);
            loading.value = false;
        };

        const filteredRealtimeMessages = computed(() => {
            return realtimeMessages.value.filter(
                (msg) => (msg.raspberry_id || msg.id) == selectedDeviceId.value,
            );
        });

        const normalizeHost = (raw) => {
            if (!raw) return null;
            const cleaned = String(raw)
                .trim()
                .replace(/;|\s|,/g, "");
            if (cleaned.length === 0) return null;
            return cleaned;
        };

        const toggleLED = async (status) => {
            loading.value = true;
            error.value = null;
            try {
                const host = normalizeHost(targetHost.value);
                if (status === "ON") {
                    await ledService.turnOn(
                        "external",
                        selectedDeviceId.value,
                        externalLedPin.value,
                        host,
                    );
                } else {
                    await ledService.turnOff(
                        "external",
                        selectedDeviceId.value,
                        externalLedPin.value,
                        host,
                    );
                }
                await fetchDeviceDetails(selectedDeviceId.value);
            } catch (err) {
                error.value = `Erro ao ${status === "ON" ? "ligar" : "desligar"} LED externo`;
            }
            loading.value = false;
        };

        onMounted(() => {
            fetchAllData();

            console.log(
                "Aguardando 10 segundos antes de iniciar detecção RFID...",
            );
            rfidInitTimeout = setTimeout(() => {
                isRfidInitialized.value = true;
                console.log("Detecção RFID ativada!");
            }, 10000); // 10 segundos

            // Inicia polling geral (mas RFID só responde após 10s)
            refreshTimer = setInterval(() => {
                if (selectedDeviceId.value) {
                    fetchDeviceDetails(selectedDeviceId.value);
                    fetchRealtimeMessages();
                    pollLastRfid(); // Agora com tripla proteção!
                }
            }, 5000);
        });

        onBeforeUnmount(() => {
            if (refreshTimer) clearInterval(refreshTimer);
            if (rfidInitTimeout) clearTimeout(rfidInitTimeout);
            if (modalTimer) clearInterval(modalTimer);
            if (bannerTimer) clearTimeout(bannerTimer);
        });

        return {
            loading,
            error,
            isOnline,
            devices,
            selectedDeviceId,
            selectedDeviceDetails,
            realtimeMessages,
            externalLedPin,
            targetHost,
            filteredRealtimeMessages,
            fetchAllData,
            selectDevice,
            normalizeHost,
            toggleLED,
            downloadDb,
            showRfidBanner,
            lastRfidUid,
            lastRfidTagName,
            lastRfidDisplay,
            showNameModal,
            modalCountdown,
            submitTagName,
            closeNameModal,
            closeRfidBanner,
        };
    },
};
</script>

<style scoped>
section {
    scrollbar-width: thin;
    scrollbar-color: rgba(107, 114, 128, 0.5) transparent;
}

section::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

section::-webkit-scrollbar-thumb {
    background-color: rgba(107, 114, 128, 0.5);
    border-radius: 4px;
}

button {
    transition: background-color 0.3s ease;
}

.chart-container {
    position: relative;
    height: 250px;
    width: 100%;
}
</style>
