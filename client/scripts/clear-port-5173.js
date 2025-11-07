#!/usr/bin/env node

/**
 * Script para limpar a porta 5173 antes de iniciar o Vite
 * Mata qualquer processo node/vite/npm que esteja usando a porta 5173
 */

import { execSync } from 'child_process';

const PORT = 5173;

try {
  // Verifica se há algo na porta 5173
  console.log(`[Clear Port] Verificando se a porta ${PORT} está em uso...`);
  
  try {
    // Usa ss para encontrar processos na porta 5173
    const result = execSync(
      `ss -tlnp 2>/dev/null | grep ':${PORT}' | grep LISTEN`,
      { encoding: 'utf-8', stdio: 'pipe' }
    ).trim();
    
    if (result) {
      // Extrai o PID do processo
      const pidMatch = result.match(/pid=(\d+)/);
      if (pidMatch) {
        const pid = pidMatch[1];
        
        // Verifica se é processo node/vite/npm
        try {
          const procName = execSync(
            `ps -p ${pid} -o comm= 2>/dev/null`,
            { encoding: 'utf-8', stdio: 'pipe' }
          ).trim().toLowerCase();
          
          if (procName.includes('node') || procName.includes('vite') || procName.includes('npm')) {
            console.log(`[Clear Port] Processo encontrado na porta ${PORT} (PID ${pid}, ${procName})`);
            console.log(`[Clear Port] Matando processo ${pid}...`);
            
            // Mata o processo
            execSync(`kill -9 ${pid} 2>/dev/null`, { stdio: 'pipe' });
            
            // Aguarda um pouco para o processo ser finalizado (usando execSync com sleep)
            try {
              execSync(`sleep 0.5`, { stdio: 'pipe' });
            } catch {
              // Se sleep não funcionar, continua mesmo assim
            }
            
            console.log(`[Clear Port] ✓ Porta ${PORT} liberada com sucesso`);
          } else {
            console.log(`[Clear Port] Porta ${PORT} está em uso por ${procName}, mas não é node/vite/npm. Ignorando.`);
          }
        } catch (err) {
          // Se não conseguir verificar o nome do processo, tenta matar mesmo assim
          console.log(`[Clear Port] Matando processo ${pid} na porta ${PORT}...`);
          execSync(`kill -9 ${pid} 2>/dev/null`, { stdio: 'pipe' });
          try {
            execSync(`sleep 0.5`, { stdio: 'pipe' });
          } catch {
            // Continua mesmo se sleep falhar
          }
          console.log(`[Clear Port] ✓ Porta ${PORT} liberada`);
        }
      }
    } else {
      console.log(`[Clear Port] Porta ${PORT} está livre`);
    }
  } catch (err) {
    // Se ss não encontrar nada, a porta está livre
    if (err.status === 1) {
      console.log(`[Clear Port] Porta ${PORT} está livre`);
    } else {
      console.log(`[Clear Port] Aviso ao verificar porta: ${err.message}`);
    }
  }
} catch (error) {
  console.error(`[Clear Port] Erro ao limpar porta ${PORT}:`, error.message);
  // Não falha o script, apenas avisa
}

