# Redutor planetário 1024:1 — V2, com saída por polias 2:1 (total 2048:1)

Versão corrigida do redutor original (`../REDUCAO/`, que não foi alterado). A saída agora passa por polias GT2 20T → 40T até um EIXO de Ø8 paralelo ao motor.

## Arquivos
- `REDUCAO_V2.FCStd`: peças paramétricas do redutor. A planilha **Parametros** controla módulo, dentes e folga, e também o alojamento do 608 da TAMPA.
- `MONTAGEM_V2.FCStd`: montagem (abra junto com `REDUCAO_V2.FCStd`). Inclui:
  - o MANCAL e o EIXO;
  - no grupo `Saida_impressas`: a PLACA_SUPERIOR e os espaçadores;
  - no grupo `Saida_comprados`: os rolamentos e os anéis elásticos, como referência;
  - em `POLIAS_GT2`: as polias e a correia.
- `STL/`: prontos para imprimir (o sufixo `_xN` é a quantidade), já na orientação de impressão.
- `scripts/`:
  - `saida_polias.py` aplica a saída por polias **sobre os arquivos atuais**. Pode rodar de novo: ele refaz só o que ele mesmo criou. Os parâmetros da saída (entre centros, correia, anéis, folga axial) ficam no início dele.
    - A PLACA_SUPERIOR que já existe é **mantida** (você a editou à mão). O script avisa se o alojamento do EIXO não bater com o entre centros.
    - Para testar sem mexer nos arquivos, copie os dois `.FCStd` para outra pasta e rode com `$env:REDUCAO_V2_DIR = "pasta"`.
  - `exporta_stl_saida.py` regrava os STLs das peças da saída.
  - `corrige_visibilidade.py` deixa as peças visíveis ao abrir e devolve as cores (`GuiDocument.xml`), se elas tiverem sumido. O FreeCAD sem interface (`freecadcmd`) não grava essa parte, e o `saida_polias.py` já faz isso sozinho (módulo `visivel.py`). Rode com os arquivos fechados no FreeCAD.
  - `animacao_saida.py` anima o sistema dentro do FreeCAD (veja "Animação" abaixo).
  - `build_v2.py` e `montagem_v2.py` geram o redutor **do zero**. **Não rode esses dois**: eles apagam o MANCAL, o EIXO e as alterações feitas à mão.

Para rodar: `& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" scripts\saida_polias.py`

## Saída por polias
```
        PLACA_SUPERIOR: 608 da SAIDA + 608 do EIXO                    z 88,5..97,5
                                    anel DIN 471 + espaçador 1 mm
   [20T]=====correia 120 (sem tensor)=====[40T]                       z 69..86
        TAMPA: só o 608 da SAIDA (sem aba)                            z 59,4..68,4
   CAIXA + motor                         EIXO Ø8                      z -51..59,4
                                    anel DIN 471 + espaçador 1 mm
        MANCAL: 608 do EIXO, aparafusado na traseira do motor         z -61..-51
                                         EIXO sai 9 mm abaixo (acoplamento)
```
- **SAIDA**: eixo de Ø8 apoiado em dois 608, um na TAMPA e outro na PLACA_SUPERIOR. A polia de 20T fica entre os dois, então a tração da correia não inclina mais o porta-planetas do 5º estágio.
  - Um ressalto de Ø11,5 × 0,4 no disco apoia na pista interna do 608 de baixo.
  - Um espaçador de 2,6 mm prende a pista interna por cima; a 20T aperta contra ele.
  - O rebaixo para o parafuso da 20T fica no lado −x, de z 77,5 a 85.
