"""
Handler RFID para Raspberry Pi 5
Gerencia leitura de tags RFID e persiste dados
"""

import threading
import json
from datetime import datetime
from typing import Optional, Callable
from database import SessionLocal, RFIDTag, RFIDReadHistory, DeviceStatus
import socket

try:
    from pirc522 import RFID
    RFID_AVAILABLE = True
except ImportError:
    RFID_AVAILABLE = False
    print("pirc522 não disponível - rodando em modo simulação")

class RFIDHandler:
    """Handler para gerenciar sensor RFID"""
    
    def __init__(self, raspberry_id: Optional[str] = None):
        self.raspberry_id = raspberry_id or socket.gethostname()
        self.reader = None
        self.util = None
        self.running = False
        self.read_callback: Optional[Callable] = None
        
        if RFID_AVAILABLE:
            try:
                self.reader = RFID()
                self.util = self.reader.util()
                self.util.debug = False
                print(f"[RFID] Sensor inicializado com sucesso para {self.raspberry_id}")
            except Exception as e:
                print(f"[RFID] Erro ao inicializar: {e}")
                self.reader = None
    
    def set_read_callback(self, callback: Callable):
        """Define função callback para quando uma tag for lida"""
        self.read_callback = callback
    
    def load_tag_name(self, uid_str: str) -> str:
        """Carrega nome da tag do banco de dados"""
        db = SessionLocal()
        try:
            tag = db.query(RFIDTag).filter(RFIDTag.uid == uid_str).first()
            if tag:
                return tag.name
            return "<Sem nome>"
        finally:
            db.close()
    
    def save_tag_name(self, uid_str: str, name: str) -> bool:
        """Salva ou atualiza nome da tag"""
        db = SessionLocal()
        try:
            tag = db.query(RFIDTag).filter(RFIDTag.uid == uid_str).first()
            if tag:
                tag.name = name
                tag.updated_at = datetime.utcnow()
            else:
                tag = RFIDTag(
                    uid=uid_str,
                    name=name,
                    raspberry_id=self.raspberry_id
                )
                db.add(tag)
            db.commit()
            return True
        except Exception as e:
            print(f"[RFID] Erro ao salvar tag: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def record_read(self, uid_str: str, tag_name: str) -> bool:
        """Registra leitura RFID no histórico"""
        db = SessionLocal()
        try:
            read = RFIDReadHistory(
                uid=uid_str,
                tag_name=tag_name,
                raspberry_id=self.raspberry_id,
                timestamp=datetime.utcnow()
            )
            db.add(read)
            
            # Atualizar last_rfid_read no DeviceStatus
            device = db.query(DeviceStatus).filter(
                DeviceStatus.raspberry_id == self.raspberry_id
            ).first()
            if device:
                device.last_rfid_read = datetime.utcnow()
                device.rfid_reader_status = "online"
            db.commit()
            return True
        except Exception as e:
            print(f"[RFID] Erro ao registrar leitura: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def read_tag(self) -> Optional[dict]:
        """Lê uma tag RFID e retorna dados"""
        if not self.reader:
            return None
        
        try:
            self.reader.wait_for_tag()
            (error, data) = self.reader.request()
            if error:
                return None
            
            (error, uid) = self.reader.anticoll()
            if error:
                return None
            
            uid_str = "-".join(f"{x:02X}" for x in uid)
            self.util.set_tag(uid)
            
            # Carregar nome salvo
            tag_name = self.load_tag_name(uid_str)
            
            # Registrar leitura
            self.record_read(uid_str, tag_name)
            
            result = {
                "uid": uid_str,
                "tag_name": tag_name,
                "raspberry_id": self.raspberry_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Executar callback se configurado
            if self.read_callback:
                self.read_callback(result)
            
            return result
        except Exception as e:
            print(f"[RFID] Erro ao ler tag: {e}")
            return None
    
    def start_polling(self, interval: float = 0.5):
        """Inicia polling contínuo de tags RFID em thread separada"""
        if not self.reader:
            print("[RFID] Sensor não disponível")
            return
        
        self.running = True
        
        def polling_thread():
            print("[RFID] Thread de polling iniciada")
            while self.running:
                try:
                    import time
                    time.sleep(interval)
                    self.read_tag()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[RFID] Erro no polling: {e}")
        
        thread = threading.Thread(target=polling_thread, daemon=True)
        thread.start()
    
    def stop_polling(self):
        """Para o polling de tags"""
        self.running = False
        if self.reader:
            try:
                self.reader.cleanup()
            except:
                pass
    
    def set_rfid_status(self, status: str):
        """Atualiza status do leitor RFID no DeviceStatus"""
        db = SessionLocal()
        try:
            device = db.query(DeviceStatus).filter(
                DeviceStatus.raspberry_id == self.raspberry_id
            ).first()
            if device:
                device.rfid_reader_status = status
                db.commit()
        except Exception as e:
            print(f"[RFID] Erro ao atualizar status: {e}")
        finally:
            db.close()

# Instância global
_rfid_handler: Optional[RFIDHandler] = None

def init_rfid_handler(raspberry_id: Optional[str] = None) -> RFIDHandler:
    """Inicializa o handler global RFID"""
    global _rfid_handler
    _rfid_handler = RFIDHandler(raspberry_id)
    return _rfid_handler

def get_rfid_handler() -> Optional[RFIDHandler]:
    """Retorna a instância global do handler RFID"""
    return _rfid_handler

def cleanup_rfid():
    """Limpa recursos do RFID"""
    global _rfid_handler
    if _rfid_handler:
        _rfid_handler.stop_polling()
        _rfid_handler = None

