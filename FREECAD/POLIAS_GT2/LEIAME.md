# Polias GT2 20T / 40T + correia fechada 120 × 6 mm (60 dentes)

Modelo do conjunto de polias GT2 (passo 2 mm, redução **2:1**) usado na saída do redutor V2 (`../REDUCAO_V2/`). Por padrão, não há tensor: o entre centros é fixo.

## Arquivos
- `POLIAS_GT2.FCStd`: as 2 polias, 4 parafusos de fixação e a correia, com os dentes já encaixados nos vãos.
- `STEP/`: cada polia no próprio sistema de coordenadas (furo no eixo Z, flange de baixo em z = 0), a correia e o conjunto completo.
- `scripts/build_polias.py`: gera tudo. O `../REDUCAO_V2/scripts/saida_polias.py` também chama esse script, com C = 29,35.

## Como rodar (PowerShell)
```powershell
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" "C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\POLIAS_GT2\scripts\build_polias.py"
```
Para mudar um parâmetro, defina a variável antes, na mesma linha (ela vale até fechar o terminal):
```powershell
$env:L_CORREIA = "122"; & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" "C:\LUIZ\PROJECTS\GOTO_TELESCOPE\FREECAD\POLIAS_GT2\scripts\build_polias.py"
```
| Variável | Padrão | O que é |
|---|---|---|
| `Z1`, `Z2` | 20, 40 | dentes |
| `FURO1`, `FURO2` | 8, 8 | furos (mm) |
| `L_CORREIA` | 120 | comprimento primitivo (múltiplo de 2) |
| `LARG` | 6 | largura da correia |
| `C_FIXO` | `0` (calcular) | entre centros fixo em mm; `0` = calculado pela correia |
| `IDLER_X` | `0` (sem tensor) | posição x do tensor 2× F623 no ramo de cima; exige `C_FIXO` abaixo do nominal |
| `ROT1`, `ROT2` | 180, 0 | giro extra das polias (múltiplo do passo angular) para posicionar os parafusos |

No PowerShell, `$env:X = ""` apaga a variável em vez de deixá-la vazia. Para "nenhum", use `"0"`. Para voltar ao padrão: `Remove-Item Env:NOME` ou feche o terminal.

## Resultado com os valores padrão
- **Diâmetro primitivo**: 12,73 mm na 20T e 25,46 mm na 40T. O diâmetro externo dos dentes é 12,22 / 24,96 mm.
- **Entre centros nominal** para 120 mm: **29,306 mm**. Na montagem do redutor usei 29,35: a correia estica 0,086 mm, uma leve pré-tensão.
- **Abraçamento na 20T**: 154,9°, cerca de 8,6 dentes engrenados.

| Correia (sem tensor) | Entre centros nominal |
|---|---|
| 120 mm (60 dentes) | 29,31 mm |
| 122 mm (61 dentes) | 30,33 mm |
| 124 mm (62 dentes) | 31,35 mm |
| 126 mm (63 dentes) | 32,37 mm |

## Dimensões das polias (típicas do kit; meça as suas)
| | 20T | 40T |
|---|---|---|
| Flange | Ø16 × 1 (só embaixo) | Ø30 × 1 (dos dois lados) |
| Largura dentada | 7 mm | 7 mm |
| Cubo | Ø16 × 8 | Ø20 × 8 |
| Altura total | 16 mm | 17 mm |
| Parafusos de fixação | 2× M3 a 90° | 2× M4 a 90° |

## Limitações
- Não modelei chanfros nem a rosca dos furos dos parafusos.
- A correia é desenhada no comprimento do percurso. Com C acima do nominal, ela aparece esticada, e os dentes encostam de leve na 20T (cerca de 0,7 mm³ de sobreposição no modelo).
- `STEP/POLIA_GT2_20T_furo5.step` é de uma versão anterior, com furo de 5 mm.