- **EIXO**: Ø8 × 165,5 mm (aço), apoiado em dois 608, um na PLACA_SUPERIOR e outro no MANCAL, cerca de 140 mm entre eles. A 40T fica entre os dois.
  - **Trava axial cruzada com 2 anéis DIN 471-8**. Cada anel empurra um espaçador de 1 mm (Ø11,5/8,2) que apoia só na pista interna, sem tocar na blindagem do rolamento.
    - O anel de cima, logo acima da 40T, empurra o 608 da PLACA para cima, contra o ressalto da PLACA.
    - O anel de baixo, logo acima do MANCAL, empurra o 608 do MANCAL para baixo, contra o ressalto do MANCAL.
  - Folga axial de projeto: **0,3 mm**, no anel de baixo. Ela absorve a dilatação do PETG em relação ao aço (cerca de 0,1 mm a cada 15 °C) e a tolerância de impressão de PLACA, espaçadores, TAMPA, CAIXA e MANCAL.
  - Ajuste a folga na montagem: se não sobrar folga, lixe o espaçador de 1 mm do MANCAL; se sobrar mais de ~0,5 mm, ponha uma arruela de calço Ø8 (DIN 988, 8 × 14 × 0,1/0,2) sobre o espaçador.
  - Canais no eixo: Ø7,6 × 0,9 mm. Medindo da ponta de baixo, o primeiro fica de 20,2 a 21,1 mm e o segundo de 156,7 a 157,6 mm.
  - O rebaixo para o parafuso M4 da 40T fica de 148,5 a 156 mm (cubo da polia).
- **608**: alojamento de Ø22,2 × 7 (`Drol_ext`, `Hrol`) e ressalto de Ø15 (`D_ressalto`). O ressalto apoia só na pista externa e não raspa na pista interna, que gira.
- **Correia**: GT2 fechada **120 × 6 mm (60 dentes), sem tensor**. O entre centros é fixo, **29,35 mm** (`entre_centros`).
  - O valor nominal para 120 mm é 29,306 mm. Os 0,044 mm a mais esticam a correia cerca de 0,09 mm, uma leve pré-tensão (na ordem de 15–20 N). A flexão das peças impressas absorve parte disso.
  - Abraçamento na 20T: 155°, cerca de 8,6 dentes engrenados.
  - Se a correia ficar frouxa e pular dente sob carga, ou justa demais para montar, mude `C` no `saida_polias.py`, rode de novo e reimprima PLACA_SUPERIOR e MANCAL. Cada 0,1 mm de C muda o comprimento em cerca de 0,2 mm.
  - Se mais tarde for preciso um tensor, o `build_polias.py` ainda calcula (`IDLER_X`), mas aí C tem que ficar abaixo do nominal.
- **TAMPA**: sem a aba e sem o alojamento do EIXO, só o octógono do motor (42 × 42) com o 608 da SAIDA. Os 4 parafusos do motor viram barras roscadas M3 que seguram também a PLACA.
- **PLACA_SUPERIOR**: leva 2 rolamentos 608, o da SAIDA e o do EIXO; o do EIXO fica num braço de raio 16.
  - É presa à TAMPA por 4 espaçadores de 21,6 mm, um em cada canto do motor, encaixados no escareado da TAMPA.
- **MANCAL**: aparafusado na traseira do motor pelos 4 furos de ±15,5. Os 4 parafusos traseiros do NEMA17 são trocados por outros 10 mm mais longos. Não há pilares.
  - O MANCAL leva só cerca de 13% da força da correia: a 40T fica perto da PLACA, então o 608 de lá leva o resto.
  - O alinhamento entre os dois 608 do EIXO depende da cadeia MANCAL → motor → CAIXA → TAMPA → espaçadores → PLACA. Antes de pôr a correia, veja se o EIXO gira livre.

