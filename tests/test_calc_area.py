from app.models.fase1.area_model import calc_area

def test_area_retangulo():
    assert calc_area("retangulo", base=4, altura=2) == 8

def test_area_quadrado():
    assert calc_area("quadrado", lado=3) == 9
