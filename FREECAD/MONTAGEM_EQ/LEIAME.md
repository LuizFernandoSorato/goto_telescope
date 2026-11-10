# Montagem equatorial impressa (GEM) — Greika 70070 + redutores 1024:1

## Revisão 3 — `MONTAGEM_EQ_V3.FCStd` (atual)
É a montagem que você desenhou na V2: dois redutores V2 com saída por polias, com o EIXO Ø8 servindo de eixo RA e de eixo DEC. As correções foram aplicadas por script, e a V2 não foi alterada.
- `scripts/revisao3.py` gera a V3 a partir da V2. A latitude é `$env:LAT = "28.5"` e a barra do contrapeso é `$env:L_BARRA_CW = "250"`. Ele grava também os STLs em `STL_V3/` e o resumo em `scripts/revisao3_relatorio.txt`.
- `scripts/verifica_v3.py` confere interferências, folgas, balanceamento, cargas e colisões girando RA e DEC. Leva ~8 min.
- `scripts/anima_montagem.py` é a animação do movimento real: GoTo, acompanhamento sideral, meridian flip e a passagem da ISS. Veja a seção "Animação" abaixo.
- `scripts/eq_massas.py` guarda as massas estimadas. Depois de pesar as peças de verdade, ajuste os valores aqui.

Para rodar (PowerShell, na pasta `MONTAGEM_EQ`):
```
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" scripts\revisao3.py
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" scripts\verifica_v3.py
```

### O que mudou em relação à V2
| Item | V2 | V3 |
|---|---|---|
| Peças duplicadas | 43 cópias sobrepostas em cada redutor | apagadas |
| ACOPLADOR1/2 (eixo → carga) | placa 5 mm, cubo Ø16 × 5, furo D com 8 mm de encaixe | placa 6 mm, cubo cônico Ø28→Ø22 × 16,5 mm, furo D Ø8,15 com **20 mm** de encaixe, parafuso de trava M3 sem cabeça (com porca embutida) contra a face plana do eixo, furos M3 Ø3,4 |
| EIXO Ø8 (os dois) | 165,5 mm | **178 mm**, com face plana de 0,5 mm nos últimos 21 mm da ponta do MANCAL |
| Folga entre o acoplador (que gira) e o mancal (fixo) | 0,98 mm e 1,62 mm | 2,0 mm |
| Tubo no DEC | sapata direto no acoplador, 43 mm fora de balanço | **sela Vixen** (`SELA_DEC`) + barra Vixen de 200 mm: o tubo desliza para balancear |
| Contrapeso | não havia | `TAMPA_CW` + barra M12 de 250 mm + copo impresso Ø80 × 50 cheio de esferas de aço |
| Latitude | 27,0° (fixa no modelo) | **28,5°**, no pivô e no arco da BASE (o arco cobre ~−4° a 78°) |
| ACOPLADOR3 × MANCAL RA | invadia 0,66 mm | encostado |
| BASE | haste do ACOPLADOR3 sem folga; parafuso do tripé sem furo | vão de 10,5 mm (0,25 mm de cada lado) e furo Ø5,2 para abrir rosca 1/4"-20 |
| Tripé (no modelo) | perna 1 embaixo do contrapeso | girado 60°: **uma perna apontando para o norte**, e o contrapeso fica entre as duas pernas do lado sul |

### Verificação (`verifica_v3.py`)
- **Eixos:** RA a 28,50°, perpendicular ao DEC (90,00°), e os dois se cruzam (distância 0,000 mm).
- **Interferências:** nenhuma entre conjuntos. A única é o parafuso 1/4" do tripé dentro do furo da BASE, onde fica a rosca.
- **Folgas:** acopladores a 2,0 mm dos mancais, 0,25 mm de cada lado da haste do ACOPLADOR3 e 2,0 mm entre a TAMPA_CW e o EIXO/SAIDA DEC, que giram.
- **Balanceamento** (com as massas estimadas):
  - DEC: 1,74 kg, centro de massa a 0,13 mm do eixo.
  - RA: 2,95 kg, centro de massa a 0,06 mm do eixo.
  - Os dois ficam abaixo de 0,01 N·m.
- **Contrapeso:**
  - Copo, tampa, 2 porcas e ~320 g de esferas de aço somam ~400 g, a ~330 mm do cruzamento dos eixos.
  - O copo cheio leva ~840 g, então sobra para câmera.
  - Cada +100 g no tubo pede +~40 g no copo, e 1 cm de deslocamento do copo vale 0,035 N·m.