### Compras da saída
| Item | Qtd |
|---|---|
| Rolamento 608ZZ (8×22×7) | 4 |
| Polia GT2 20T furo 8 mm, largura 6 | 1 |
| Polia GT2 40T furo 8 mm, largura 6 | 1 |
| Correia GT2 fechada 120 × 6 mm (60 dentes) | 1 |
| Eixo Ø8 mm × 165,5 mm (aço retificado), com 2 canais Ø7,6 × 0,9 (feitos no torno) | 1 |
| Anel elástico externo DIN 471 – 8 × 0,8 (Seeger) | 2 (+ reserva) |
| Arruela de calço DIN 988 8 × 14 × 0,1 e 0,2 (opcional, para ajustar a folga) | algumas |
| Barra roscada M3 × ~108 mm + porca (no lugar dos 4 M3 × 75 da TAMPA) | 4 |
| Parafuso M3 10 mm mais longo que os 4 da traseira do motor (para prender o MANCAL) | 4 |
| Alicate de anel externo (ponta reta, pequeno) | ferramenta |

Os comprimentos das barras e dos parafusos dependem do seu motor: meça os parafusos originais antes de comprar.

### Ordem de montagem da saída
1. Prense os 608: 1 na TAMPA (SAIDA), 1 no MANCAL e 2 na PLACA_SUPERIOR.
2. Monte o redutor como antes, com as 4 barras roscadas no lugar dos parafusos do motor. O ressalto da SAIDA encosta na pista interna do 608 da TAMPA.
3. **SAIDA**: coloque o espaçador de 2,6 mm e a 20T, com um parafuso sobre o rebaixo. Empurre a polia contra o espaçador e aperte.
4. **MANCAL**: troque os 4 parafusos traseiros do motor, um de cada vez, pelos mais longos, prendendo o MANCAL. Não solte os 4 ao mesmo tempo, para a tampa traseira do motor não sair do lugar.
5. **EIXO**:
   1. Ponha o anel no canal de baixo do EIXO. Enfie o espaçador de 1 mm pela ponta de baixo até encostar no anel.
   2. Desça o EIXO, por cima, pelo 608 do MANCAL, até o espaçador encostar na pista interna.
   3. Enfie a 40T por cima do EIXO, sem apertar, e o anel no canal de cima.
6. Ponha a correia nas duas polias e os 4 espaçadores nas barras do motor. Coloque o espaçador de 1 mm no topo do EIXO e desça a PLACA (os 608 entram na SAIDA e no EIXO).
7. Aperte as porcas das 4 barras por igual. Confira a folga axial do EIXO (cerca de 0,3 mm; veja acima como ajustar) e se ele gira livre.
8. Alinhe a 40T com a 20T pela correia e aperte os parafusos da 40T sobre o rebaixo.

## Animação (FreeCAD com interface)
O script `scripts/animacao_saida.py` mostra o sistema girando: o sol do motor, os 5 estágios (suportes, sóis e planetas, que orbitam e giram em torno de si), a SAIDA, as polias, o EIXO e a correia, com os dentes correndo pelo percurso.

Como rodar:
1. Abra `MONTAGEM_V2.FCStd` no FreeCAD. O `REDUCAO_V2.FCStd` abre junto.
2. Menu **Macro → Macros…**. Em "Local das macros do usuário", aponte para a pasta `scripts`, escolha `animacao_saida.py` e clique em **Executar**. Outra opção: abra o arquivo (Arquivo → Abrir) e use **Macro → Executar macro** (Ctrl+F6).
3. Um painel aparece à direita. Nele você tem:
   - a rotação do motor (escala logarítmica de 0,1 a 100 000 rpm) e atalhos: **Sideral** (≈1,43 rpm no motor, o EIXO dá 1 volta por dia sideral), 60 rpm, 600 rpm e **EIXO a 1 rpm** (2048 rpm no motor);
   - os botões **Iniciar/Pausar**, **Inverter sentido** e **Zerar**;
   - **Esconder carcaça**, que já vem marcado: esconde CAIXA, TAMPA, PLACA, MANCAL e motor para mostrar as engrenagens;
   - **Correia andando**: desmarque para mostrar a correia original, parada. Ao abrir, o painel leva 1 a 2 s para preparar 12 posições da correia dentro de 1 dente;
   - quanto cada estágio já girou e o ângulo do EIXO (em graus e minutos de arco).
