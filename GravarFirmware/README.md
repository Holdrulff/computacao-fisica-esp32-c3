# Gravar Firmware no ESP32-C3

## Instalação do MicroPython

Para instalar MicroPython no ESP32-C3 Supermini, siga as instruções oficiais em:
https://micropython.org/download/ESP32_GENERIC_C3/

## Passos Básicos

```bash
# 1. Apagar flash existente
esptool --port /dev/ttyACM0 erase_flash

# 2. Gravar firmware MicroPython
esptool --port /dev/ttyACM0 write_flash 0 ESP32_GENERIC_C3-20251209-v1.27.0.bin
```

**Windows**: Substitua `/dev/ttyACM0` por `COM3` (ou a porta serial correspondente)

## Erros Comuns e Soluções

### Erro de Comunicação ao Gravar

**Sintoma**: Erro "stop interaction" durante execução de `esptool --port /dev/ttyACM0 erase_flash`

![](./Captura%20de%20tela%20de%202026-01-31%2010-22-37.png)

**Causa**: Problemas de comunicação serial com o ESP32-C3

**Solução Testada**:

1. Abra o Arduino IDE
2. Configure para programar ESP32:
   - Vá em **Tools → Board → ESP32 Arduino → ESP32C3 Dev Module**
3. Selecione a porta serial correta
4. Carregue um sketch básico (bare minimum):
   ```cpp
   void setup() {
     // Empty
   }

   void loop() {
     // Empty
   }
   ```
5. Clique em **Upload** e aguarde conclusão
6. Após upload bem-sucedido no Arduino IDE, execute novamente:
   ```bash
   esptool --port /dev/ttyACM0 erase_flash
   ```

**Resultado**: O comando `esptool` geralmente funciona sem erros após essa sequência.

## Verificação da Instalação

Após gravar o firmware, teste a instalação:

```bash
# Conecte ao REPL do MicroPython
mpremote connect /dev/ttyACM0

# Você deve ver o prompt do MicroPython:
>>>
```

Teste básico:

```python
>>> import sys
>>> print(sys.version)
3.4.0; MicroPython v1.27.0 on 2024-12-09

>>> import machine
>>> print(machine.unique_id())
```

## Notas Importantes

- **Sempre use cabo USB com suporte a dados** (não apenas carga)
- **ESP32-C3 requer drivers**: No Windows, pode ser necessário instalar drivers CH340/CP2102
- **Porta serial**: Linux geralmente usa `/dev/ttyACM0` ou `/dev/ttyUSB0`, Windows usa `COM3`, `COM4`, etc.
- **Permissões no Linux**: Adicione seu usuário ao grupo `dialout`:
  ```bash
  sudo usermod -a -G dialout $USER
  # Faça logout e login novamente
  ```

## Firmware Recomendado

Use sempre a versão estável mais recente disponível em:
- https://micropython.org/download/ESP32_GENERIC_C3/

**Versão testada neste projeto**: `ESP32_GENERIC_C3-20251209-v1.27.0.bin`

## Troubleshooting Adicional

### Erro: "Failed to connect"

```bash
# Tente segurar o botão BOOT enquanto conecta o USB
# Depois execute:
esptool --port /dev/ttyACM0 --before default_reset erase_flash
```

### Erro: "Permission denied" (Linux)

```bash
# Dê permissão para a porta serial
sudo chmod 666 /dev/ttyACM0

# Ou adicione permanentemente ao grupo dialout (recomendado)
sudo usermod -a -G dialout $USER
```

### ESP32 não responde após gravação

```bash
# Pressione o botão RESET físico na placa
# Ou desconecte e reconecte o cabo USB
```

---

**Última atualização**: Março 2026
**Firmware testado**: MicroPython v1.27.0
**Hardware**: ESP32-C3 Supermini
