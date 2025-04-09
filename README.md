# Tradutor Sensorial de Música

Este projeto de pesquisa busca construir um sistema capaz de converter música em representações sensoriais multicanal com base em princípios físico-matemáticos e técnicas modernas de ciência de dados e redes neurais.

## Estrutura do Projeto

- **notebooks/**: notebooks exploratórios com visualizações e protótipos
- **src/**: código modular e reutilizável da aplicação
- **data/**: diretório para armazenar dados estruturados
- **outputs/**: resultados gerados por simulações, inferência etc.
- **reports/**: textos científicos e proposta em LaTeX

## Como rodar

```bash
conda env create -f environment.yml
conda activate tradutor-sensorial
python -m ipykernel install --user --name=sensory-translation --display-name "Python (sensory-translation)"
jupyter lab

