import numpy as np
import colorsys


def wavelength_to_rgb(wavelength_nm):
    gamma = 0.8
    intensity_max = 255

    if wavelength_nm < 380 or wavelength_nm > 750:
        return (0, 0, 0)  # fora da faixa visível, retorna preto

    if 380 <= wavelength_nm < 440:
        R = -(wavelength_nm - 440) / (440 - 380)
        G = 0.0
        B = 1.0
    elif 440 <= wavelength_nm < 490:
        R = 0.0
        G = (wavelength_nm - 440) / (490 - 440)
        B = 1.0
    elif 490 <= wavelength_nm < 510:
        R = 0.0
        G = 1.0
        B = -(wavelength_nm - 510) / (510 - 490)
    elif 510 <= wavelength_nm < 580:
        R = (wavelength_nm - 510) / (580 - 510)
        G = 1.0
        B = 0.0
    elif 580 <= wavelength_nm < 645:
        R = 1.0
        G = -(wavelength_nm - 645) / (645 - 580)
        B = 0.0
    elif 645 <= wavelength_nm <= 750:
        R = 1.0
        G = 0.0
        B = 0.0

    # Atenuação
    if 380 <= wavelength_nm < 420:
        factor = 0.3 + 0.7 * (wavelength_nm - 380) / (420 - 380)
    elif 645 <= wavelength_nm <= 750:
        factor = 0.3 + 0.7 * (750 - wavelength_nm) / (750 - 645)
    else:
        factor = 1.0

    R = round(intensity_max * (R * factor) ** gamma)
    G = round(intensity_max * (G * factor) ** gamma)
    B = round(intensity_max * (B * factor) ** gamma)

    return (R, G, B)


def frequency_to_color_physical(frequencies: list = [110, 440, 1760, 8800]) -> tuple:
    """
    Mapeia uma frequência sonora para uma cor RGB baseada em um modelo físico com mapeamento logarítmico por oitavas.
    """
    c = 3e8  # velocidade da luz (m/s)
    f_ref_som: float = 20.0  # Hz
    lambda_ref_nm: float = 700.0  # nm (vermelho)

    f_ref_luz = c / (lambda_ref_nm * 1e-9)  # Hz

    colors = ()
    for f in frequencies:
        if f <= 0 or np.isnan(f):
            continue  # ignora valores inválidos

        try:
            n = np.log2(f / f_ref_som)
            f_luz = f_ref_luz * (2 ** n)
            lambda_luz_m = c / f_luz
            lambda_luz_nm = lambda_luz_m * 1e9

            # Trazer para faixa visível (modo cíclico)
            if lambda_luz_nm < 380 or lambda_luz_nm > 750:
                lambda_luz_nm = 400 + (lambda_luz_nm % 300)

            colors += (wavelength_to_rgb(lambda_luz_nm),)
        except Exception:
            continue  # previne erros numéricos imprevistos

    return colors