- **Cargas:**
  - 608 do MANCAL RA: 40 N. 608 da PLACA RA: 14 N.
  - Flexão no eixo RA: 2,1 N·m, ~41 MPa no aço Ø8. No DEC: 30 MPa.
  - Tudo folgado. Use aço prata ou retificado, não alumínio.
- **Colisões:**
  - O DEC dá a volta inteira livre.
  - O RA fica livre até ±135°. A ±150° o tubo bate na BASE e na cabeça do tripé.
  - **Limite no firmware: ±120°.**

### Torque e balanceamento na prática
O ponto fraco do acionamento é a correia GT2 6 mm na polia 20T, sem tensor. O EIXO aguenta cerca de **0,3 a 0,5 N·m** antes de a correia pular dentes. Por isso:
1. **DEC:** solte os 2 M6 da sela, deixe o tubo na horizontal e deslize até ele ficar parado sozinho. Aperte.
2. **RA:** deixe o DEC na horizontal (contrapeso para o lado). Ajuste o copo na barra ou a quantidade de esferas até o conjunto ficar parado em qualquer ângulo. Depois deixe um pouco mais pesado para o leste (1 a 2 cm do copo), assim as engrenagens trabalham sempre encostadas do mesmo lado.
3. Limite a corrente do motor. Com 2048:1 ele tem força para quebrar dentes se a montagem bater em algo.

### Lista de compras da V3
| Item | Qtd | Uso |
|---|---|---|
| Barra Vixen (cauda de andorinha) 200 mm | 1 | tubo ↔ sela. Prenda na SAPATA com 2 parafusos a 60 mm (confira a rosca dos furos da sapata) |
| Parafuso M6 × 16 + porca M6 | 2 | aperto da sela (porca embutida) |
| Parafuso M3 × 14 + porca M3 | 4 | SELA_DEC → ACOPLADOR2 (cabeça embutida na sela, porca no acoplador) |
| Parafuso M3 × 20 + porca M3 | 8 | ACOPLADOR1 → MANCAL DEC e ACOPLADOR3 → MANCAL RA |
| Parafuso M3 × 8 sem cabeça (grub) + porca M3 | 2 | trava dos acopladores na face plana do eixo |
| Eixo de aço Ø8 × 178 mm | 2 | RA e DEC. Canais dos anéis DIN 471 como no REDUCAO_V2, mais uma face plana de 0,5 mm × 21 mm na ponta do MANCAL |
| Barra roscada M12 × 250 mm + 4 porcas M12 | 1 | contrapeso: 1 porca presa na TAMPA_CW, 1 de trava e 2 apertando o copo |
| Esferas de aço (BB 4,5 mm) ou chumbinho | ~0,35 kg (até 0,8) | enchimento do copo. Com chumbinho de chumbo, cabe ~1,2 kg |
| Barras roscadas M3 do redutor DEC | 4 | 8 mm mais longas: as porcas passam para cima da TAMPA_CW |
| Parafuso M5 × 35 + porca (ou manípulo) | 2 | pivô e trava de latitude (BASE ↔ ACOPLADOR3) |
| Macho 1/4"-20 (ou inserto de 1/4") | 1 | rosca do tripé na BASE |

### Impressão (STL_V3)
- `ACOPLADOR1`, `ACOPLADOR2`, `ACOPLADOR3`, `SELA_DEC`, `TAMPA_CW`, `BASE`: são estruturais. Use **5 paredes, 50% gyroid** e imprima com a placa na mesa, sem suporte.
- `CONTRAPESO_COPO` e `CONTRAPESO_TAMPA`: 3 paredes e 20% bastam. Encha o copo, encaixe a tampa (tem um ressalto) e prenda os dois com as 2 porcas M12.
- Antes, imprima um furo D de teste: o eixo, já com a face plana, deve entrar justo, sem forçar. Para ajustar, mude `D_FURO`/`PLANO_FURO` no `revisao3.py`.
- O parafuso de trava fica do lado da face plana. Monte o eixo com a face plana virada para ele.

### Animação do movimento real (`scripts/anima_montagem.py`)
A animação mostra o telescópio fazendo GoTo e acompanhando o céu, com as engrenagens e as correias dos dois redutores girando juntas.
1. Abra `MONTAGEM_EQ_V3.FCStd` no FreeCAD.
2. Em **Macro → Macros…**, aponte para a pasta `scripts`, escolha `anima_montagem.py` e clique em **Executar**.
3. Espere uns 20 s, enquanto ele prepara as correias. O painel "Movimento da montagem" abre à direita.

