"""
Script para debugar os tipos de dados retornados pelas funções
Execute este script para ver exatamente o que suas funções estão retornando
"""

import numpy as np
from utils.winding_utils import generate_winding
from mapping.color_mapping import frequency_to_rgb


def debug_data_types():
    """Função para testar e mostrar os tipos de dados"""

    print(" DEBUGANDO TIPOS DE DADOS")
    print("=" * 50)

    test_frequencies = [440.0, 880.0, 220.0, 1000.0]

    for freq in test_frequencies:
        print(f"\n Testando frequência: {freq}Hz")
        print("-" * 30)

        try:
            winding = generate_winding(freq)
            print(f"Winding resultado:")
            print(f"  Tipo: {type(winding)}")
            print(f"  Valor: {winding}")

            if hasattr(winding, 'shape'):
                print(f"  Shape: {winding.shape}")
            if hasattr(winding, 'dtype'):
                print(f"  Dtype: {winding.dtype}")
            if hasattr(winding, '__len__'):
                print(f"  Length: {len(winding)}")

            if isinstance(winding, (tuple, list)):
                for i, item in enumerate(winding):
                    print(f"  Item {i}: {type(item)} = {item}")

            if hasattr(winding, 'x'):
                print(f"  winding.x: {type(winding.x)} = {winding.x}")
            if hasattr(winding, 'y'):
                print(f"  winding.y: {type(winding.y)} = {winding.y}")

        except Exception as e:
            print(f"Erro em generate_winding: {e}")

        try:
            color = frequency_to_rgb(freq)
            print(f"\nCor resultado:")
            print(f"  Tipo: {type(color)}")
            print(f"  Valor: {color}")

            if hasattr(color, 'shape'):
                print(f"  Shape: {color.shape}")
            if hasattr(color, 'dtype'):
                print(f"  Dtype: {color.dtype}")
            if hasattr(color, '__len__'):
                print(f"  Length: {len(color)}")

            if isinstance(color, (tuple, list)):
                for i, item in enumerate(color):
                    print(f"  Item {i}: {type(item)} = {item}")

            if hasattr(color, 'r'):
                print(f"  color.r: {type(color.r)} = {color.r}")
            if hasattr(color, 'g'):
                print(f"  color.g: {type(color.g)} = {color.g}")
            if hasattr(color, 'b'):
                print(f"  color.b: {type(color.b)} = {color.b}")

        except Exception as e:
            print(f" Erro em frequency_to_rgb: {e}")

    print("\n" + "=" * 50)
    print("🔍 Debug concluído!")


if __name__ == "__main__":
    debug_data_types()
