def calc_area(shape: str, **kwargs):
    if shape == "retangulo":
        return kwargs["base"] * kwargs["altura"]
    elif shape == "quadrado":
        return kwargs["lado"] * kwargs["lado"]
    elif shape == "triangulo":
        return kwargs["base"] * kwargs["altura"] / 2
    else:
        raise ValueError("Forma desconhecida")