No painel:
- **Alvo + GoTo:** são cerca de 20 estrelas e objetos do céu do sul (Cruzeiro, Alfa Centauri, Eta Carinae, Órion, as Nuvens de Magalhães…).
  - Os dois eixos giram na velocidade de GoTo, que é a rotação do motor ÷ 2048. Com 600 rpm no motor, dá 1,76°/s no eixo.
  - Depois o RA passa a acompanhar o céu a 15°/h. Isso dá 1,43 rpm no motor.
  - A linha amarela sai da objetiva e aponta para onde está o alvo.
- **ISS — passagem de 10/11 14:55:** é o segundo item da lista. A órbita sai do TLE da Celestrak (`TLE_ISS` no topo do script), propagada por Kepler + J2 + arrasto.
  - Com GoTo, o tempo volta para 90 s antes de a ISS nascer. A montagem vai até o ponto onde ela aparece (SO), espera, acompanha a passagem e para quando ela some (NE). O tempo fica em ×1, mas pode ser acelerado.
  - O painel e a janela Report view mostram o resumo: nascimento, máximo e ocaso; velocidade máxima de cada eixo e rpm do motor; horário do meridian flip.
  - Em lat −28,5° e lon −49,0°, a passagem nasce às 14:53:03 no SO, chega a 79,9° às 14:58:31 no NO e some às 15:04 no NE. Com lon −49,2°, o máximo dá 82,0°.
  - Velocidade máxima: RA 0,87°/s (~300 rpm no motor) e DEC 0,71°/s (~240 rpm). O GoTo a 600 rpm dá 1,76°/s, então a montagem acompanha com folga.
  - Essa passagem força **um meridian flip** às 14:59:51, com a ISS a 34° descendo para o NE. A volta leva ~90 s e a ISS é retomada a 13°.
  - Para outra passagem: cole um TLE novo (vale ~2 dias) em `TLE_ISS` e mude `PASSAGEM_ISS` (hora local do PC, qualquer minuto dentro da passagem).
  - A propagação simplificada erra ~1° numa passagem alta. Serve para a animação; para apontar de verdade, use SGP4 completo e relógio sincronizado.
- **Hora:** a hora sideral vem do relógio do PC e da **longitude** (padrão −49°; ajuste para o seu local).
- **Tempo:** acelera de ×1 a ×3600. Em ×1200, uma hora passa em 3 s. A aceleração vale também para o GoTo.
- **Meridian flip:** se o acompanhamento levar o RA além de ±120° (o limite do firmware), a montagem troca o tubo de lado. Isso acontece cerca de 2 h depois de o alvo passar pelo meridiano. Alvos abaixo do horizonte não são seguidos.
- **RA± / DEC±:** movimento manual enquanto o botão estiver apertado.
- **Estacionar:** volta o tubo para o polo, com o contrapeso para baixo.
- **Ver engrenagens:** esconde as caixas, tampas e mancais dos redutores.
- **Texto:** mostra o estado, a altura e o azimute do tubo e do alvo, o ângulo horário, o erro de apontamento e as voltas de cada motor.
- **Fechar e restaurar:** volta tudo à posição original e apaga os objetos temporários (`ANIM_*`).

Detalhes técnicos:
- As peças só se movem na tela, pelo nó Coin de cada uma. Os `Placement` do documento não mudam.
- Ainda assim, **não salve com a animação aberta**: as correias e a linha temporárias iriam junto.
- Cada quadro leva cerca de 150 a 350 ms, a maior parte para desenhar o modelo inteiro.
- Em velocidade alta, as engrenagens rápidas parecem paradas ou girando ao contrário. É o efeito estroboscópico.
- Na posição de estacionamento, com o contrapeso para baixo, girar só o DEC leva o tubo pelo círculo horário de 6 h. Por isso, no meridiano, o RA fica perto de ±90°, com a barra do contrapeso na horizontal. Numa GEM isso é normal.

### Limitações
- As massas do tubo e das peças são estimadas (`eq_massas.py`). O balanceamento final é na prática, e por isso a sela e o copo são ajustáveis.
- O motor e o cabo do DEC giram junto com o RA: deixe uma alça folgada.
- A folga angular (engrenagens impressas + correia) se nota mais no DEC. Use guiagem com compensação de folga (*backlash*).

---
## Versão 1 (`MONTAGEM_EQ.FCStd`, gerada por `build_eq.py`)

Equatorial alemã impressa em PETG para latitude **−28,5°** (faixa de ajuste: ~16° a 34°), com carga de 1,5 kg (tubo). Os dois redutores V2 (`../REDUCAO_V2/`) ficam **presos direto nos eixos**: a saída sextavada do redutor encaixa no cubo de aperto do eixo, e um braço anti-giro, preso na carcaça do redutor, corre num canal da extensão. Não tem embreagem.