4. Clique em **Fechar e restaurar** ou no X do painel para devolver todas as peças à posição original.

O que é importante saber:
- **Não salve com a animação aberta.** Ela move as peças de verdade (mexe no Placement) e cria uma correia temporária.
- Em rotações altas, o sol do motor parece parado ou girando ao contrário. É efeito estroboscópico da taxa de quadros (~30 por segundo), não erro. Para ver a saída se mexer, use **EIXO a 1 rpm**. Em velocidade sideral, só o primeiro estágio se mexe de forma visível.
- A cinemática usa a coroa da CAIXA parada. Lê os dentes na planilha `Parametros` e acha as peças pelo nome (`SOL_MOTOR`, `SUPORTE_k`, `SOL_k`, `PLANETA_k_j`, `SAIDA`, `POLIA_GT2_*`, `EIXO`…). Se você renomear peças, ajuste o script.

## O que mudou em relação ao original (redutor)
| Item | Original | V2 |
|---|---|---|
| Engrenagens | 9 dentes, módulo 1,2 (coroa 27 dentes, módulo 1,23) | 12 dentes, módulo 0,9 (coroa 36 dentes, mesmo módulo); mesmo diâmetro externo |
| Raio dos pinos | 10,5 mm (o sol prendia) | 10,8 mm = distância correta entre sol e planeta |
| Coroa | cavidade de engrenagem externa | engrenagem interna real, adendo de 0,55·m |
| Folga | variava de 0 a 0,2 mm conforme a posição | constante: 0,053 mm por engrenamento (`desloc_planeta = -0,08`) |
| Furo do planeta | 5,5 mm no pino de 5 | 5,2 mm |
| Saída | eixo de 10 mm num furo de 10,5 (plástico) | eixo de Ø8 em 608 na TAMPA e na PLACA_SUPERIOR + polias 2:1 |
| Redução | 4⁵ = 1024 | 4⁵ × 2 = 2048 |

## Folga estimada na saída do redutor (só geometria do CAD)
- `desloc_planeta = -0,08` → cerca de 22′ na SAIDA. Depois das polias, o efeito no EIXO cai à metade, mais a folga da correia.
- `desloc_planeta = -0,05` → cerca de 14′ na SAIDA (se a impressora for bem calibrada).
- Impresso, o valor real depende da calibração. Meça com o teste do laser (1′ ≈ 1,5 mm a 5 m).

## Dicas de impressão
- PETG ou ASA; engrenagens deitadas, 100% de preenchimento (ou ≥ 4 paredes), camada de 0,12–0,16 mm.
- **SAIDA**: o eixo de Ø8 transmite todo o torque e leva o parafuso da 20T. Imprima com 100% de preenchimento.
- **608**: imprima antes um anel de teste com o alojamento de Ø22,2. O rolamento deve entrar com pressão leve. Se ficar justo ou folgado, mude `Drol_ext` (a TAMPA se atualiza sozinha). No MANCAL e na PLACA, mude também o valor em `saida_polias.py` (`DROL`) e rode o script de novo.
- **PLACA_SUPERIOR**: o STL já vem virado (alojamento para cima).
- Imprima primeiro 1 SOL + 3 PLANETAS + 1 SUPORTE + um anel curto da coroa para testar o encaixe.
- Lubrifique as engrenagens com graxa de PTFE ou silicone.

## Limitações conhecidas
- O acoplamento do EIXO com o eixo do telescópio ainda não foi feito: o CUBO da `MONTAGEM_EQ` ainda tem o sextavado antigo. Esse acoplamento deve transmitir só torque, sem carga axial.
- `../MONTAGEM_EQ/MOTORIZACAO.FCStd` é uma cópia estática antiga (sem MANCAL e com o EIXO em outra posição).
- O SOL_MOTOR reaproveita o cubo do original como peça fixa (não paramétrica).
- No FreeCAD, as engrenagens são editadas pelo painel de propriedades (o duplo clique não abre o diálogo de engrenagem).