## Arquivos
- `MONTAGEM_EQ.FCStd` — montagem completa com as peças agrupadas por movimento (Fixo_tripe, Fixo_corpo_AR, Gira_AR, Gira_AR_corpo_DEC, Gira_DEC) e os itens comprados de referência (eixos, rolamentos, redutores, barra, contrapeso e tubo).
- `STL/` — peças para imprimir, já na orientação de impressão (o sufixo `_xN` é a quantidade).
- `scripts/build_eq.py` — gera tudo. Os parâmetros estão no topo; `LAT=30` muda a latitude. Rodar com:
  `"C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" scripts\build_eq.py`
  O script relata as massas, o contrapeso, a faixa de latitude e as interferências, e regrava os STLs.

## Como funciona
```
            tubo 70070
        ===================
             SELA (Vixen)
               |  eixo DEC Ø25
  [EXT_DEC + redutor]==CORPO_DEC==   ← o redutor DEC fica do lado do contrapeso
       barra M12 → anilha        \
                                  eixo AR Ø25 (aponta para o polo sul, 28,5° acima do horizonte)
                                  CORPO_AR (2× 6805)
                                  quilha + pivô M8 entre as bochechas da CUNHA
                                  [EXT_AR + redutor AR] pendurado para o norte
         CUNHA (gira em azimute) / BASE (rosca 1/4" do tripé)
```
- **Cada eixo**: um tubo de alumínio Ø25 em 2 rolamentos 6805-2RS, que ficam no CORPO (afastados 83 mm). O CUBO aperta o eixo e encosta na pista interna do rolamento de baixo; do outro lado, o cubo da peça seguinte (corpo DEC ou sela) encosta na pista interna do rolamento de cima. Isso trava a folga axial.
- **Acionamento**: o redutor fica dentro da EXT, que é aparafusada no flange do corpo. A saída sextavada entra no CUBO, e os 2 rolamentos 6700 da TAMPA do redutor sustentam o peso do motor. O COLAR abraça a caixa octogonal; a orelha dele entra no canal da EXT e o parafuso M3 lateral zera a folga (aperte só até encostar).
- **Latitude**: a quilha do CORPO_AR gira no pivô M8. A quina norte da quilha apoia na RODA_LAT (porca M6 numa barra roscada M6), e a trava M6 corre no arco das bochechas. O centro de gravidade fica 18 mm ao norte do pivô, então o peso sempre apoia na roda: solte a trava, gire a roda e aperte de novo.
- **Azimute**: a CUNHA gira sobre a BASE (centralizada no ressalto Ø40). Os 2 parafusos M5 horizontais das colunas empurram o bloco da roda (±3,5°). Os 2 M5 verticais nos rasgos em arco travam a cunha.

## Verificações feitas (no script)
- **0 interferências** dentro de cada conjunto e entre as partes móveis, com AR de −120° a +120° (em passos de 30°) e DEC 0/90/180/270.
- Latitude de 16,5° a 40,5°: o corpo AR não toca a cunha. A roda de ajuste cobre de ~16° a ~34°.
- **Limite para o firmware (OnStep etc.)**: com o contrapeso mais de 45° acima da horizontal (AR além de ±135° do estacionamento), o tubo de 700 mm bate na base. Configure o limite em ±120° e o *meridian flip* normal.

## Balanceamento
O redutor e motor DEC (~0,45 kg) e a barra M12 já ficam do lado do contrapeso, por isso o contrapeso é pequeno:

| Carga no DEC | Contrapeso (anilha na ponta da barra … encostada na tampa) |
|---|---|
| 1,5 kg (só o tubo) | 0,28 … 0,46 kg |
| 2,0 kg | 0,47 … 0,79 kg |
| 2,5 kg (tubo + câmera) | 0,67 … 1,12 kg |
| 3,0 kg | 0,86 … 1,45 kg |

→ Uma anilha de **0,5 kg** para uso visual e uma de **1 kg** com câmera, numa barra de 200 mm. A BUCHA_CW adapta o furo de 25 mm da anilha para M12. Trave a anilha com 2 porcas M12 e ponha uma porca + arruela de segurança na ponta.

## Lista de compras
| Item | Qtd | Uso |
|---|---|---|
| Rolamento 6805-2RS (25×37×7) | 4 | eixos AR e DEC |
| Rolamento 6700ZZ (10×15×4) | 4 | 2 por redutor (TAMPA) |
| Tubo de alumínio Ø25 mm × parede 2 | 1 × 30 cm (melhor 35) | eixo AR 143,5 mm + eixo DEC 135,5 mm |
| Barra roscada M12 | 215 mm | contrapeso |
| Porca M12 | 4 | 1 presa na TAMPA_EXT, 2 travam a anilha, 1 na ponta |
| Anilha de academia, furo 25 mm | 0,5 kg (+1 kg p/ câmera) | contrapeso |
| Parafuso M8 × 45 + porca autotravante + 2 arruelas | 1 | pivô de latitude |
| Parafuso M6 × 45 + arruelas + porca/manípulo | 1 | trava de latitude |
| Barra roscada M6 × 40 + 2 porcas M6 | 1 | roda de latitude |
| Parafuso M6 × 25 (ou manípulo) + porca | 2 | aperto da sela |
| Parafuso M5 × 40 + porca | 2 | ajuste fino de azimute |
| Parafuso M5 × 25 + arruela + porca | 2 | trava de azimute |
| Parafuso M5 × 25 + porca | 2 | aperto do corpo DEC no eixo AR |
| Parafuso M4 × 16 + porca | 8 | flanges corpo ↔ EXT |
| Parafuso M4 × 16 + porca | 4 | cubo da sela ↔ placa da sela |
| Parafuso M4 × 20 + porca | 6 | aperto dos cubos (2 por CUBO + 2 no cubo da sela) |
| Parafuso M3 × 16 + porca | 4 | aperto do sextavado (CUBO) e do COLAR |
| Parafuso M3 × 10 (direto no plástico) | 2 | ajuste do braço anti-giro na EXT |
| Parafuso M3 × 8 (direto no plástico) | 6 | TAMPA_EXT na EXT |
| Parafuso M3 × 75 (ou barra roscada M3) | 8 | montagem dos redutores |
| Porca 1/4"-20 | 1 | presa na BASE (rosca do tripé) |

## Impressão (perfil Cura "Estrutura PETG 0.4")
- Peças estruturais (CORPO_AR, CORPO_DEC, CUNHA, CUBO, SELA_*): **5 paredes, 50% gyroid**. EXT, TAMPA_EXT e BASE: perfil padrão (4 paredes, 40%).
- Todas cabem na mesa de 220×220; a maior é a EXT, com 160 mm de altura.
- **Precisam de suporte**: CORPO_DEC (só embaixo do cubo de aperto lateral) e CUNHA (embaixo do bloco da roda, que sai para fora do prato). As outras imprimem sem suporte.
- Os alojamentos dos 6805 (Ø37,15) estão no diâmetro nominal. Imprima antes um anel de teste: o rolamento deve entrar com pressão leve de polegar. Se ficar apertado, aumente `ROL_D` no script.
- O furo dos cubos é 25,1 mm, com rasgo de aperto. Meça o tubo de alumínio: se ele não tiver 25,0 mm, mude `FURO_EIXO`.

## Montagem (ordem)
1. Prense os 6805 nos dois corpos e as porcas nos alojamentos sextavados (aqueça a porca com o ferro de solda se estiver justo).
2. **Eixo AR**: passe o tubo pelo CORPO_AR, encaixe o CUBO na ponta norte (lado do flange) e o CORPO_DEC na ponta sul. Aperte os dois encostados nas pistas internas, sem pré-carga excessiva: o eixo deve girar livre e sem folga axial.
3. **Eixo DEC**: o mesmo, com o CUBO do lado da EXT e o SELA_CUBO do lado do telescópio.
4. Monte o redutor com o COLAR na caixa, encaixe o sextavado no CUBO, deslize a EXT por cima (orelha no canal) e aparafuse a EXT no flange. Aperte o M3 lateral do braço.
5. Feche com a TAMPA_EXT (fios pelo furo de 12 mm). Rosqueie a barra M12 na TAMPA_EXT do lado DEC.
6. BASE no tripé → CUNHA → corpo AR no pivô M8 → trava M6 → roda.
7. **Polar no hemisfério sul**: não há estrela polar. Use *plate solving* (NINA/SharpCap/Ekos) ou o método de deriva. Comece apontando o eixo AR para o sul geográfico (não o magnético: no sul do Brasil a bússola erra cerca de 20°; confira a declinação magnética do seu local).

## Limitações conhecidas
- O cabo do motor DEC gira junto com o AR: deixe uma alça folgada (o limite de ±120° evita que ele enrole).
- A rigidez é de peça impressa: espere alguma vibração com vento. Para astrofoto, use exposições curtas e guiagem.
- O adaptador da cauda de andorinha para os 2 parafusos do Greika será feito à parte (falta a distância entre os parafusos).
- A massa das peças impressas foi estimada com 60% de preenchimento efetivo; pese as peças reais e ajuste o contrapeso na prática.
